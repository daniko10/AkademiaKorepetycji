import pytest
from flask import url_for
from app.models import Student, Teacher, Administrator
from flask_login import login_user

def login_admin(client, admin):
    with client.application.test_request_context():
        login_user(admin)

# GET - czy strona admina się renderuje
def test_admin_dashboard_page_renders(client):

    admin = Administrator.query.filter_by(email='admin@example.com').first()

    login_admin(client, admin)

    resp = client.get("/dashboard", follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # podstawowe nagłówki
    assert "Panel Administratora" in html
    assert "Studenci oczekujący na zatwierdzenie" in html
    assert "Nauczyciele oczekujący na zatwierdzenie" in html
    assert "Przypisz zatwierdzonych studentów" in html
    assert "Wszyscy użytkownicy w systemie" in html

    # sprawdź czy seedowane dane są widoczne
    assert "Jan Kowalski" in html
    assert "Anna Nowak" in html


# POST - zatwierdzanie studenta
def test_admin_approve_student(client):

    admin = Administrator.query.filter_by(email='admin@example.com').first()

    login_admin(client, admin)

    s = Student(
        name="Piotr",
        surname="Testowy",
        email="piotr@example.com",
        password="hashed",
        approved=False
    )
    from app import db
    db.session.add(s)
    db.session.commit()

    resp = client.post("/admin/dashboard", data={
        "student_id": s.id,
        "action": "approve_student"
    }, follow_redirects=True)

    db.session.refresh(s)
    assert resp.status_code == 200
    assert s.approved is True


# POST - usuwanie studenta
def test_admin_delete_student(client):

    admin = Administrator.query.filter_by(email='admin@example.com').first()

    login_admin(client, admin)

    from app import db
    s = db.session.query(Student).filter_by(email="student@example.com").first()
    assert s is not None

    resp = client.post("/admin/dashboard", data={
        "student_id": s.id,
        "action": "delete_student"
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert db.session.get(Student, s.id) is None


# POST - zatwierdzanie nauczyciela
def test_admin_approve_teacher(client):

    admin = Administrator.query.filter_by(email='admin@example.com').first()

    login_admin(client, admin)

    from app import db
    t = Teacher(
        name="Tomasz",
        surname="Nowy",
        email="tomasz@example.com",
        password="hashed",
        subject="Fizyka",
        approved=False
    )
    db.session.add(t)
    db.session.commit()

    resp = client.post("/admin/dashboard", data={
        "teacher_id": t.id,
        "action": "approve_teacher"
    }, follow_redirects=True)

    db.session.refresh(t)
    assert resp.status_code == 200
    assert t.approved is True


# POST - przypisywanie studenta do nauczyciela
def test_admin_assign_student_to_teacher(client):

    admin = Administrator.query.filter_by(email='admin@example.com').first()

    login_admin(client, admin)

    from app import db
    student = Student(
        name="Karol",
        surname="Nowak",
        email="karol@example.com",
        password="hashed",
        approved=True
    )
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    db.session.add(student)
    db.session.commit()

    resp = client.post("/admin/dashboard", data={
        "student_id": student.id,
        "teacher_ids": [teacher.id],
        "action": "assign_student"
    }, follow_redirects=True)

    db.session.refresh(student)
    assert resp.status_code == 200
    assert teacher in student.teachers


# POST - aktualizacja nauczycieli przypisanych do studenta
def test_admin_update_student_teachers(client):

    admin = Administrator.query.filter_by(email='admin@example.com').first()

    login_admin(client, admin)

    from app import db
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = Teacher(
        name="Ewa",
        surname="Nowa",
        email="ewa@example.com",
        password="hashed",
        subject="Biologia",
        approved=True
    )
    db.session.add(teacher)
    db.session.commit()

    resp = client.post("/admin/dashboard", data={
        "student_id": student.id,
        "teacher_ids": [teacher.id],
        "action": "update_teachers"
    }, follow_redirects=True)

    db.session.refresh(student)
    assert resp.status_code == 200
    assert teacher in student.teachers
