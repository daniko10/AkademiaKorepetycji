
from app import db
from datetime import datetime
from app.models import Student, Teacher, LessonSeries
from flask_login import login_user

def login_student(client, student):
    with client.application.test_request_context():
        login_user(student)

def login_teacher(client, teacher):
    with client.application.test_request_context():
        login_user(teacher)

def test_assign_lesson_page_loads(client):
    teacher = Teacher.query.filter_by(email='teacher@example.com').first()
    student = Student.query.filter_by(email='student@example.com').first()
    login_teacher(client, teacher)

    response = client.get(f'/lesson/assign/{student.id}/{teacher.id}')
    assert response.status_code == 200
    html = response.data.decode()

    # Sprawdzamy nagłówek
    assert f"Nowa seria zajęć dla {student.name} {student.surname}" in html

    # Sprawdzamy pola formularza
    assert 'name="day_of_week"' in html
    assert 'name="start_time"' in html
    assert 'name="end_time"' in html
    assert 'name="start_date"' in html
    assert 'name="end_date"' in html
    assert 'type="submit"' in html

def test_assign_lesson_create_series(client):
    teacher = Teacher.query.filter_by(email='teacher@example.com').first()
    student = Student.query.filter_by(email='student@example.com').first()
    login_teacher(client, teacher)

    form_data = {
        'day_of_week': '0',  # poniedziałek
        'start_time': '10:00',
        'end_time': '11:00',
        'start_date': '2025-09-01',
        'end_date': '2025-09-30'
    }

    response = client.post(f'/lesson/assign/{student.id}/{teacher.id}', data=form_data, follow_redirects=True)
    html = response.data.decode()

    # Sprawdzenie przekierowania na dashboard
    assert response.status_code == 200
    assert 'Seria zajęć została dodana!' in html

    # Sprawdzenie, że seria faktycznie istnieje w bazie
    series = LessonSeries.query.filter_by(student_id=student.id, teacher_id=teacher.id).first()
    assert series is not None
    assert series.start_time.strftime('%H:%M') == '10:00'
    assert series.end_time.strftime('%H:%M') == '11:00'

def test_assign_lesson_conflict(client):
    teacher = Teacher.query.filter_by(email='teacher@example.com').first()
    student = Student.query.filter_by(email='student@example.com').first()
    login_teacher(client, teacher)

    # Dodajemy istniejącą serię zajęć
    existing = LessonSeries(
        teacher_id=teacher.id,
        student_id=student.id,
        day_of_week=0,
        start_time=datetime.strptime("10:00", "%H:%M").time(),
        end_time=datetime.strptime("11:00", "%H:%M").time(),
        start_date=datetime(2025, 9, 1).date(),
        end_date=datetime(2025, 9, 30).date()
    )
    db.session.add(existing)
    db.session.commit()

    # Próba dodania kolidującej serii
    form_data = {
        'day_of_week': '0',
        'start_time': '10:30',  # koliduje
        'end_time': '11:30',
        'start_date': '2025-09-01',
        'end_date': '2025-09-30'
    }

    response = client.post(f'/lesson/assign/{student.id}/{teacher.id}', data=form_data)
    html = response.data.decode()

    # Sprawdzenie komunikatu o konflikcie
    assert 'Konflikt! Nauczyciel ma już zajęcia w tym czasie.' in html

    # Sprawdzenie, że nie dodano nowej serii
    series_count = LessonSeries.query.filter_by(student_id=student.id, teacher_id=teacher.id).count()
    assert series_count == 1  # tylko poprzednia seria istnieje