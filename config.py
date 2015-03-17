import os
basedir = os.path.abspath(os.path.dirname(__file__))

# csrf protection
WTF_CSRF_ENABLED = False
SECRET_KEY = 'super-mario-brothers'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
