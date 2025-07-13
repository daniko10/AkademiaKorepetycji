from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, SelectField, TextAreaField, DateTimeField, IntegerField, MultipleFileField
from wtforms.validators import InputRequired, Email, Length, ValidationError
from wtforms.validators import NumberRange
from flask_wtf.file import FileField, FileAllowed
from app.models import Student

class RegisterForm(FlaskForm):
    role = RadioField(
        'Register as',
        choices=[('student', 'Uczeń'), ('teacher', 'Nauczyciel')],
        default='student'
    )
    name = StringField(validators=[InputRequired(), Length(min=4, max=15)])
    surname = StringField(validators=[InputRequired(), Length(min=3, max=15)])
    email = StringField(validators=[InputRequired(), Email(), Length(min=4, max=30)])
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=30)])
    submit = SubmitField('Register')

    subject = SelectField(
        'Subject',
        choices=[
            ('', '--- Wybierz przedmiot ---'),
            ('Matematyka', 'Matematyka')
        ]
    )

    def validate_email(self, email):
        if Student.query.filter_by(email=email.data).first():
            raise ValidationError('Email already exists.')

class LoginForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(min=4, max=30)])
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=30)])
    submit = SubmitField('Login')

class AssignTaskForm(FlaskForm):
    title = StringField('Tytuł zadania', validators=[InputRequired(), Length(min=3, max=100)])
    description = TextAreaField('Opis zadania')
    due_date = DateTimeField('Termin wykonania (RRRR-MM-DD)', format='%Y-%m-%d', validators=[InputRequired()])
    max_points = IntegerField('Maksymalna liczba punktów', validators=[InputRequired(), NumberRange(min=1, max=100)])
    attachments  = MultipleFileField(
        'Załącznik od nauczyciela (PDF, PNG, JPG)',
        validators=[FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Dozwolone tylko PDF lub obrazy')], render_kw={'multiple' : True, 'accept': '.pdf,.png,.jpg,.jpeg'}
    )
    submit = SubmitField('Utwórz zadanie')

class TaskSubmissionForm(FlaskForm):
    answer = TextAreaField('Odpowiedź', validators=[InputRequired(), Length(min=3, max=500)])
    attachments  = MultipleFileField(
        'Załącznik od studenta (PDF, PNG, JPG)',
        validators=[FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Dozwolone tylko PDF lub obrazy')], render_kw={'multiple' : True, 'accept': '.pdf,.png,.jpg,.jpeg'}
    )
    submit = SubmitField('Prześlij zadanie')

class GradeTaskForm(FlaskForm):
    earned_points = IntegerField("Liczba punktów", validators=[
        InputRequired(),
        NumberRange(min=0, max=100, message="Punkty muszą być w zakresie 0–100")
    ])
    submit = SubmitField("Zapisz ocenę")