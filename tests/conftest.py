import pytest
from app import app, db, bcrypt
from app.models import Student, Teacher, Administrator

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # ułatwia testy formularzy

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            student = Student(
                name='Jan',
                surname='Kowalski',
                email='student@example.com',
                password=bcrypt.generate_password_hash('haslo123'),
                approved=True
            )
            db.session.add(student)
            teacher = Teacher(
                name='Anna',
                surname='Nowak',
                email='teacher@example.com',
                password=bcrypt.generate_password_hash('nauczyciel123'),
                approved=True
            )
            db.session.add(teacher)
            admin = Administrator(
                name='Adam',
                surname='Admin',
                email='admin@example.com',
                password=bcrypt.generate_password_hash('admin123'),
            )
            db.session.add(admin)

            db.session.commit()
            yield client
            db.drop_all()