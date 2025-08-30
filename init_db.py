from app import create_app, db
from app.models import Student, Teacher, Administrator, Task, Message, LessonSeries

app = create_app()

with app.app_context():
    db.create_all()
    print("Database and tables created successfully.")