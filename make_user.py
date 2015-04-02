from __future__ import absolute_import
from app import db
from app.models import User

USERNAME = 'david@storagebright.com'
PASSWORD = 'test'

u = User()
u.email = USERNAME
u.set_password(PASSWORD)
db.session.add(u)
db.session.commit()

print("")
print("#### Created new user ####")
print("username: {}".format(USERNAME))
print("password: {}".format(PASSWORD))
print("##########################")
