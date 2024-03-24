from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, PasswordField, BooleanField, SubmitField, SelectField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo

# Exemplo de formulário
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar acesso')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    username = StringField('Nome', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    plan = SelectField('Plano', choices=[('Grátis', 'Grátis'), ('Pro', 'Pro'), ('Empresarial', 'Empresarial')])
    user_pic = HiddenField("Foto do Usuário")
    submit = SubmitField('Cadastrar-se')
    
    def validate_email(self, email):
        from .models import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email address.')


