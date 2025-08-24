import pytest
from app.models import Message, Student, Teacher
from flask_login import login_user


def login_student(client, student):
    with client.application.test_request_context():
        login_user(student)

def login_teacher(client, teacher):
    with client.application.test_request_context():
        login_user(teacher)

# 1. Render strony chatu
def test_chat_page_renders(client):
    from app import db
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    login_student(client, student)

    resp = client.get(f"/chat/{student.id}/{teacher.id}/student", follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    assert "Chat" in html
    assert "Brak wiadomości" in html or "Uczeń:" in html or "Nauczyciel:" in html
    assert '<form' in html


# 2. Brak wiadomości
def test_chat_empty(client):
    from app import db
    Message.query.delete()
    db.session.commit()

    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    login_student(client, student)

    resp = client.get(f"/chat/{student.id}/{teacher.id}/student", follow_redirects=True)
    html = resp.get_data(as_text=True)

    assert "Brak wiadomości." in html


# 3. Render wiadomości od nauczyciela i ucznia
def test_chat_messages_render(client):
    from app import db
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()

    msg1 = Message(
        sender_id=student.id,
        receiver_id=teacher.id,
        sender_role="student",
        receiver_role="teacher",
        content="Cześć, mam pytanie."
    )
    msg2 = Message(
        sender_id=teacher.id,
        receiver_id=student.id,
        sender_role="teacher",
        receiver_role="student",
        content="Dzień dobry, słucham."
    )
    
    db.session.add_all([msg1, msg2])
    db.session.commit()

    login_student(client, student)

    resp = client.get(f"/chat/{student.id}/{teacher.id}/student", follow_redirects=True)
    html = resp.get_data(as_text=True)

    assert "Uczeń:" in html
    assert "Nauczyciel:" in html
    assert "Cześć, mam pytanie." in html
    assert "Dzień dobry, słucham." in html


# 4. Wysyłanie wiadomości
def test_chat_send_message(client):
    from app import db
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    login_student(client, student)

    resp = client.post(f"/chat/{student.id}/{teacher.id}/student", data={
        "message": "Nowa wiadomość testowa",
        "submit": True
    }, follow_redirects=True)

    assert resp.status_code == 200

    # sprawdzamy w bazie
    msg = db.session.query(Message).filter_by(content="Nowa wiadomość testowa").first()
    assert msg is not None
    assert msg.sender_role == "student"

    html = resp.get_data(as_text=True)
    assert "Nowa wiadomość testowa" in html