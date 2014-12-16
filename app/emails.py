from flask.ext.mail import Message
from app import mail, app
from config import ADMINS
from flask import render_template
from .decorators import async


@async              # our custom decorator from .decorators
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject=subject,
                  sender=sender,
                  recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # Instead of sending the email from here ( mail.send(msg) ), we'll create and start a new thread to send
    # the email in the background, so this process doesn't have to wait for the email to get sent.
    send_async_email(app, msg)


def follower_notification(followed, follower):
    send_email(subject="[microblog] {} is now following you!".format(follower.nickname),
               sender=ADMINS[0],
               recipients=[followed.email],
               text_body=render_template("follower_email.txt", user=followed, follower=follower),
               html_body=render_template("follower_email.html", user=followed, follower=follower))
