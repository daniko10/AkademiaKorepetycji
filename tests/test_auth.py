from app import db, bcrypt

def test_login_wrong_password(client):
    response = client.post('/login', data={
        'email': 'student@example.com',
        'password': 'zlehaslo'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Logowanie' in response.data  # powinno pozostać na stronie logowania


def test_login_student(client):
    response = client.post('/login', data={
        'email': 'student@example.com',
        'password': 'haslo123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Dashboard' in response.data  # lub fragment strony dashboardu

def test_login_teacher(client):
    response = client.post('/login', data={
        'email': 'teacher@example.com',
        'password': 'nauczyciel123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Dashboard' in response.data  # albo inny fragment strony głównej nauczyciela

def test_login_admin(client):
    response = client.post('/login', data={
        'email': 'admin@example.com',
        'password': 'admin123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Panel Administratora' in response.data  # albo fragment panelu administratora

def test_login_unapproved_user(client):
    # Dodaj niezatwierdzonego studenta
    from app.models import Student
    student = Student(
        name='Anna',
        surname='Nowak',
        email='anna@example.com',
        password=bcrypt.generate_password_hash('tajne'),
        approved=False
    )
    db.session.add(student)
    db.session.commit()

    response = client.post('/login', data={
        'email': 'anna@example.com',
        'password': 'tajne'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'oczekuje na zatwierdzenie' in response.data

# 🔒 test: dostęp do dashboard bez logowania
def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=True)
    assert response.status_code == 200
    assert b"Logowanie" in response.data  # lub inny fragment strony logowania

# ✅ test: poprawne logowanie i sesja
def test_login_creates_session(client):
    response = client.post("/login", data={
        "email": "student@example.com",
        "password": "haslo123"
    }, follow_redirects=True)

    # powinien się zalogować
    assert response.status_code == 200
    assert b"Dashboard" in response.data  # dostosuj do swojej strony

    # sprawdzamy czy sesja istnieje
    with client.session_transaction() as sess:
        assert "_user_id" in sess
        assert sess["_user_id"] == "1"  # ID studenta
        assert sess["role"] == "student"

# 🚪 test: wylogowanie usuwa sesję
def test_logout_clears_session(client):
    # najpierw zaloguj się
    client.post("/login", data={
        "email": "student@example.com",
        "password": "haslo123"
    }, follow_redirects=True)

    # potem wyloguj
    response = client.get("/logout", follow_redirects=True)

    assert response.status_code == 200
    assert b"Logowanie" in response.data  # wrócił na login

    # sesja powinna być pusta
    with client.session_transaction() as sess:
        assert "user_id" not in sess


# 🛑 test: student nie ma dostępu do admin dashboard
def test_student_cannot_access_admin(client):
    # zaloguj się jako student
    client.post("/login", data={
        "email": "student@example.com",
        "password": "haslo123"
    }, follow_redirects=True)

    # próbujemy wejść na panel admina
    response = client.get("/admin/dashboard", follow_redirects=True)
    assert response.status_code == 403

def test_register_student(client):
    response = client.post("/register", data={
        "email": "newstudent@example.com",
        "password": "haslo123",
        "role": "student"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Rejestracja" in response.data  # albo komunikat o oczekiwaniu na akceptację admina


def test_register_teacher(client):
    response = client.post("/register", data={
        "email": "newteacher@example.com",
        "password": "haslo123",
        "role": "teacher"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Rejestracja" in response.data

def test_register_existing_email(client):
    # zakładamy, że student@example.com już istnieje
    response = client.post("/register", data={
        "email": "student@example.com",
        "password": "haslo123",
        "role": "student"
    }, follow_redirects=True)

    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert "Ten adres e-mail jest" in html