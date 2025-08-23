from app import db
from flask_login import UserMixin
from sqlalchemy import Text
from datetime import datetime, timezone

class UserBase(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), nullable=False)
    surname = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

student_teacher = db.Table(
    'student_teacher',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id'), primary_key=True),
    db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id'), primary_key=True)
)

class Student(UserBase, UserMixin):
    __tablename__ = 'students'
    approved = db.Column(db.Boolean, default=False)
    teachers = db.relationship(
        'Teacher',
        secondary=student_teacher,
        back_populates='students'
    )

class Teacher(UserBase, UserMixin):
    __tablename__ = 'teachers'
    subject = db.Column(db.String(50))
    approved = db.Column(db.Boolean, default=False)
    students = db.relationship(
        'Student',
        secondary=student_teacher,
        back_populates='teachers'
    )

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    issued_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    due_date = db.Column(db.DateTime, nullable=False)
    max_points = db.Column(db.Integer, nullable=False, default=100)
    earned_points = db.Column(db.Integer, nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    student = db.relationship('Student', backref='tasks', lazy=True)
    teacher = db.relationship('Teacher', backref='assigned_tasks', lazy=True)
    student_answer = db.Column(db.Text, nullable=True)
    teacher_attachments = db.Column(Text, nullable=True)
    student_attachments = db.Column(Text, nullable=True)
    submitted = db.Column(db.Boolean, default=False)

class Administrator(UserBase, UserMixin):
    __tablename__ = 'administrators'

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)
    sender_role = db.Column(db.String(20), nullable=False)
    receiver_role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    