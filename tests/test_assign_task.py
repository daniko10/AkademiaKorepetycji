import io
from app.models import Task, Student, Teacher
from flask_login import login_user
from app import db

# helper do logowania nauczyciela
def login_teacher(client, teacher):
    with client.application.test_request_context():
        login_user(teacher)


def test_assign_task_form_renders(client):
    """Formularz powinien się wyświetlać dla zalogowanego nauczyciela."""
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    login_teacher(client, teacher)
    resp = client.get(f"/assign-task/{student.id}")
    assert resp.status_code == 200
    assert b"Nowe zadanie dla" in resp.data
    assert student.name.encode() in resp.data


def test_assign_task_success(client):
    """Tworzenie zadania powinno działać poprawnie."""
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    login_teacher(client, teacher)
    resp = client.post(
        f"/assign-task/{student.id}",
        data={
            "title": "Testowe zadanie",
            "description": "Opis testowego zadania",
            "due_date": "2030-01-01",
            "max_points": 50,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    task = db.session.query(Task).filter_by(title="Testowe zadanie", student_id=student.id).first()
    assert task is not None
    assert task.max_points == 50
    assert task.teacher_id == teacher.id


# def test_assign_task_missing_title(client):
#     """Brak tytułu powinien zwrócić błąd walidacji."""
#     student = db.session.query(Student).filter_by(email="student@example.com").first()
#     teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
#     login_teacher(client, teacher)
#     resp = client.post(
#         f"/assign-task/{student.id}",
#         data={
#             "title": "",
#             "description": "Opis",
#             "due_date": "2030-01-01",
#             "max_points": 10,
#         },
#         follow_redirects=True,
#     )
#     assert resp.status_code == 200
#     # Flask-WTF wyświetla komunikat walidacji
#     assert b"Pole wymagane" in resp.data or b"This field is required" in resp.data


def test_assign_task_with_attachment(client):
    """Można dodać zadanie z plikiem PDF."""
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    login_teacher(client, teacher)

    fake_file = (io.BytesIO(b"fake pdf content"), "test.pdf")

    resp = client.post(
        f"/assign-task/{student.id}",
        data={
            "title": "Zadanie z plikiem",
            "description": "Opis z plikiem",
            "due_date": "2030-01-01",
            "max_points": 100,
            "attachments": [fake_file],
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    task = db.session.query(Task).filter_by(title="Zadanie z plikiem", student_id=student.id).first()
    assert task is not None
    assert "test.pdf" in (task.teacher_attachments or "")


def test_assign_task_unauthorized_access(client):
    """Student nie powinien mieć dostępu do /assign-task/<id>."""
    student = db.session.query(Student).filter_by(email="student@example.com").first()
    teacher = db.session.query(Teacher).filter_by(email="teacher@example.com").first()
    client.post("/login", data={
        "email": student.email,
        "password": "haslo123"
    }, follow_redirects=True)

    resp = client.get(f"/assign-task/{student.id}")
    assert resp.status_code == 403