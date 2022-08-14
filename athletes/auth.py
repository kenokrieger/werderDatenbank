from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user

from howami.models import User
from howami.db import DATABASE
from howami.account_setup import create_default_trackers

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Anmeldung erfolgreich!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Fehler: Falsches Passwort.', category='error')

        else:
            flash('Es existiert kein Konto mit dieser E-Mail Adresse',
                  category='error')
    return render_template("login.html", user=current_user)


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        fullname = request.form.get('name')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Es existiert bereits ein Konto mit dieser E-Mail-Adresse!',
                  category='error')
        elif password1 != password2:
            flash('Passwörter stimmen nicht überein', category='error')
        else:
            new_user = User(
                fullname=fullname, email=email,
                password=generate_password_hash(password1, method='sha256')
            )
            DATABASE.session.add(new_user)
            DATABASE.session.commit()
            create_default_trackers(new_user)
            flash('Registrierung erfolgreich!', category='success')

    return render_template("sign_up.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Du wurdest abgemeldet.', category='success')
    return redirect(url_for('auth.login'))
