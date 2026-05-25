from flask import Blueprint, render_template, redirect, flash, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from .. import db, limiter
from ..models import User
from .forms import RegisterForm, LoginForm

auth = Blueprint('auth', __name__)

DUPLICATE_EMAIL_MSG = 'An account with this email already exists. Please log in.'


@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit('10 per hour')
def register():
    form = RegisterForm()

    if request.method == 'POST':
        existing = User.find_by_email(request.form.get('email', ''))
        if existing:
            flash(DUPLICATE_EMAIL_MSG, 'danger')
            return render_template('register.html', form=form)

    if form.validate_on_submit():
        email = User.normalize_email(form.email.data)
        if User.find_by_email(email):
            flash(DUPLICATE_EMAIL_MSG, 'danger')
            return render_template('register.html', form=form)

        hashed_pw = generate_password_hash(form.password.data)
        user = User(name=form.name.data.strip(), email=email, password=hashed_pw)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(DUPLICATE_EMAIL_MSG, 'danger')
            return render_template('register.html', form=form)

        flash('Registration successful!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit('20 per hour')
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_email(form.email.data)
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(request.args.get('next') or url_for('blog.home'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('auth.login'))
