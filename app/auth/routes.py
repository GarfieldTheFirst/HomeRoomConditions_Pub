from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_required, login_user, logout_user, current_user
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm
from app.decorators import admin_required
from app.models.roomdata import User, Role
from app.auth.email import send_password_reset_email


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        # defines where the user wanted to go from the 'next' argument after
        # they tried to access a login-required page
        next_page = request.args.get('next')
        # An attacker could insert a URL to a malicious site in the next
        # argument, so the application only redirects when the URL is relative,
        # which ensures that the redirect stays within the same site as the
        # application. To determine if the URL is relative or absolute, I
        # parse it with Werkzeug's url_parse() function and then check if the
        # netloc component is set or not.
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('views.home')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)


@bp.route('/confirm', methods=['GET', 'POST'])
@login_required
@admin_required
def confirm():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    role_to_be_verified = \
        Role.query.filter_by(name='Tentative').first()
    users_to_be_verified = \
        User.query.with_parent(role_to_be_verified).all()
    return render_template('auth/user_verification.html',
                           title='Verify users',
                           users_to_be_verified=users_to_be_verified)


@bp.route('/confirm/approve', methods=['POST'])
@login_required
@admin_required
def approve_user():
    user_id_to_be_granted_rights = request.form['user_id']
    user_to_be_granted_rights = User.query.filter_by(
        id=user_id_to_be_granted_rights).first()
    user_to_be_granted_rights.role = Role.query.filter_by(name='User').first()
    db.session.commit()
    if user_to_be_granted_rights.role.name == "User":
        return "User confirmed!"
    else:
        return "User not confirmed"


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            'Check your email for the instructions to reset your password')
        return redirect(url_for('views.home'))
    return render_template('auth/reset_password_request.html',
                           title='Reset Password', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('views.home'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('views.home'))
    return render_template('auth/reset_password.html', form=form)
