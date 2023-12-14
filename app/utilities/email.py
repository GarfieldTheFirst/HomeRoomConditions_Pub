from flask_mail import Message
from flask import current_app
from app import mail
from threading import Thread

# Flask-Mail supports some features that I'm not utilizing here such as Cc and
# Bcc lists. Be sure to check the Flask-Mail Documentation if you are
# interested in those options.


# The send_async_email function now runs in a background thread, invoked via
# the Thread class in the last line of send_email(). With this change, the
# sending of the email will run in the thread, and when the process completes
# the thread will end and clean itself up.
def send_async_email(app, msg):
    # When working with threads there is an important design aspect of Flask
    # that needs to be kept in mind. Flask uses contexts to avoid having to
    # pass arguments across functions.
    # Here, for instance, this is the app.config object
    with app.app_context():
        with mail.connect() as conn:
            conn.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # if a lot of emails need to be sent, start a thread in the background
    # that handles this task-based
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()
