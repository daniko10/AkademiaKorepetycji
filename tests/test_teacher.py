from datetime import datetime, timedelta, timezone
from app.models import Teacher, Student, Task, db
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
    assert url_for('assign_task', student_id=student.id) in html
    # Sprawdzamy link do czatu
    assert url_for('chat', student_id=student.id, teacher_id=teacher.id, role='teacher') in html
