from app import db
from app.models import User


u = User()
u.email = 'test@google.com'
u.set_password('test')
db.session.add(u)
db.session.commit()
