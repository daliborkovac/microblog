from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import os
from flask.ext.login import LoginManager    # Flask-Login extension will handle users logged in state
from flask.ext.openid import OpenID         # Flask-OpenID extension will handle authentication
from config import basedir, ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD

# create a Flask application object
app = Flask(__name__)
# Read config settings from config.py. This populates a list named "config" in our app object with
# all the config information from config.py. We can access that information like this:
#    app.config['CONFIG_ITEM_NAME']     e.g.: app.config['OPENID_PROVIDERS']
app.config.from_object('config')
db = SQLAlchemy(app)

# initialization for Flask-Mail
from flask.ext.mail import Mail
mail = Mail(app)     # this is the object that will connect to the SMTP server and send the emails for us

# initialization for Flask-Login
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'   # automatically redirect to this view if the user is not logged in yet and tries
                          # to access one of the views "protected" by login_required decorator
oid = OpenID(app, os.path.join(basedir, 'tmp'))   # this is where OpenID will be storing its files

# To work with translations we are going to use a package called Babel, along with its Flask extension Flask-Babel.
# This is the initialization of that extension for our application.
from flask.ext.babel import Babel
babel = Babel(app)

from app import views   # Decorators in views.py will cause the routes to be mapped to appropriate functions.
                        # That will happen during initialization of "views" package.
                        # And when the request comes from the browser via those routes the appropriate function
                        # will be called to supply the response.
from app import models

# Normally, error messages are displayed to stderr.
# Here we will set up a logger that will send us an email every time an error occurrs, and we will also
# set up logging to a file.
if not app.debug:
    # We're doing this only if we're not running in debug mode.
    # If we are in debug mode then this is not necessary since we get the whole error stack displayed anyway.
    import logging
    from logging.handlers import SMTPHandler, RotatingFileHandler

    # setup mail handler
    credentials = None
    if MAIL_USERNAME or MAIL_PASSWORD:
        credentials = (MAIL_USERNAME, MAIL_PASSWORD)
    mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT),
                               'no-reply@' + MAIL_SERVER,
                               ADMINS,
                               'microblog failure',
                               credentials)
    mail_handler.setLevel(logging.ERROR)   # we want to log only errors
    # add this mail handler as logger in app
    app.logger.addHandler(mail_handler)

    # setup file handler
    # we will limit the log file size to 1MB, and we will keep the last 10 log files
    file_handler = RotatingFileHandler('tmp/microblog.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    # add this file handler as logger in app
    app.logger.addHandler(file_handler)
    # insert a log entry manually
    app.logger.info('microblog startup')


# This just tells Jinja2 to expose our class as a global variable momentjs to all templates.
# So, we will use momentjs in our templates when we want to reference class MomentJS.
from .momentjs import MomentJS
app.jinja_env.globals['momentjs'] = MomentJS

