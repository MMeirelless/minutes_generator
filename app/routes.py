from io import BytesIO
from docx import Document
from flask import Blueprint, session, render_template, redirect, url_for, request, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User, Report, Trash
from .forms import LoginForm, RegistrationForm
from .services import report_generator, dict_to_html, send_verification_email
from werkzeug.security import generate_password_hash, check_password_hash
from json import dumps 
from datetime import datetime, timedelta
from hashlib import md5
from sqlalchemy.exc import IntegrityError
from random import randint, choices
from string import digits

main = Blueprint('main', __name__)

@main.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.new_report'))
    else:
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
    form = RegistrationForm()
    if current_user.is_authenticated:
        return redirect(url_for('main.new_report'))
    
    if request.method == 'POST':
        if form.validate_on_submit():
            verification_code = ''.join(choices(digits, k=6))
            session['email'] = form.email.data
            session['verification_code'] = verification_code
            session['username'] = form.username.data
            session['password'] = generate_password_hash(form.password.data)
            session['plan'] = form.plan.data
            session['user_pic'] = form.user_pic.data if form.user_pic.data != "" else f"user{randint(1, 6)}.webp"

            send_verification_email(form.email.data, verification_code)

            return redirect(url_for('main.verify_email'))
    return render_template('register.html', form=form)

@main.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if current_user.is_authenticated:
        return redirect(url_for('main.new_report'))
    
    if request.method == 'POST':
        user_code = request.form['verification_code']

        if user_code == session.get('verification_code'):
            existing_user = User.query.filter_by(email=session.get('email')).first()
            if existing_user:
                flash('Email já em uso. Por favor, escolha outro.', 'danger')
                return redirect(url_for('main.register'))
            
            user = User(username=session.get('username'), email=session.get('email'), password=session.get('password'), plan=session.get('plan'), user_pic=session.get('user_pic'))
            db.session.add(user)
            db.session.commit()

            session.pop('email', None)
            session.pop('username', None)
            session.pop('password', None)
            session.pop('plan', None)
            session.pop('user_pic', None)
            session.pop('verification_code', None)

            flash('Sua conta foi criada! Bem vindo!', 'success')
            return redirect(url_for('main.login'))
        
        else:
            flash('Código de verificação inválido.', 'danger')
            return redirect(url_for('main.verify_email'))
        
    return render_template('verify_email.html')

@main.route('/logout')
def logout():
    logout_user()
    flash('Você saiu, até logo :)', 'danger')
    return redirect(url_for('main.home'))

@main.route("/plans")
def plans():
    return render_template('plans.html')

@main.route("/my_account")
def my_account():
    if current_user.is_authenticated:
        return render_template('dashboard/my_account.html')
    else:
        return redirect(url_for('main.home'))

@main.route('/my_reports')
def my_reports():
    if current_user.is_authenticated:
        reports = Report.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard/my_reports.html', reports=reports)
    else:
        return redirect(url_for('main.home'))

@main.route('/new_report', methods=['GET', 'POST'])
def new_report():
    if current_user.is_authenticated:
        global output
        global doc_title
        html_content_title = "Novo Relatório"
        html_content = ""

        # Cleaning Trash
        user_trashes = Trash.query.filter_by(user_id=current_user.id).all()
        for trash in user_trashes:
            if trash.date < datetime.now()-timedelta(days=7):
                print(datetime.now()-trash.date)
                db.session.delete(trash)
                db.session.commit()
        
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
                html_content_title = doc_title.replace("_", " ").split(".")[0]
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
                return render_template('dashboard/new_report.html', html_content=html_content,is_report_generated="true",html_content_title=html_content_title)
            
        return render_template('dashboard/new_report.html', html_content=html_content,is_report_generated="false",html_content_title=html_content_title)
    else:
        return redirect(url_for('main.home'))

@main.route('/report_download')
def report_download():
    if current_user.is_authenticated:
        global output
        global doc_title
        try:
            return send_file(output, download_name=doc_title, as_attachment=True, mimetype='mainlication/vnd.openxmlformats-officedocument.wordprocessingml.document')
        except Exception as e:
            flash('Erro ao baixar o arquivo.', 'danger')
            return redirect(url_for('main.new_report'))
    
    else:
        return redirect(url_for('main.home'))

@main.route('/save_report', methods=["POST"])
def save_report():
    if request.method == 'POST' and current_user.is_authenticated:
        report = request.get_json()["html_content"]
        report_id = md5(f"{report}{datetime.now()}".encode()).hexdigest()
        user_id = current_user.id
        date = datetime.now()
        title = request.get_json()["html_content_title"]
        
        try:
            new_report = Report(report=report, report_id=report_id, user_id=user_id, date=date, title=title)
            db.session.add(new_report)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            flash('Esse relatório já foi salvo.', 'warning')
        
        return {"response":"report saved"}
    
    else:
        return redirect(url_for('main.home'))

@main.route('/delete_report', methods=["POST"])
def delete_report():
    if request.method == "POST" and current_user.is_authenticated and report_user_id == current_user.id:
        report_id = request.get_json()["report_id"]
        selected_report = Report.query.get(report_id)
        report_user_id = Report.query.filter_by(report_id=report_id).first().user_id
        # Moving to Trash        
        new_trash = Trash(report=selected_report.report, report_id=md5(f"{selected_report.report}{datetime.now()}".encode()).hexdigest(), user_id=selected_report.user_id, date=datetime.now(), title=selected_report.title)
        db.session.add(new_trash)

        # Deleting
        db.session.delete(selected_report)
        db.session.commit()

        return {"response":"report deleted"}
    
    else:
        return redirect(url_for('main.home'))

@main.route('/delete_account', methods=["POST"])
def delete_account():
    if request.method == "POST" and current_user.is_authenticated:
        
        reports = Report.query.filter_by(user_id=current_user.id).all()
        for report in reports:
            db.session.delete(report)
        
        trashes = Trash.query.filter_by(user_id=current_user.id).all()
        for trash in trashes:
            db.session.delete(trash)
        
        user = User.query.get_or_404(current_user.id)
        db.session.delete(user)
            
        db.session.commit()

        logout_user()
        flash('Conta apagada com sucesso.', 'success')

        return redirect(url_for('main.home'))
    else:
        return redirect(url_for('main.home'))

@main.route('/update_account', methods=["POST"])
def update_account():
    if request.method == "POST" and current_user.is_authenticated:
        
        data = request.get_json()

        username = data["username"]
        email = data["email"]

        is_updating_user = current_user.username != username
        is_updating_email = current_user.email != email

        if is_updating_user:
            current_user.username = username
            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
            
        if is_updating_email:
            print(f"Old Email: {current_user.email}\nNew Username: {email}")

        else:
            pass

        # pensar em lógica para atualizar senha

        flash('Conta atualizada com sucesso.', 'success')
        return {"response":"success"}
    else:
        return {"response":"access denied or error"}

@main.route('/delete_trash', methods=["POST"])
def delete_trash():
    if request.method == "POST" and current_user.is_authenticated and trash_user_id == current_user.id:
        trash_id = request.get_json()["report_id"]
        selected_trash = Trash.query.get(trash_id)
        trash_user_id = selected_trash.user_id
        db.session.delete(selected_trash)
        db.session.commit()
        flash('Report apagado com sucesso.', 'success')
        return {"response":"report saved"}
    
    else:
        return redirect(url_for('main.home'))

@main.route("/trash")
def trash():
    if current_user.is_authenticated:
        user_trash = Trash.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard/trash.html', user_trash=user_trash)

    else:
        return redirect(url_for('main.home'))

@main.route("/recording")
def recording():
    return render_template("recording.html")