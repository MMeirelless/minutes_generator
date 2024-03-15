from io import BytesIO
from docx import Document
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User, Report
from .forms import LoginForm, RegistrationForm
from .services import report_generator, dict_to_html
from werkzeug.security import generate_password_hash, check_password_hash
from json import dumps 
from datetime import datetime
from hashlib import md5
from sqlalchemy.exc import IntegrityError

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.new_report'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'Olá, {current_user.username}!', 'success')
            return redirect(url_for('main.new_report'))

        else:
            flash('Não foi possível entrar. Por favor, verifique seu e-mail e senha.', 'danger')

    return render_template('login.html', title='Login', form=form)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email já em uso. Por favor, escolha outro.', 'danger')
            return redirect(url_for('main.register'))
        
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, plan=form.plan.data)
        db.session.add(user)
        db.session.commit()
        flash('Sua conta foi criada! Bem vindo!', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)


@main.route('/logout')
def logout():
    logout_user()
    flash('Você saiu, até logo :)', 'danger')
    return redirect(url_for('main.home'))

@main.route("/plans")
def plans():
    return render_template('plans.html')

@main.route("/support")
def support():
    return render_template('support.html')

@main.route("/my_account")
def my_account():
    return render_template('dashboard/my_account.html')

@main.route('/my_reports')
def my_reports():
    reports = Report.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard/my_reports.html', reports=reports)


@main.route('/new_report', methods=['GET', 'POST'])
def new_report():
    global output
    global doc_title
    html_content = ""
    if request.method == 'POST':
        if 'audio_file' not in request.files:
            flash('Por favor, selecione um arquivo.', 'danger')
            return redirect(request.url)
        
        audio_file = request.files['audio_file']

        if audio_file.filename == '':
            flash('Por favor, selecione um arquivo.', 'danger')
            return redirect(request.url)
        
        if audio_file and audio_file.filename.endswith('.mp3'):
            doc = Document()
            result = report_generator(audio_file)  
            minutes = result[0]
            doc_title = f"{result[1]}.docx"
            download_url = url_for('main.report_download')
            html_content = dict_to_html(minutes, download_url)
            
            for key, value in minutes.items():
                heading = ' '.join(word.capitalize() for word in key.split('_'))
                doc.add_heading(heading, level=1)
                doc.add_paragraph(value)
                doc.add_paragraph()

            output = BytesIO()
            doc.save(output)
            output.seek(0)

            flash('Relatório gerado com sucesso!', 'success')
            return render_template('dashboard/new_report.html', html_content=html_content,is_report_generated="true")
        
    return render_template('dashboard/new_report.html', html_content=html_content,is_report_generated="false")

@main.route('/report_download')
def report_download():
    global output
    global doc_title
    try:
        return send_file(output, download_name=doc_title, as_attachment=True, mimetype='mainlication/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except Exception as e:
        flash('Erro ao baixar o arquivo.', 'danger')
        return redirect(url_for('main.new_report'))

@main.route('/save_report', methods=["POST"])
def save_report():
    if request.method == 'POST' and current_user.is_authenticated:
        report = request.get_json()["htmlReport"]
        report_id = md5(report.encode()).hexdigest()
        user_id = current_user.id
        date = datetime.now()
        title = f"Report {report_id}"

        try:
            new_report = Report(report=report, report_id=report_id, user_id=user_id, date=date, title=title)
            db.session.add(new_report)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            flash('Esse relatório já foi salvo.', 'warning')
        
        return {"reponse":"report saved"}
    
    return render_template('dashboard/new_report.html')

@main.route('/delete_report', methods=["POST"])
def delete_report():
    report_id = request.get_json()["report_id"]
    report_user_id = Report.query.filter_by(report_id=report_id).first().user_id
    if request.method == "POST" and current_user.is_authenticated and report_user_id == current_user.id:
        report = Report.query.get(report_id)
        db.session.delete(report)
        db.session.commit()
        flash('Report apagado com sucesso.', 'success')
        return render_template('dashboard/trash.html')

    return render_template('dashboard/my_reports.html')

@main.route("/trash")
def trash():
    return render_template('dashboard/trash.html')

@main.route("/recording")
def recording():
    return render_template("recording.html")