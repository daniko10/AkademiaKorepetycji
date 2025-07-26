# Dokumentacja aplikacji Flask – Akademia Korepetycji

## 1. Wprowadzenie

Aplikacja powstała w celu umożliwienia łatwego kontaktu pomiędzy uczniem i studentem. Umożliwia ona przypisywanie konkretnych zadań uczniom wraz z możliwością wysłania załączników, określenie deadlinów, maksymalnej liczby punktów do uzyskania. Interfejs ucznia również pozwala na przesłanie w ramach odpowiedzi konkretnych załączników. Użytkownik zewnętrzny po rejestracji musi czekać na zatwierdzenie jego konta przez Administratora, który również zarządza przydziałem nauczycieli do studentów. Jeden student może mieć wielu nauczycieli.

Aktualnie umożliwiamy rejestrację nauczycieli udzielających korepetycji jedynie z *matematyki*.

Projekt wykorzystuje:
- **Flask** (Python) jako framework webowy
- **SQLite** jako bazę danych

## 2. Instalacja i uruchomienie

```bash
git clone -b production https://github.com/daniko10/AkademiaKorepetycji.git
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 init_db.py
python3 run.py
```

## 3. Struktura projektu

```
├── app/
│   ├── __init__.py             # Inicjalizacja aplikacji Flask
│   ├── routes.py               # Główne trasy i logika widoków
│   ├── models.py               # Modele SQLAlchemy
│   ├── forms.py                # Formularze WTForms
│   ├── utils.py
├── static/
│   └── styles.css
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── home.html
│   ├── student_dashboard.html
│   ├── teacher_dashboard.html
│   ├── admin_dashboard.html
│   ├── assign_task.html
│   ├── submit_task.html
│   └── grade_task.html
├── uploads/                    # Przesyłane pliki (PDF, JPG, PNG)
├── database.db                 # Baza SQLite
├── init_db.py                  # Inicjalizacja bazy danych
├── run.py                      # Uruchamianie aplikacji
├── requirements.txt            # Zależności
└── venv/                       # Środowisko wirtualne
```

## 4. Konfiguracja

Konfiguracja aplikacji znajduje się w pliku `app/__init__.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database.db'
app.config['SECRET_KEY'] = '...'
app.config['UPLOAD_FOLDER'] = '../uploads'
```

## 5. API

### Autoryzacja i sesje

| Metoda   | Endpoint        | Opis                                           | Dostęp        |
|----------|------------------|------------------------------------------------|---------------|
| GET      | `/`              | Strona główna                                  | Publiczny     |
| GET/POST | `/login`         | Logowanie użytkownika                          | Publiczny     |
| GET/POST | `/register`      | Rejestracja nowego konta                       | Publiczny     |
| GET      | `/logout`        | Wylogowanie użytkownika                        | Zalogowany    |

### Dashboardy

| Metoda   | Endpoint                                 | Opis                                                     | Dostęp        |
|----------|------------------------------------------|----------------------------------------------------------|---------------|
| GET      | `/dashboard`                             | Przekierowanie na odpowiedni dashboard wg roli          | Zalogowany    |
| GET/POST | `/admin/dashboard`                       | Panel admina     | Administrator |
| GET      | `/admin/approve/<user_type>/<user_id>`   | Zatwierdzanie kont studenta lub nauczyciela              | Administrator |

### Obsługa zadań

| Metoda   | Endpoint                            | Opis                                                       | Dostęp     |
|----------|-------------------------------------|------------------------------------------------------------|------------|
| GET/POST | `/assign-task/<student_id>`         | Tworzenie zadania dla ucznia                               | Nauczyciel |
| GET/POST | `/submit-task/<task_id>`            | Przesyłanie odpowiedzi i załączników                       | Student    |
| GET/POST | `/grade-task/<task_id>`             | Ocenianie zadania ucznia                                   | Nauczyciel |

### Pliki

| Metoda | Endpoint               | Opis                          | Dostęp     |
|--------|------------------------|-------------------------------|------------|
| GET    | `/uploads/<filename>`  | Pobieranie przesłanych plików | Zalogowany |

### Kody odpowiedzi HTTP

| Kod | Znaczenie                               |
|-----|-----------------------------------------|
| 200 | OK – poprawna odpowiedź                 |
| 302 | Redirect            |
| 400 | Błąd walidacji / niewłaściwe dane       |
| 403 | Brak dostępu (rola użytkownika)         |
| 404 | Zasób nie znaleziony                    |
