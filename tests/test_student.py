from app import db
from datetime import datetime, timedelta, timezone
from app.models import Student, Teacher, Task
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
