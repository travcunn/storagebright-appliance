from app import db


class User(db.Model):
    """
    User model.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    firstName = db.Column(db.String(80))
    lastName = db.Column(db.String(80))
    password = db.Column(db.String(20))
    securityQuestion1 = db.Column(db.String(100))
    securityAnswer1 = db.Column(db.String(30))
    securityQuestion2 = db.Column(db.String(100))
    securityAnswer2 = db.Column(db.String(30))
    securityQuestion3 = db.Column(db.String(100))
    securityAnswer3 = db.Column(db.String(30))

    
    #  adds relationship between User and Barks so a user's barks can be displayed
    barks = db.relationship('Bark', backref='author', lazy='dynamic')
        
    def is_authenticated(self):
        """ Returns authentication status of a user. """
        return True

    def is_active(self):
        """ Returns true if the user is active. """
        return True

    def get_id(self):
        """ Rreturns the id of a user. """
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.email)
 

class Bark(db.Model):
    """
    Bark class for collection of barks in the feed.
    """
    id = db.Column(db.Integer, primary_key=True)
    barkBody = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    #  adds foreign key to tie each bark to a user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Bark %r>' % (self.barkBody)


class Friendship(db.Model):
    """
    Friendship class representing relationships between users.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    friend_id = db.Column(db.Integer)
