import pytest
import os
from app import create_app, db, bcrypt
from app.models import Student, Teacher, Administrator
from app.config import TestConfig

# Ścieżka do pliku bazy testowej (jeśli używasz SQLite)
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), 'test.db')


@pytest.fixture
def app():
    """Tworzy aplikację w trybie testowym i bazę danych."""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        # przykładowe dane
        student = Student(
            name='Jan',
            surname='Kowalski',
            email='student@example.com',
            password=bcrypt.generate_password_hash('haslo123'),
            approved=True
        )
        teacher = Teacher(
            name='Anna',
            surname='Nowak',
            email='teacher@example.com',
            password=bcrypt.generate_password_hash('nauczyciel123'),
            subject='Matematyka',
            approved=True
        )
        admin = Administrator(
            name='Adam',
            surname='Admin',
            email='admin@example.com',
            password=bcrypt.generate_password_hash('admin123'),
        )

        db.session.add_all([student, teacher, admin])
        teacher.students.append(student)
        db.session.commit()

    yield app

    # Sprzątanie po testach
    with app.app_context():
        db.session.remove()
        db.drop_all()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture
def client(app):
    """Zwraca klienta testowego Flask"""
    return app.test_client()