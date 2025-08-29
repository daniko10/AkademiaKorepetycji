# Dokumentacja aplikacji Flask – Akademia Korepetycji

## 1. Wprowadzenie

Aplikacja powstała w celu umożliwienia łatwego kontaktu pomiędzy uczniem i studentem. Umożliwia ona przypisywanie konkretnych zadań uczniom wraz z możliwością wysłania załączników, określenie deadlinów, maksymalnej liczby punktów do uzyskania. Interfejs ucznia również pozwala na przesłanie w ramach odpowiedzi konkretnych załączników. Użytkownik zewnętrzny po rejestracji musi czekać na zatwierdzenie jego konta przez Administratora, który również zarządza przydziałem nauczycieli do studentów. Jeden student może mieć wielu nauczycieli.

Aktualnie umożliwiamy rejestrację nauczycieli udzielających korepetycji jedynie z *matematyki*.

### Role użytkowników

Aplikacja obsługuje trzy typy użytkowników z różnymi uprawnieniami:

* Student

    * Odbiera przydzielone zadania
    * Przesyła rozwiązania i załączniki
    * Prowadzi chat z nauzycielem
    * Ma możliwość podglądu planu zajęć

* Nauczyciel

    * Tworzy i przypisuje zadania studentom
    * Ocenia rozwiązania
    * Ustawia, edytuje, usuwa zajęcia, ich termin i godzinę
    * Prowadzi chat ze studentem

* Administrator

    * Zatwierdza nowe konta studentów i nauczycieli
    * Przydziela nauczycieli do studentów
    * Ma wgląd w całość systemu


Projekt wykorzystuje:
- **Flask** (Python) jako framework webowy
- **SQLite** jako bazę danych

## 2. Wymagania systemowe:
Aplikacja została przetestowana w następujących środowiskach:
* Python: 3.12+
* pip: 24+
* Systemy operacyjne: Linux

W przypadku uruchamiania aplikacji na serwerze produkcyjnym zaleca się:
* Linux (Ubuntu/Debian)
* Serwer WWW: ------
* WSGI: ------

## 3. Instrukcje środowiska developerskiego

Debug mode: app.run(debug=True, port=5001)

### Uruchomienie aplikacji

Poniższe komendy dla terminala Linux kolejno:
* klonują repozytorium z GitHuba
* tworzy wirtualne środowisko Pythona
* aktywuje wirtualne środowisko Pythona
* instaluje wszystkie zależności projektu zapisane w pliku requirements.txt
* inicjuje bazę danych, tworzy jej pliki, wszystkie tabele i zależności
* inicjuje aplikację (domyślny adres uruchomienia: http://127.0.0.1:5001/)

```bash
git clone -b production https://github.com/daniko10/AkademiaKorepetycji.git
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 init_db.py
python3 run.py
```

Wszelkie zmiany (w tym w pliku .scss do .css) są na bieżąco kompilowane podczas trwania aplikacji.

Zawartość pliku .scss jest kompilowana do .css przy użyciu rozszerzenia sass, kompilacja odbywa się poprzez inicjację pliku run.py.

### Uruchamianie testów jednostkowych

Poniższy kod uruchamia testy jednostkowe znajdujące się w katalogu tests:

```bash
python -m pytest -v
```

Testy bazują na tymczasowej bazie danych, w pamięci RAM.

## 4. Struktura projektu

```
├── app/
│   ├── __init__.py             # Inicjalizacja aplikacji Flask
│   ├── routes.py               # Główne trasy i logika widoków
│   ├── models.py               # Modele SQLAlchemy
│   ├── forms.py                # Formularze WTForms
│   └── utils.py                # Funkcje pomocnicze
│
├── node_modules/               # Folder z bibliotekami zainstalowanymi przez npm/yarn
├── static/
│   ├── bootstrap/              # Pliki bootstrapa
│   ├── css/
│   │   └── prettierStyles.css  # Plik css stworzony przez kompilator sass
│   └── scss/
│       └── prettierStyles.scss # Arkusz stylów scss
│   
├── templates/
│   ├── base.html               # Podstawowy formularz strony, dziedziczony przez wszystkie poniższe
│   ├── login.html              # Formularz logowania
│   ├── register.html           # Formularz rejestracji
│   ├── home.html               # Strona główna/tytułowa
│   ├── student_dashboard.html  # Panel studenta
│   ├── teacher_dashboard.html  # Panel nauczyciela
│   ├── admin_dashboard.html    # Panel administratora
│   ├── assign_task.html        # Formularz tworzenia zadania/taska
│   ├── submit_task.html        # Formularz oddania zadania/taska
│   ├── grade_task.html         # Formularz oceny zadania/taska
│   ├── assign_lesson.html      # Formularz tworzenia nowej lekcji na planie
│   └── chat.html               # Panel komunikatora między nauczycielem, a studentem
├──tests
│   ├── conftest.py             # Podstawowe ustawienia testów
│   ├── test_admin.py           # Testy panelu administratora
│   ├── test_assign_task.py     # Testy formularza tworzenia zadania
│   ├── test_auth.py            # Testy autoryzacji użytkowników
│   ├── test_basic.py           # Testy ekranu głównego
│   ├── test_chat.py            # Testy chatu
│   ├── test_grade_task.py      # Testy formularza oceny zadania
│   ├── test_student.py         # Testy panelu studenta
│   ├── test_submit_task.py     # Testy formularza oddania zadania
│   └── test_teacher.py         # Testy panelu nauczyciela
│
├── uploads/                    # Przesyłane pliki (PDF, JPG, PNG)
├── database.db                 # Baza SQLite
├── init_db.py                  # Inicjalizacja bazy danych
├── run.py                      # Uruchamianie aplikacji
├── requirements.txt            # Zależności
└── venv/                       # Środowisko wirtualne
```

## 5. Architektura systemu:

### User → Frontend → Backend Flow

flowchart TD
    A[Użytkownik: Student / Nauczyciel / Admin] 
        --> B[Przeglądarka / Frontend: HTML + CSS + Bootstrap]

    B --> C[Flask App]
    C --> D[Routes (routes.py)]
    C --> E[Forms (forms.py)]
    C --> F[Models (models.py)]
    C --> G[Templates (Jinja2)]

    F --> H[(SQLite Database)]
    C --> I[(Uploads Folder)]
    C --> J[(Mail Server: Gmail SMTP)]

    style A fill:#f6d365,stroke:#333,stroke-width:2px
    style C fill:#c3f0ca,stroke:#333,stroke-width:2px
    style H fill:#fddde6,stroke:#333,stroke-width:2px
    style J fill:#e0bbff,stroke:#333,stroke-width:2px


### Przepływ użytkownika:

flowchart TD
    A[Strona główna] --> B[Logowanie / Rejestracja]

    B -->|Student| C[Panel studenta]
    B -->|Nauczyciel| D[Panel nauczyciela]
    B -->|Administrator| E[Panel administratora]

    %% Student
    C --> C1[Odbiera zadania]
    C --> C2[Przesyła rozwiązania]
    C --> C3[Przegląda plan zajęć]
    C --> C4[Chat z nauczycielem]

    %% Teacher
    D --> D1[Tworzy i przypisuje zadania]
    D --> D2[Ocenia rozwiązania]
    D --> D3[Zarządza zajęciami]
    D --> D4[Chat ze studentem]

    %% Admin
    E --> E1[Zatwierdza konta]
    E --> E2[Przydziela nauczycieli do studentów]
    E --> E3[Ma wgląd w system]

### Struktura bazy danych i powiązania 

erDiagram
    ADMINISTRATORS {
        INTEGER id PK
        VARCHAR name
        VARCHAR surname
        VARCHAR email
        VARCHAR password
    }

    STUDENTS {
        INTEGER id PK
        VARCHAR name
        VARCHAR surname
        VARCHAR email
        VARCHAR password
        BOOLEAN approved
    }

    TEACHERS {
        INTEGER id PK
        VARCHAR name
        VARCHAR surname
        VARCHAR email
        VARCHAR password
        BOOLEAN approved
        VARCHAR subject
    }

    MESSAGES {
        INTEGER id PK
        INTEGER sender_id
        INTEGER receiver_id
        VARCHAR sender_role
        VARCHAR receiver_role
        TEXT content
        DATETIME timestamp
    }

    LESSON_SERIES {
        INTEGER id PK
        INTEGER teacher_id FK
        INTEGER student_id FK
        INTEGER day_of_week
        TIME start_time
        TIME end_time
        DATE start_date
        DATE end_date
    }

    STUDENT_TEACHER {
        INTEGER student_id FK
        INTEGER teacher_id FK
    }

    TASKS {
        INTEGER id PK
        VARCHAR title
        TEXT description
        DATETIME issued_at
        DATETIME due_date
        INTEGER max_points
        INTEGER earned_points
        INTEGER student_id FK
        INTEGER teacher_id FK
        TEXT student_answer
        TEXT teacher_attachments
        TEXT student_attachments
        BOOLEAN submitted
    }

    %% Relacje
    STUDENTS ||--o{ LESSON_SERIES : has
    TEACHERS ||--o{ LESSON_SERIES : has
    STUDENTS ||--o{ STUDENT_TEACHER : has
    TEACHERS ||--o{ STUDENT_TEACHER : has
    STUDENTS ||--o{ TASKS : assigned
    TEACHERS ||--o{ TASKS : assigns

## 5. Konfiguracja

Konfiguracja aplikacji znajduje się w pliku `app/__init__.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = '../uploads'
```
Aplikacja korzysta z konfiguracji Flask-Mail do wysyłania wiadomości.  

```python
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
```

Kofiguracja pliku .env:
* MAIL_USERNAME=twoj_email@gmail.com    # Nazwa użytkownika adresu email
* MAIL_PASSWORD=twoje_haslo             # Hasło adresu email
* SECRET_KEY=super_tajny_klucz          # Klucz flask

## 6. API – rozszerzona wersja

### Autoryzacja i sesje

| Metoda   | Endpoint                                | Opis                                           | Dostęp        | Przykład request/response |
|----------|----------------------------------------|------------------------------------------------|---------------|--------------------------|
| GET      | `/`                                     | Strona główna                                  | Publiczny     | – |
| GET/POST | `/login`                                | Logowanie użytkownika                          | Publiczny     | – |
| GET/POST | `/register`                             | Rejestracja nowego konta                       | Publiczny     | – |
| GET      | `/logout`                               | Wylogowanie użytkownika                        | Zalogowany    | – |
| GET      | `/check_email?email=<email>`           | Sprawdzenie, czy email istnieje w systemie    | Publiczny     | **Response JSON:**<br>```json<br>{"exists": true}<br>``` |

---

### Dashboardy

| Metoda   | Endpoint                                 | Opis                                                     | Dostęp        |
|----------|------------------------------------------|----------------------------------------------------------|---------------|
| GET      | `/dashboard`                             | Przekierowanie na odpowiedni dashboard wg roli          | Zalogowany    |
| GET/POST | `/admin/dashboard`                       | Panel administratora, zarządzanie użytkownikami         | Administrator |
| GET      | `/admin/approve/<user_type>/<user_id>`   | Zatwierdzanie kont studenta lub nauczyciela             | Administrator |

---

### Obsługa zadań

| Metoda   | Endpoint                            | Opis                                                       | Dostęp     |
|----------|-------------------------------------|------------------------------------------------------------|------------|
| GET/POST | `/assign-task/<student_id>`         | Tworzenie zadania dla ucznia                               | Nauczyciel |
| GET/POST | `/submit-task/<task_id>`            | Przesyłanie odpowiedzi i załączników                       | Student    |
| GET/POST | `/grade-task/<task_id>`             | Ocenianie zadania ucznia                                   | Nauczyciel |

---

### Seria zajęć / lekcje

| Metoda   | Endpoint                                         | Opis                                                   | Dostęp        | Przykład request/response |
|----------|-------------------------------------------------|--------------------------------------------------------|---------------|--------------------------|
| GET/POST | `/lesson/assign/<student_id>/<teacher_id>`      | Tworzenie serii zajęć dla studenta                     | Zalogowany    | – |
| DELETE   | `/lesson/delete/<lesson_id>`                    | Usuwanie serii zajęć                                   | Zalogowany    | – |
| GET      | `/teacher/<teacher_id>/lessons?start=YYYY-MM-DD&end=YYYY-MM-DD` | Pobranie zajęć nauczyciela w przedziale dat | Zalogowany | **Response JSON:**<br>```json<br>[{"id":"series-1-2025-08-26","title":"Jan Kowalski","start":"2025-08-26T09:00:00","end":"2025-08-26T10:00:00"}]<br>``` |
| GET      | `/student/<student_id>/lessons?start=YYYY-MM-DD&end=YYYY-MM-DD` | Pobranie zajęć studenta w przedziale dat     | Zalogowany | **Response JSON:**<br>```json<br>[{"id":"series-1-2025-08-26","title":"Matematyka","start":"2025-08-26T09:00:00","end":"2025-08-26T10:00:00"}]<br>``` |

---

### Komunikacja / e-mail / chat

| Metoda   | Endpoint                                     | Opis                                               | Dostęp        | Przykład request/response |
|----------|---------------------------------------------|---------------------------------------------------|---------------|--------------------------|
| GET/POST | `/send-email/<email>/<purpose>`             | Wysyłanie wiadomości e-mail w zależności od celu (assign_task / submit_task / grade_task) | Zalogowany | – |
| GET/POST | `/chat/<student_id>/<teacher_id>/<role>`   | Wysyłanie i przeglądanie wiadomości między uczniem a nauczycielem | Zalogowany | **Response JSON:**<br>```json<br>[{"sender_id":1,"receiver_id":2,"sender_role":"student","receiver_role":"teacher","content":"Witaj","timestamp":"2025-08-26T09:00:00"}]<br>``` |
| GET      | `/uploads/<filename>`                        | Pobieranie przesłanych plików                     | Zalogowany    | – |

---

### Kody odpowiedzi HTTP

| Kod | Znaczenie                               |
|-----|-----------------------------------------|
| 200 | OK – poprawna odpowiedź                 |
| 302 | Redirect                                |
| 400 | Błąd walidacji / niewłaściwe dane       |
| 403 | Brak dostępu (rola użytkownika)         |
| 404 | Zasób nie znaleziony                    |

## 7. Deployment (Wdrożenie na serwer produkcyjny)

--------------------------------------------------

## 9. Bezpieczeństwo

* Hasła użytkowników są hashowane przy użyciu bcrypt (lub innej funkcji skrótu).

* Dostęp do endpointów jest ograniczony według roli użytkownika (Student / Nauczyciel / Admin).

* Pliki przesyłane przez użytkowników trafiają do katalogu uploads/ i są chronione przed dostępem z zewnątrz.

* Zaleca się ustawienie silnego SECRET_KEY w pliku .env.

## 12. Licencja i autorzy

Projekt jest dostępny na licencji ----.
Autorzy: Daniel Czapla, Piotr Szczerbiak
Repozytorium: https://github.com/daniko10/AkademiaKorepetycji

## 13. FAQ i troubleshooting

## 14. Użyte narzędzia i zależności:
* Flask 3.1.1
* Flask-SQLAlchemy 3.1.1
* Flask-Login 0.6.3
* Flask-Bcrypt 1.0.1



