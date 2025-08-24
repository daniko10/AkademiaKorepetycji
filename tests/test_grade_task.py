import io
import pytest
from app import db
from app.models import Task, Student, Teacher
from flask_login import login_user
from datetime import datetime


def login_teacher(client, teacher):
    with client.application.test_request_context():
        login_user(teacher)

def test_grade_task_form_renders(client):
    """Sprawdza, czy formularz oceny zadania jest renderowany."""
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    
    task = Task(
        title="Zadanie do oceny",
        description="Opis zadania",
        due_date=datetime(2030, 1, 1),
        max_points=100,
        student_id=student.id,
        teacher_id=teacher.id,
        student_answer="Odpowiedz ucznia",
        submitted=True
    )
    db.session.add(task)
    db.session.commit()

    login_teacher(client, teacher)
    resp = client.get(f"/grade-task/{task.id}")
    assert resp.status_code == 200
    assert b"Zadanie do oceny" in resp.data
    assert b"Odpowiedz ucznia" in resp.data
    assert b"Max 100 pkt" in resp.data

def test_grade_task_success(client):
    """Przydzielanie punktów powinno działać poprawnie."""
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    
    task = Task(
        title="Zadanie do oceny",
        description="Opis zadania",
        due_date=datetime(2030, 1, 1),
        max_points=50,
        student_id=student.id,
        teacher_id=teacher.id,
        student_answer="Odpowiedz ucznia",
        submitted=True
    )
    db.session.add(task)
    db.session.commit()

    login_teacher(client, teacher)
    resp = client.post(
        f"/grade-task/{task.id}",
        data={"earned_points": 45},
        follow_redirects=True
    )
    assert resp.status_code == 200

    # odświeżenie obiektu z bazy
    updated_task = db.session.get(Task, task.id)
    assert updated_task.earned_points == 45
