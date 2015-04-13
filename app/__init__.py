from flask import Flask
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.ldap import LDAP


app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
ldap = LDAP(app)

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.session_protection = "strong"


from app import models, views
