from app import db
from flask_login import UserMixin
from datetime import datetime

class UserBase(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), nullable=False)
    surname = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

class Student(UserBase, UserMixin):
    __tablename__ = 'students'
    approved = db.Column(db.Boolean, default=False)

class Teacher(UserBase, UserMixin):
    __tablename__ = 'teachers'
    subject = db.Column(db.String(50))
    approved = db.Column(db.Boolean, default=False)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    max_points = db.Column(db.Integer, nullable=False, default=100)
    earned_points = db.Column(db.Integer, nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    student = db.relationship('Student', backref='tasks', lazy=True)
    teacher = db.relationship('Teacher', backref='assigned_tasks', lazy=True)
    student_answer = db.Column(db.Text, nullable=True)
    teacher_attachment = db.Column(db.String(255), nullable=True)
    student_attachment = db.Column(db.String(255), nullable=True)
    submitted = db.Column(db.Boolean, default=False)

class Administrator(UserBase, UserMixin):
    __tablename__ = 'administrators'