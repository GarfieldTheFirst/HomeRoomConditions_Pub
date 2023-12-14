from flask import render_template, redirect, url_for, flash, request
from flask_table import Table, Col, ButtonCol
from werkzeug.urls import url_parse
from flask_login import login_required, login_user, logout_user, current_user
from app import db
from app.auth import bpr
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm
from app.utilities.decorators import admin_required
from app.models.roomdata import User, Role
from app.auth.email import send_password_reset_email
from app.db_handler.db_handler import get_all_stored_users, get_stored_user, \
    modify_stored_user_permissions, delete_stored_users


class UserTable(Table):
    id = Col('User id', th_html_attrs={"style": "width:10%"})
    name = Col('User name', th_html_attrs={"style": "width:10%"})
    email = Col('User email', th_html_attrs={"style": "width:10%"})
    status = Col('Status', th_html_attrs={"style": "width:10%"})
    change_status = ButtonCol('Confirm/Disallow', 'auth.confirm',
                              url_kwargs=dict(id='id'),
                              # this ends up in request.values as an identifier
                              th_html_attrs={"style": "width:10%"},
                              button_attrs={"name": "form_confirm"})
    delete = ButtonCol('Delete', 'auth.confirm',
                       url_kwargs=dict(id='id'),
                       th_html_attrs={"style": "width:10%"},
                       button_attrs={"name": "form_delete"})


class UserEntry(object):
    def __init__(self, id, name, email, status) -> None:
        self.id = id
        self.name = name
        self.email = email
        self.status = status


@bpr.route('auth/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role != Role.query.filter_by(name='Tentative').first():
            return redirect(url_for('home.home'))
        else:
            return redirect(url_for('auth.waiting'))
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
            next_page = url_for('home.home')
        if current_user.role == Role.query.filter_by(name='Tentative').first():
            next_page = url_for('auth.waiting')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)


@bpr.route('auth/confirm', methods=['GET', 'POST'])
@login_required
@admin_required
def confirm():
    users = []
    if request.method == "POST":
        if "form_confirm" in request.values:
            user_id_to_confirm = request.args['id']
            user_to_confirm = get_stored_user(id=user_id_to_confirm)
            modify_stored_user_permissions([user_to_confirm])
            flash("Changed user {}'s status.".format(user_to_confirm.username))
        if "form_delete" in request.values:
            user_id_to_delete = request.args['id']
            user_to_delete = get_stored_user(id=user_id_to_delete)
            delete_stored_users([user_to_delete])
            flash("Deleted user {}.".format(user_to_delete.username))
    stored_users = get_all_stored_users()
    for stored_user in stored_users:
        if not stored_user.is_administrator():
            users.append(UserEntry(id=stored_user.id,
                                   name=stored_user.username,
                                   status=stored_user.is_user(),
                                   email=stored_user.email))
    table = UserTable(users)
    table.table_id = "users"
    table.classes = ["table", "table-striped", "left-align"]
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('auth/user_verification.html',
                           title='Verify users',
                           user_table=table)


@bpr.route('auth/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@bpr.route('auth/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.role = Role.query.filter_by(default=True).first()
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)


@bpr.route('auth/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('home.home'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            'Check your email for the instructions to reset your password')
        return redirect(url_for('home.home'))
    return render_template('auth/reset_password_request.html',
                           title='Reset Password', form=form)


@bpr.route('auth/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home.home'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('home.home'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('home.home'))
    return render_template('auth/reset_password.html', form=form)


@bpr.route('auth/waiting', methods=['GET'])
def waiting():
    return render_template('auth/waiting.html')
