from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from enum import Enum
from sqlalchemy.orm import relationship

class TransactionType(Enum):
    TOPUP = 'top-up'
    PAYMENT = 'payment'
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Balance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship('User', back_populates='balance')
 
    
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer)
    date_of_payment = db.Column(db.DateTime(timezone=True),default=func.now() )
    date = db.Column(db.Date,unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    balance_id = db.Column(db.Integer, db.ForeignKey('balance.id'))
    type = db.Column(db.Enum(TransactionType))
    user = db.relationship('User', backref='transactions')
    balance = db.relationship('Balance', backref='transactions')


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    unit_info = db.Column(db.String(150))
    unit_type = db.Column(db.String(150))
    qrcode = db.Column(db.String(150))
    avatar = db.Column(db.String(150))
    notes = db.relationship('Note', backref='user')
    balance = db.relationship('Balance', back_populates='user', uselist=False)
