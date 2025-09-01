from datetime import datetime, timedelta, timezone
from app.models import Teacher, Student, Task, db, LessonSeries
from flask_login import login_user
from flask import url_for

def login_teacher(client, teacher):
    with client.application.test_request_context():
        login_user(teacher)

def test_teacher_dashboard_with_students_and_tasks(client):
    # Pobieramy nauczyciela i studenta z bazy testowej
    teacher = Teacher.query.filter_by(email='teacher@example.com').first()
    student = Student.query.filter_by(email='student@example.com').first()

    # Dodajemy zadanie dla studenta przypisane przez nauczyciela
    task = Task(
        title='Zadanie testowe od nauczyciela',
        description='Opis zadania dla ucznia',
        issued_at=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        student_id=student.id,
        teacher_id=teacher.id,
        submitted=False,
        max_points=10
    )
    db.session.add(task)
    db.session.commit()

    # Logujemy nauczyciela
    login_teacher(client, teacher)

    # Wejście na dashboard nauczyciela
    response = client.get('/dashboard')
    assert response.status_code == 200
    html = response.data.decode()

    # Sprawdzamy dane nauczyciela
    assert f"{teacher.name} {teacher.surname}" in html
    assert teacher.subject in html

    # Sprawdzamy, że student jest wyświetlony
    assert f"{student.name} {student.surname}" in html
    assert student.email in html

    # Sprawdzamy, że zadanie jest widoczne pod studentem
    assert 'Zadanie testowe od nauczyciela' in html
    assert 'Nieoddane' in html  # bo submitted=False
    assert f'Maks. pkt: {task.max_points}' not in html  # dashboard nauczyciela pokazuje max pkt tylko po ocenieniu?

    # Sprawdzamy link do przypisania nowego zadania
    assert url_for('main.assign_task', student_id=student.id) in html
    # Sprawdzamy link do czatu
    assert url_for('main.chat', student_id=student.id, teacher_id=teacher.id, role='teacher') in html

def test_teacher_dashboard_calendar_section(client):
    teacher = Teacher.query.filter_by(email='teacher@example.com').first()
    login_teacher(client, teacher)

    response = client.get('/dashboard')
    assert response.status_code == 200
    html = response.data.decode()

    # Sprawdzamy przycisk do rozwijania kalendarza
    assert '📅 Pokaż kalendarz' in html
    # Sprawdzamy, że kontener kalendarza istnieje
    assert 'id="calendarCard"' in html
    assert 'id="calendar"' in html

def test_teacher_dashboard_assign_lesson_link(client):
    teacher = Teacher.query.filter_by(email='teacher@example.com').first()
    student = Student.query.filter_by(email='student@example.com').first()
    login_teacher(client, teacher)

    response = client.get('/dashboard')
    html = response.data.decode()

    # Sprawdzamy link do przypisania nowej serii lekcji
    assert url_for('main.assign_lesson', student_id=student.id, teacher_id=teacher.id) in html

def test_teacher_lessons_endpoint(client):
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
        f"/student/{teacher.id}/lessons?start=2025-09-01&end=2025-09-30"
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
