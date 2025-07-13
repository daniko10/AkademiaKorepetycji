from flask import render_template, redirect, url_for, session, flash, send_from_directory, request
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, bcrypt, login_manager
from app.forms import LoginForm, RegisterForm, AssignTaskForm, TaskSubmissionForm, GradeTaskForm
from app.models import Student, Teacher, Task, Administrator
from werkzeug.utils import secure_filename
from datetime import datetime
from app.utils import compress_file
import os
import json

@login_manager.user_loader
def load_user(user_id):
    role = session.get('role')

    if role == 'teacher':
        return Teacher.query.get(int(user_id))
    elif role == 'student':
        return Student.query.get(int(user_id))
    elif role == 'administrator':
        return Administrator.query.get(int(user_id))
    return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
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
                return redirect(url_for('login'))
            login_user(user)
            session['role'] = role
            return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = Student.query.filter_by(email=form.email.data).first()
        if not existing_user:
            existing_user = Teacher.query.filter_by(email=form.email.data).first()
        if not existing_user:
            existing_user = Administrator.query.filter_by(email=form.email.data).first()

        if existing_user:
            flash("Użytkownik z tym adresem e-mail już istnieje.", "danger")
            return render_template('register.html', form=form)
        
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
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    if isinstance(current_user, Teacher):
        students = current_user.students  # Twoi uczniowie

        # Dla każdego zadania każdego ucznia: dekoduj listy załączników
        for student in students:
            # bierzemy tylko zadania tego nauczyciela
            student_tasks = [t for t in student.tasks if t.teacher_id == current_user.id]
            for t in student_tasks:
                # dekoduj załączniki od nauczyciela
                t.attachment_list  = json.loads(t.teacher_attachments  or '[]')
                # dekoduj załączniki od ucznia
                t.submission_list  = json.loads(t.student_attachments or '[]')

        return render_template('teacher_dashboard.html',
                               teacher=current_user,
                               students=students)

    elif isinstance(current_user, Student):
        tasks = Task.query.filter_by(student_id=current_user.id).all()
        for t in tasks:
            t.attachment_list = json.loads(t.teacher_attachments  or '[]')
            t.submission_list = json.loads(t.student_attachments or '[]')
        return render_template('student_dashboard.html',
                               student=current_user,
                               tasks=tasks)

    elif isinstance(current_user, Administrator):
        return redirect(url_for('admin_dashboard'))

    return "Nieznany typ użytkownika", 400

@app.route('/assign-task/<int:student_id>', methods=['GET', 'POST'])
@login_required
def assign_task(student_id):
    if not isinstance(current_user, Teacher):
        return "Brak dostępu", 403

    student = Student.query.get_or_404(student_id)
    form = AssignTaskForm()

    if form.validate_on_submit():
        filenames = []
        for file_storage in form.attachments.data:
            if file_storage:
                filename = secure_filename(file_storage.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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
            issued_at=datetime.utcnow(),
            teacher_attachments=json.dumps(filenames)
        )
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('assign_task.html', form=form, student=student)

@app.route('/submit-task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def submit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not isinstance(current_user, Student) or task.student_id != current_user.id:
        return "Brak dostępu", 403
    form = TaskSubmissionForm()

    if form.validate_on_submit():
        filenames = []
        for file_storage in form.attachments.data:
            if file_storage:
                fname = secure_filename(file_storage.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
                file_storage.save(filepath)
                compress_file(filepath)
                filenames.append(fname)
        
        task.student_answer = form.answer.data
        task.student_attachments = json.dumps(filenames)
        task.earned_points = None
        task.submitted = True
        db.session.commit()

        return redirect(url_for('dashboard'))
    return render_template('submit_task.html', form=form, task=task)

@app.route('/grade-task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def grade_task(task_id):
    task = Task.query.get_or_404(task_id)

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
            flash("Ocena zapisana!", "success")
            return redirect(url_for('dashboard'))

    return render_template('grade_task.html', form=form, task=task)

@app.route('/uploads/<filename>')
@login_required
def download_file(filename):
    uploads_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'uploads')
    return send_from_directory(uploads_dir, filename, as_attachment=True)

@app.route('/admin/dashboard', methods=['GET','POST'])
@login_required
def admin_dashboard():
    if not isinstance(current_user, Administrator):
        return "Brak dostępu", 403

    pending_students   = Student.query.filter_by(approved=False).all()
    pending_teachers   = Teacher.query.filter_by(approved=False).all()
    unassigned_students = Student.query.filter_by(approved=True, teacher_id=None).all()
    assigned_students = Student.query.filter_by(approved=True).all()
    approved_teachers  = Teacher.query.filter_by(approved=True).all()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'approve_student':
            sid = int(request.form['student_id'])
            student = Student.query.get_or_404(sid)
            student.approved = True
            db.session.commit()
            flash(f"Studenta {student.name} zatwierdzono.", "success")

        elif action == 'approve_teacher':
            tid = int(request.form['teacher_id'])
            teacher = Teacher.query.get_or_404(tid)
            teacher.approved = True
            db.session.commit()
            flash(f"Nauczyciela {teacher.name} zatwierdzono.", "success")

        elif action == 'assign_student':
            sid = int(request.form['student_id'])
            tid = int(request.form['teacher_id'])
            student = Student.query.get_or_404(sid)
            teacher = Teacher.query.get_or_404(tid)
            student.teacher_id = tid
            db.session.commit()
            flash(f"Studenta {student.name} przypisano do nauczyciela {teacher.name}.", "success")

        elif action == 'delete_student':
            sid = int(request.form['student_id'])
            student = Student.query.get_or_404(sid)
            db.session.delete(student)
            db.session.commit()
            flash(f"Studenta {student.name} usunięto z systemu.", "warning")

        elif action == 'delete_teacher':
            tid = int(request.form['teacher_id'])
            teacher = Teacher.query.get_or_404(tid)
            for s in teacher.students:
                s.teacher_id = None
            db.session.delete(teacher)
            db.session.commit()
            flash(f"Nauczyciela {teacher.name} usunięto z systemu.", "warning")

        elif action == 'unassign_student':
            sid = int(request.form['student_id'])
            student = Student.query.get_or_404(sid)
            student.teacher_id = None
            db.session.commit()
            flash(f"Ucznia {student.name} odłączono od nauczyciela.", "warning")
        
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_dashboard.html',
                           pending_students=pending_students,
                           pending_teachers=pending_teachers,
                           unassigned_students=unassigned_students,
                           assigned_students=assigned_students,
                           approved_teachers=approved_teachers)

@app.route('/admin/approve/<string:user_type>/<int:user_id>')
@login_required
def approve_user(user_type, user_id):
    if not isinstance(current_user, Administrator):
        return "Brak dostępu", 403

    model = Student if user_type == "student" else Teacher
    user = model.query.get_or_404(user_id)
    user.approved = True
    db.session.commit()
    flash("Użytkownik zatwierdzony!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
