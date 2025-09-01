from app import db
from datetime import datetime, timedelta, timezone
from app.models import Student, Teacher, Task, LessonSeries
from flask_login import login_user

def login_student(client, student):
    """Zaloguj studenta w testach używając Flask-Login"""
    with client.application.test_request_context():
        login_user(student)


def test_student_dashboard_with_tasks(client):
    # Pobieramy istniejącego studenta i nauczyciela z bazy testowej
    student = Student.query.filter_by(email='student@example.com').first()
    teacher = Teacher.query.filter_by(email='teacher@example.com').first()

    # Dodajemy zadanie dla studenta
    task = Task(
        title='Zadanie testowe',
        description='Opis zadania',
        issued_at = datetime.now(timezone.utc),
        due_date = datetime.now(timezone.utc) + timedelta(days=7),
        student_id=student.id,
        teacher_id=teacher.id,
        submitted=False,
        max_points=10
    )
    db.session.add(task)
    db.session.commit()

    # Logujemy studenta
    login_student(client, student)

    # Wchodzimy na dashboard studenta
    response = client.get('/dashboard')
    assert response.status_code == 200
    html = response.data.decode()

    # Sprawdzamy dane studenta
    assert 'Jan Kowalski' in html
    assert 'student@example.com' in html

    # Sprawdzamy nauczyciela
    assert 'Anna Nowak' in html

    # Sprawdzamy zadanie
    assert 'Zadanie testowe' in html
    assert 'Opis zadania' in html
    assert '📩 Wyślij odpowiedź' in html


def test_student_dashboard_without_tasks(client):
    student = Student.query.filter_by(email='student@example.com').first()

    # Usuwamy wszystkie zadania studenta
    Task.query.filter_by(student_id=student.id).delete()
    db.session.commit()

    login_student(client, student)

    response = client.get('/dashboard')
    assert response.status_code == 200
    html = response.data.decode()

    # Sprawdzenie komunikatu o braku zadań
    assert 'Nie masz jeszcze żadnych zadań.' in html


def test_student_dashboard_calendar_section(client):
    student = Student.query.filter_by(email='student@example.com').first()
    login_student(client, student)

    response = client.get('/dashboard')
    assert response.status_code == 200
    html = response.data.decode()

    # Sprawdzamy, że przycisk do kalendarza jest widoczny
    assert '📅 Pokaż kalendarz' in html
    # Sprawdzamy, że kontener kalendarza istnieje
    assert 'id="calendarCard"' in html
    assert 'id="calendar"' in html

def test_student_lessons_endpoint(client):
    student = Student.query.filter_by(email='student@example.com').first()
    teacher = Teacher.query.filter_by(email='teacher@example.com').first()

    # Dodajemy serię zajęć (np. każdy poniedziałek we wrześniu)
    series = LessonSeries(
        teacher_id=teacher.id,
        student_id=student.id,
        day_of_week=0,  # poniedziałek
        start_time=datetime.strptime("10:00", "%H:%M").time(),
        end_time=datetime.strptime("11:00", "%H:%M").time(),
        start_date=datetime(2025, 9, 1).date(),
        end_date=datetime(2025, 9, 30).date()
    )
    db.session.add(series)
    db.session.commit()

    # Wywołujemy endpoint z zakresem obejmującym wrzesień
    response = client.get(
        f"/student/{student.id}/lessons?start=2025-09-01&end=2025-09-30"
    )
    assert response.status_code == 200
    data = response.get_json()

    # Sprawdzamy czy JSON zawiera wydarzenia
    assert isinstance(data, list)
    assert len(data) > 0

    # Sprawdzamy przykładowe pole
    event = data[0]
    assert "title" in event
    assert "start" in event
    assert "end" in event
    assert "Matematyka" in event["title"] or teacher.subject in event["title"]
