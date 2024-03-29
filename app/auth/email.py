from flask import render_template, current_app
from app.utilities.email import send_email


# This is the email functionality needed for this blueprint
def send_password_reset_email(user, host_name):
    token = user.get_reset_password_token()
    send_email('[Gs site] Reset Your Password',
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token,
                                         host_name=host_name),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token,
                                         host_name=host_name))
