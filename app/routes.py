from flask import render_template, redirect, url_for, session, flash, send_from_directory, request, jsonify, Blueprint, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message as MailMessage
from app import db, bcrypt, login_manager, mail
from app.forms import LoginForm, RegisterForm, AssignTaskForm, TaskSubmissionForm, GradeTaskForm, WriteMessageForm
from app.models import Student, Teacher, Task, Administrator, Message, LessonSeries
from sqlalchemy import and_, not_
from werkzeug.utils import secure_filename
from datetime import datetime
from app.utils import compress_file
from datetime import date, timezone, timedelta
from app.utils import get_or_404
import os
import json

# Tworzymy blueprint
bp = Blueprint('main', __name__)


@login_manager.user_loader
def load_user(user_id):
    role = session.get('role')
    match role:
        case 'student':
            return Student.query.get(int(user_id))
        case 'teacher':
            return Teacher.query.get(int(user_id))
        case 'administrator':
            return Administrator.query.get(int(user_id))
    return None

@bp.route('/')
def home():
    return render_template('home.html')

@bp.route("/check_email/<email>", methods=["GET"])
def check_email(email):
    exists = bool(
        Student.query.filter_by(email=email).first() or
        Teacher.query.filter_by(email=email).first() or
        Administrator.query.filter_by(email=email).first()
    )
    return jsonify({"exists": exists})

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Student.query.filter_by(email=form.email.data).first()
        role = 'student'

        if not user:
            user = Teacher.query.filter_by(email=form.email.data).first()
            role = 'teacher'

        if not user:
            user = Administrator.query.filter_by(email=form.email.data).first()
            role = 'administrator'

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if hasattr(user, 'approved') and not user.approved:
                flash('Twoje konto oczekuje na zatwierdzenie przez administratora.', 'warning')
                return redirect(url_for('main.login'))
            login_user(user)
            session['role'] = role
            return redirect(url_for('main.dashboard'))
    return render_template('login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        if form.role.data == 'student':
            user = Student(
                name=form.name.data,
                surname=form.surname.data,
                email=form.email.data,
                password=hashed_pw
            )
        else:
            user = Teacher(
                name=form.name.data,
                surname=form.surname.data,
                email=form.email.data,
                password=hashed_pw,
                subject=form.subject.data
            )

        db.session.add(user)
        db.session.commit()
        flash("Rejestracja zakończona pomyślnie! Proszę czekać na potwierdzenie.", "success")
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)

@bp.route('/dashboard')
@login_required
def dashboard():
    if isinstance(current_user, Teacher):
        students = current_user.students

        for student in students:
            student_tasks = [t for t in student.tasks if t.teacher_id == current_user.id]
            for t in student_tasks:
                t.attachment_list  = json.loads(t.teacher_attachments  or '[]')
                t.submission_list  = json.loads(t.student_attachments or '[]')

        return render_template('teacher_dashboard.html',
                               teacher=current_user,
                               students=students)

    elif isinstance(current_user, Student):
        tasks = Task.query.filter_by(student_id=current_user.id).all()
        teachers = current_user.teachers
        for t in tasks:
            t.attachment_list = json.loads(t.teacher_attachments  or '[]')
            t.submission_list = json.loads(t.student_attachments or '[]')
        return render_template('student_dashboard.html',
                               student=current_user,
                               tasks=tasks,
                               teachers=teachers)

    elif isinstance(current_user, Administrator):
        return redirect(url_for('main.admin_dashboard'))

    return "Nieznany typ użytkownika", 400

@bp.route('/assign-task/<int:student_id>', methods=['GET', 'POST'])
@login_required
def assign_task(student_id):
    if not isinstance(current_user, Teacher):
        return "Brak dostępu", 403

    student = get_or_404(Student,student_id)
    form = AssignTaskForm()

    if form.validate_on_submit():
        filenames = []
        for file_storage in form.attachments.data:
            if file_storage:
                filename = secure_filename(file_storage.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file_storage.save(filepath)
                compress_file(filepath)
                filenames.append(filename)
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            max_points=form.max_points.data,
            student_id=student.id,
            teacher_id=current_user.id,
            issued_at=datetime.now(timezone.utc),
            teacher_attachments=json.dumps(filenames)
        )
        db.session.add(task)
        db.session.commit()
        
        return redirect(url_for('main.send_email', email=student.email, purpose='assign_task'))
    
    today_iso = date.today().isoformat()
    return render_template('assign_task.html', form=form, student=student, min_date=today_iso)

@bp.route('/submit-task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def submit_task(task_id):
    task = get_or_404(Task,task_id)
    if not isinstance(current_user, Student) or task.student_id != current_user.id:
        return "Brak dostępu", 403
    form = TaskSubmissionForm()

    if form.validate_on_submit():
        filenames = []
        for file_storage in form.attachments.data:
            if file_storage:
                fname = secure_filename(file_storage.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], fname)
                file_storage.save(filepath)
                compress_file(filepath)
                filenames.append(fname)
        
        task.student_answer = form.answer.data
        task.student_attachments = json.dumps(filenames)
        task.earned_points = None
        task.submitted = True
        db.session.commit()

        return redirect(url_for('main.send_email', email=task.teacher.email, purpose='submit_task'))
        
    return render_template('submit_task.html', form=form, task=task)

@bp.route('/grade-task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def grade_task(task_id):
    task = get_or_404(Task,task_id)

    if not isinstance(current_user, Teacher) or task.teacher_id != current_user.id:
        return "Brak dostępu", 403

    if not task.submitted:
        return "Zadanie nie zostało jeszcze oddane przez ucznia.", 400

    form = GradeTaskForm()

    if form.validate_on_submit():
        if form.earned_points.data > task.max_points:
            flash(f"Nie możesz przyznać więcej niż {task.max_points} punktów.", "warning")
        else:
            task.earned_points = form.earned_points.data
            db.session.commit()
            
            return redirect(url_for('main.send_email', email=task.student.email, purpose='grade_task'))

    return render_template('grade_task.html', form=form, task=task)

@bp.route('/send-email/<string:email>/<string:purpose>', methods=['GET', 'POST'])
def send_email(email, purpose):    
    match purpose:
        case 'assign_task':
            subject = "Nowe zadanie do wykonania"
            body = "Zostało Ci przydzielone nowe zadanie. Proszę sprawdzić swoje zadania na stronie."
        case 'submit_task':
            subject = "Zadanie zostało oddane"
            body = "Zadanie zostało oddane. Proszę ocenić zadanie."
        case 'grade_task':
            subject = "Zadanie zostało ocenione"
            body = "Twoje zadanie zostało ocenione. Proszę sprawdzić swoje zadania na stronie."
    
    msg = MailMessage(subject, sender = os.getenv('EMAIL'), recipients = [email])
    msg.body = body
    
    try:
        mail.send(msg)
    except Exception as e:
        flash(f"Wystąpił błąd podczas wysyłania emaila: {str(e)}", "danger")
    
    return redirect(url_for('main.dashboard'))

@bp.route('/uploads/<filename>')
@login_required
def download_file(filename):
    uploads_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'uploads')
    return send_from_directory(uploads_dir, filename, as_attachment=True)

@bp.route('/admin/dashboard', methods=['GET','POST'])
@login_required
def admin_dashboard():
    if not isinstance(current_user, Administrator):
        return "Brak dostępu", 403

    pending_students   = Student.query.filter_by(approved=False).all()
    pending_teachers   = Teacher.query.filter_by(approved=False).all()
    unassigned_students = Student.query \
    .filter(and_(Student.approved == True,
                 not_(Student.teachers.any()))) \
    .all()
    assigned_students = Student.query \
    .filter(and_(Student.approved == True,
                 Student.teachers.any())) \
    .all()
    approved_teachers  = Teacher.query.filter_by(approved=True).all()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'approve_student':
            sid = int(request.form['student_id'])
            student = get_or_404(Student, sid)
            student.approved = True
            db.session.commit()
            flash(f"Studenta {student.name} zatwierdzono.", "success")

        elif action == 'approve_teacher':
            tid = int(request.form['teacher_id'])
            teacher = get_or_404(Teacher, tid)
            teacher.approved = True
            db.session.commit()
            flash(f"Nauczyciela {teacher.name} zatwierdzono.", "success")

        elif action == 'assign_student':
            sid = int(request.form['student_id'])
            tid_list = request.form.getlist('teacher_ids', type=int)
            s = get_or_404(Student, sid)
            s.teachers = Teacher.query.filter(Teacher.id.in_(tid_list)).all()
            db.session.commit()
            flash(f"Studenta {s.name} przypisano do wybranych nauczycieli.", "success")

        elif action == 'delete_student':
            sid = int(request.form['student_id'])
            student = get_or_404(Student, sid)
            db.session.delete(student)
            db.session.commit()
            flash(f"Studenta {student.name} usunięto z systemu.", "warning")

        elif action == 'delete_teacher':
            tid = int(request.form['teacher_id'])
            teacher = get_or_404(Teacher, tid)
            for s in teacher.students:
                s.teacher_id = None
            db.session.delete(teacher)
            db.session.commit()
            flash(f"Nauczyciela {teacher.name} usunięto z systemu.", "warning")

        elif action == 'unassign_student':
            sid = int(request.form['student_id'])
            tid = int(request.form['teacher_id'])
            student = get_or_404(Student, sid)
            teacher = get_or_404(Teacher, tid)

            if teacher in student.teachers:
                student.teachers.remove(teacher)
                db.session.commit()
                flash(f"Ucznia {student.name} odłączono od nauczyciela {teacher.name}.", "warning")
            else:
                flash("Ten uczeń nie był przypisany do tego nauczyciela.", "info")

        elif action == 'update_teachers':
            sid = int(request.form['student_id'])
            tid_list = request.form.getlist('teacher_ids', type=int)
            student = get_or_404(Student, sid)
            student.teachers = Teacher.query.filter(Teacher.id.in_(tid_list)).all()
            db.session.commit()
            flash(f"Przypisania nauczycieli zaktualizowano dla {student.name}.", "success")

        return redirect(url_for('main.admin_dashboard'))

    return render_template('admin_dashboard.html',
                           pending_students=pending_students,
                           pending_teachers=pending_teachers,
                           unassigned_students=unassigned_students,
                           assigned_students=assigned_students,
                           approved_teachers=approved_teachers)

@bp.route('/admin/approve/<string:user_type>/<int:user_id>')
@login_required
def approve_user(user_type, user_id):
    if not isinstance(current_user, Administrator):
        return "Brak dostępu", 403

    model = Student if user_type == "student" else Teacher
    user = model.query.get_or_404(user_id)
    user.approved = True
    db.session.commit()
    flash("Użytkownik zatwierdzony!", "success")
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/chat/<int:student_id>/<int:teacher_id>/<string:role>', methods=['GET', 'POST'])
@login_required
def chat(student_id, teacher_id, role):
    print('Chat route accessed')
    sender_role = 'teacher'
    receiver_role = 'student'
    if role == 'student':
        sender_role = 'student'
        receiver_role = 'teacher'
    messages = Message.query.filter(
        db.or_(
            db.and_(
                Message.sender_id == student_id,
                Message.sender_role == 'student',
                Message.receiver_id == teacher_id,
                Message.receiver_role == 'teacher'
            ),
            db.and_(
                Message.sender_id == teacher_id,
                Message.sender_role == 'teacher',
                Message.receiver_id == student_id,
                Message.receiver_role == 'student'
            )
        )
    ).order_by(Message.timestamp.asc()).all()
    form = WriteMessageForm()
    if form.validate_on_submit():
        message = Message(
            sender_id=student_id if role == 'student' else teacher_id,
            receiver_id=teacher_id if role == 'student' else student_id,
            sender_role=sender_role,
            receiver_role=receiver_role,
            content=form.message.data
        )
        db.session.add(message)
        db.session.commit()
        return redirect(url_for('main.chat', student_id=student_id, teacher_id=teacher_id, role=role))
    return render_template('chat.html', form=form, messages=messages)

@bp.get("/teacher/<int:teacher_id>/lessons")
def teacher_lessons(teacher_id):
    start = datetime.fromisoformat(request.args["start"]).date()
    end = datetime.fromisoformat(request.args["end"]).date()

    series_list = LessonSeries.query.filter_by(teacher_id=teacher_id).all()
    events = []

    for s in series_list:
        d = max(start, s.start_date)
        while d <= min(end, s.end_date):
            if d.weekday() == s.day_of_week:
                start_dt = datetime.combine(d, s.start_time)
                end_dt = datetime.combine(d, s.end_time)
                events.append({
                    "id": f"series-{s.id}-{d}",
                    "title": f"{s.student.name} {s.student.surname}",
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat()
                })
            d += timedelta(days=1)

    return jsonify(events)

@bp.get("/student/<int:student_id>/lessons")
def student_lessons(student_id):
    start = datetime.fromisoformat(request.args["start"]).date()
    end = datetime.fromisoformat(request.args["end"]).date()

    series_list = LessonSeries.query.filter_by(student_id=student_id).all()
    events = []

    for s in series_list:
        d = max(start, s.start_date)
        while d <= min(end, s.end_date):
            if d.weekday() == s.day_of_week:
                start_dt = datetime.combine(d, s.start_time)
                end_dt = datetime.combine(d, s.end_time)
                teacher = get_or_404(Teacher,s.teacher_id)
                events.append({
                    "id": f"series-{s.id}-{d}",
                    "title": f" {teacher.subject}",
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat()
                })
            d += timedelta(days=1)

    return jsonify(events)

@bp.route('/lesson/assign/<int:student_id>/<int:teacher_id>', methods=['GET', 'POST'])
def assign_lesson(student_id, teacher_id):
    student = get_or_404(Student,student_id)
    teacher = get_or_404(Teacher,teacher_id)

    if request.method == 'POST':
        day_of_week = int(request.form['day_of_week'])
        start_time = datetime.strptime(request.form['start_time'], "%H:%M").time()
        end_time = datetime.strptime(request.form['end_time'], "%H:%M").time()
        start_date = datetime.strptime(request.form['start_date'], "%Y-%m-%d").date()
        end_date = datetime.strptime(request.form['end_date'], "%Y-%m-%d").date()

        conflicts = LessonSeries.query.filter(
            LessonSeries.teacher_id == teacher.id,
            LessonSeries.day_of_week == day_of_week,
            LessonSeries.start_date <= end_date,   
            LessonSeries.end_date >= start_date,   
            LessonSeries.start_time < end_time,     
            LessonSeries.end_time > start_time      
        ).all()

        if conflicts:
            flash("⚠️ Konflikt! Nauczyciel ma już zajęcia w tym czasie.", "danger")
            return render_template('assign_lesson.html', student=student, teacher=teacher)

        series = LessonSeries(
            teacher_id=teacher.id,
            student_id=student.id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(series)
        db.session.commit()
        flash("Seria zajęć została dodana!", "success")
        return redirect(url_for('main.dashboard'))

    return render_template('assign_lesson.html', student=student, teacher=teacher)

@bp.route('/lesson/delete/<lesson_id>', methods=['DELETE'])
def delete_lesson(lesson_id):
    try:
        real_id = int(lesson_id.split("-")[1])
    except Exception:
        return '', 400
    
    lesson = db.session.get(LessonSeries, real_id)
    if not lesson:
        return '', 404

    db.session.delete(lesson)
    db.session.commit()
    return '', 204

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))


# route jeżeli tryb ciemny miałby być skojarzony z konkretnym kontem

# @bp.route('/set-theme', methods=['POST'])
# @login_required
# def set_theme():
#     data = request.json
#     theme = data.get('theme')
#     if theme in ['light', 'dark']:
#         current_user.theme = theme
#         db.session.commit()
#         return jsonify({'status': 'success'})
#     return jsonify({'status': 'error'}), 400
