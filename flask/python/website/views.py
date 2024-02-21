from flask import Blueprint, render_template, request, flash, jsonify,redirect,url_for
from flask_login import login_required, current_user
from .models import Note,Transaction
from .models import User, Balance 
from . import db
from datetime import datetime, date,timedelta
import json
from calendar import monthcalendar,THURSDAY
import calendar
from datetime import date
from sqlalchemy import extract




views = Blueprint('views', __name__)
import calendar


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            new_note = Note(data=note, user_id=current_user.id) 
            db.session.add(new_note) 
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)


@views.route('/delete-note', methods=['POST'])
def delete_note():  
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})


@views.route('/topup', methods=['GET', 'POST'])
@login_required
def topup():
    if request.method == 'POST':
        amt = request.form.get('amt')
        user = User.query.get(current_user.id)
        
        # Get the user's balance entry from the Balance table
        balance_entry = Balance.query.filter_by(user_id=user.id).first()
        
        # If no balance entry exists, create a new one
        if not balance_entry:
            balance_entry = Balance(user_id=user.id, balance=0)
        
        # Update the balance amount
        balance_entry.balance += int(amt)
        
        # Create a new transaction
        transaction = Transaction(amount=int(amt), user_id=user.id, balance_id=balance_entry.id, type='TOPUP')
        
        # Commit the transaction and balance changes to the database
        db.session.add(transaction)
        db.session.commit()
        
        flash('Balance added!', category='success')
        return render_template("topup.html", user=current_user)
    return render_template("topup.html", user=current_user)







@views.route('/deduct', methods=['GET', 'POST'])
@login_required
def deduct():
    if request.method == 'POST':
       
        user = User.query.get(current_user.id)
        unit_type = user.unit_type
       

        if unit_type == 'Motorela':
            amt1 = 6
        elif unit_type == 'Multicab':
            amt1 = 10
            
            amt1 = unit_type
        # Get the payment date from the form
        payment_date_str = request.form.get('payment_date')
        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()

        # Ensure the payment date is not in the future
        today = date.today()
        if payment_date > today:
            flash('Cannot process payment for future dates', category='error')
            return redirect(url_for('views.deduct'))  # Redirect back to the form

        # Get the user's balance entry from the Balance table
        balance_entry = Balance.query.filter_by(user_id=user.id).first()

        # If no balance entry exists, return an error
        if not balance_entry:
            flash('No balance entry found', category='error')
            return redirect(url_for('views.deduct'))  # Redirect back to the form

       

        if balance_entry.balance < amt1:
            flash('Insufficient balance', category='error')
            return redirect(url_for('views.deduct'))  # Redirect back to the form

        # Check if a deduction has already been made for the selected date
        existing_transaction = Transaction.query.filter_by(user_id=user.id, date=payment_date).first()
        if existing_transaction:
            flash('Deduction already made for {}'.format(payment_date), category='error')
            return redirect(url_for('views.deduct'))  # Redirect back to the form

        # Deduct the amount from the balance
        balance_entry.balance -= amt1

        # Create a new transaction
        transaction = Transaction(amount=amt1, user_id=user.id, balance_id=balance_entry.id, type='PAYMENT', date=payment_date, date_of_payment=today)

        # Commit the transaction and balance changes to the database
        db.session.add(transaction)
        db.session.commit()

        flash('Balance deducted!', category='success')
        return redirect(url_for('views.deduct'))  # Redirect back to the form
    
    return render_template("deduct.html", user=current_user)  




@views.route('/payment_calendar', defaults={'year': None, 'month': None})
@views.route('/payment_calendar/<int:year>/<int:month>')
@login_required
def payment_calendar(year=None, month=None):
    if year is None or month is None:
        year = date.today().year
        month = date.today().month

    # Get the calendar data for the specified year and month
    calendar_data = [[{'day': day, 'is_paid': False, 'is_future': False} for day in week] for week in monthcalendar(year, month)]

    # Query transaction dates for the current month
    transaction_dates = {transaction.date.day for transaction in Transaction.query.filter(
        extract('year', Transaction.date) == year,
        extract('month', Transaction.date) == month,
        Transaction.user_id == current_user.id
    ).all()}

    # Update calendar data with transaction information
    for week in calendar_data:
        for day in week:
            if day['day'] != 0:
                day_date = date(year, month, day['day'])
                is_paid = day['day'] in transaction_dates
                is_future = day_date > date.today()
                day['is_paid'] = is_paid
                day['is_future'] = is_future

    # Render the template with the calendar data
    return render_template('payment_calendar.html', calendar_data=calendar_data, user=current_user, current_date=datetime(year, month, 1),calendar=calendar)



@views.route('/deduct_no_redirect', methods=['GET','POST'])
@login_required
def deduct_no_redirect():
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        unit_type = user.unit_type

        if unit_type == 'Motorela':
            amt1 = 6
        elif unit_type == 'Multicab':
            amt1 = 10
        else:
            amt1 = 0  # Set a default amount or handle the case for other unit types

        # Get the payment date from the form
        payment_date_str = request.form.get('payment_date')
        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()

        # Ensure the payment date is not in the future
        today = date.today()
        if payment_date > today:
            flash('Cannot process payment for future dates', category='error')
            return redirect(url_for('views.payment_calendar'))

        # Get the user's balance entry from the Balance table
        balance_entry = Balance.query.filter_by(user_id=user.id).first()

        # If no balance entry exists, return an error
        if not balance_entry:
            flash('No balance entry found', category='error')
            return redirect(url_for('views.payment_calendar'))


        if balance_entry.balance < amt1:
            flash('Insufficient balance', category='error')
            return redirect(url_for('views.payment_calendar'))


        # Check if a deduction has already been made for the selected date
        existing_transaction = Transaction.query.filter_by(user_id=user.id, date=payment_date).first()
        if existing_transaction:
            flash('Deduction already made for {}'.format(payment_date), category='error')
            return redirect(url_for('views.payment_calendar'))


        # Deduct the amount from the balance
        balance_entry.balance -= amt1

        # Create a new transaction
        transaction = Transaction(amount=amt1, user_id=user.id, balance_id=balance_entry.id, type='PAYMENT', date=payment_date, date_of_payment=today)

        # Commit the transaction and balance changes to the database
        db.session.add(transaction)
        db.session.commit()

        flash('Balance deducted!', category='success')

    return redirect(url_for('views.payment_calendar'))

