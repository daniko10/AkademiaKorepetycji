import io
import pytest
from app import db
from app.models import Task, Student, Teacher
from flask_login import login_user
from datetime import datetime, timezone


def login_student(client, student):
    with client.application.test_request_context():
        login_user(student)

def test_submit_task_form_renders(client):
    """Sprawdza, czy formularz odpowiedzi jest renderowany."""
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    task = Task(
        title="Testowe zadanie",
        description="Opis testowego zadania",
        due_date=datetime(2030, 1, 1),
        max_points=100,
        student_id=student.id,
        teacher_id=teacher.id,
    )
    db.session.add(task)
    db.session.commit()
    login_student(client, student)
    
    resp = client.get(f"/submit-task/{task.id}")
    assert resp.status_code == 200
    assert b"Twoja odpowied" in resp.data
    assert bytes(task.title, 'utf-8') in resp.data

def test_submit_task_success(client):
    """Wysyłanie odpowiedzi tekstowej powinno działać poprawnie."""
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    task = Task(
        title="Testowe zadanie",
        description="Opis testowego zadania",
        due_date=datetime(2030, 1, 1),
        max_points=100,
        student_id=student.id,
        teacher_id=teacher.id,
    )
    db.session.add(task)
    db.session.commit()
    login_student(client, student)

    resp = client.post(
        f"/submit-task/{task.id}",
        data={
            "answer": "Moja odpowied",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    updated_task = db.session.get(Task, task.id)
    assert updated_task.student_answer == "Moja odpowied"
    assert updated_task.submitted is True

def test_submit_task_with_attachment(client, tmp_path):
    """Wysyłanie odpowiedzi z załącznikiem."""
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    task = Task(
        title="Testowe zadanie",
        description="Opis testowego zadania",
        due_date=datetime(2030, 1, 1),
        max_points=100,
        student_id=student.id,
        teacher_id=teacher.id,
    )
    db.session.add(task)
    db.session.commit()
    login_student(client, student)

    # przygotowanie "fałszywego" pliku
    fake_file = (io.BytesIO(b"fake content"), "answer.pdf")

    resp = client.post(
        f"/submit-task/{task.id}",
        data={
            "answer": "Odpowiedź z plikiem",
            "attachments": [fake_file],
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert resp.status_code == 200
    updated_task = db.session.get(Task, task.id)
    assert "answer.pdf" in (updated_task.student_attachments or "")
