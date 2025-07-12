from flask import render_template, redirect, url_for, session, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, bcrypt, login_manager
from app.forms import LoginForm, RegisterForm, AssignTaskForm, TaskSubmissionForm, GradeTaskForm
from app.models import Student, Teacher, Task, Administrator
import os
from werkzeug.utils import secure_filename
from datetime import datetime

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
    print(f"Current user: {current_user}, Role: {session.get('role')}")
    if isinstance(current_user, Teacher):
        students = Student.query.all()
        return render_template('teacher_dashboard.html', teacher=current_user, students=students)

    elif isinstance(current_user, Student):
        tasks = Task.query.filter_by(student_id=current_user.id).all()
        return render_template('student_dashboard.html', student=current_user, tasks=tasks)

    elif isinstance(current_user, Administrator):
        return pending_users()

    return "Nieznany typ użytkownika", 400

@app.route('/assign-task/<int:student_id>', methods=['GET', 'POST'])
@login_required
def assign_task(student_id):
    if not isinstance(current_user, Teacher):
        return "Brak dostępu", 403

    student = Student.query.get_or_404(student_id)
    form = AssignTaskForm()

    if form.validate_on_submit():
        filename = None

        if form.attachment.data:
            filename = secure_filename(form.attachment.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.attachment.data.save(filepath)
            teacher_attachment_path = filename
        else:
            teacher_attachment_path = None

        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            max_points=form.max_points.data,
            student_id=student.id,
            teacher_id=current_user.id,
            issued_at=datetime.utcnow(),
            teacher_attachment=teacher_attachment_path
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
        filename = None
        if form.attachment.data:
            filename = secure_filename(form.attachment.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.attachment.data.save(filepath)
            student_attachment_path = filename
        else:
            student_attachment_path = None
        
        task.student_answer = form.answer.data
        task.student_attachment = student_attachment_path
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

@app.route('/admin/pending')
@login_required
def pending_users():
    if not isinstance(current_user, Administrator):
        return "Brak dostępu", 403

    students = Student.query.filter_by(approved=False).all()
    teachers = Teacher.query.filter_by(approved=False).all()
    return render_template('admin_dashboard.html', students=students, teachers=teachers)

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
    return redirect(url_for('pending_users'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
