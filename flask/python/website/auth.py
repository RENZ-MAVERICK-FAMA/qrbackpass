from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from . import db
from .models import User, Balance
import os
import qrcode
from flask_mail import Message, Mail
from itsdangerous import Serializer,BadSignature, SignatureExpired


auth = Blueprint('auth', __name__)

mail = Mail() 

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                qrcode = user.qrcode
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
        if request.method == 'POST':
            email = request.form.get('email')
            first_name = request.form.get('firstName')
            last_name = request.form.get('lastName')
            unit_info = request.form.get('unitinfo')
            unit_type = request.form.get('unittype')
            password1 = request.form.get('password1')
            password2 = request.form.get('password2')
            avatar = request.files['avatar'] if 'avatar' in request.files else None


            user = User.query.filter_by(email=email).first()
            if user:
                flash('Email already exists.', category='error')
            elif len(email) < 4:
                flash('Email must be greater than 3 characters.', category='error')
            elif len(first_name) < 2:
                flash('First name must be greater than 1 character.', category='error')
            elif len(last_name) < 2:
                flash('Last name must be greater than 1 character.', category='error')
            elif len(unit_info) < 2:
                flash('Unit Information must be greater than 1 character.', category='error')
            elif password1 != password2:
                flash('Passwords don\'t match.', category='error')
            elif len(password1) < 7:
                flash('Password must be at least 7 characters.', category='error')
            else:
                # Generate QR code
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
                qr.add_data(unit_info)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                qr_code_dir = os.path.join(current_app.root_path, 'static', 'qrcodes')
                os.makedirs(qr_code_dir, exist_ok=True)
                qr_code_filename = f'{email}_qrcode.png'
                qr_code_path = os.path.join(qr_code_dir, qr_code_filename)
                img.save(qr_code_path)

                # Save avatar
                if avatar:
                    avatar_filename = secure_filename(email + '.png')
                    avatar_path = os.path.join(current_app.root_path, 'static', 'avatars', avatar_filename)
                    avatar.save(avatar_path)
                else:
                    avatar_filename = 'default_avatar.png'  # Set a default avatar filename if no avatar is provided

                # Create new user
                new_user = User(email=email, first_name=first_name, last_name=last_name, unit_info=unit_info, unit_type=unit_type, qrcode=qr_code_filename,
                    password=generate_password_hash(password1, method='pbkdf2:sha256'), avatar=avatar_filename)

                new_balance = Balance(balance=0, user=new_user)
                db.session.add(new_balance)
                db.session.commit()

                login_user(new_user, remember=True)
                flash('Account created!', category='success')

        return render_template("sign_up.html", user=current_user)


@auth.route('/update_user', methods=['GET','POST'])
@login_required
def update_user():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user:
            user.first_name = request.form.get('editFirstName')
            user.last_name = request.form.get('editLastName')
            user.unit_info = request.form.get('editUnitInfo')
            user.email = request.form.get('editEmail')

            # Update password if provided
            new_password = request.form.get('editPassword')
            if new_password:
                user.password = generate_password_hash(new_password, method='pbkdf2:sha256')

            # Update profile picture if provided
            if 'editAvatar' in request.files:
                edit_avatar = request.files['editAvatar']
                if edit_avatar:
                    # Delete existing avatar file if it exists
                    if user.avatar:
                        existing_avatar_path = os.path.join(current_app.root_path, 'static', 'avatars', user.avatar)
                        if os.path.exists(existing_avatar_path):
                            os.remove(existing_avatar_path)

                    # Save new avatar file
                    avatar_filename = secure_filename(user.email + '.png')
                    avatar_path = os.path.join(current_app.root_path, 'static', 'avatars', avatar_filename)
                    edit_avatar.save(avatar_path)
                    user.avatar = avatar_filename

            db.session.commit()
            flash('User details updated successfully!', category='success')
        else:
            flash('User not found.', category='error')

    return redirect(url_for('views.home'))


@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_token(user.email)
            send_reset_email(user.email, token)
            flash('An email with instructions to reset your password has been sent.', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('Email address not found.', 'error')
    return render_template('forgot.html',user=None)

def generate_token(email):
    s = Serializer(current_app.config['SECRET_KEY'])  # Create Serializer instance
    token = s.dumps({'email': email})  # Generate token with expiration
    return token


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
        email = data['email']
        user = User.query.filter_by(email=email).first()
        if request.method == 'POST':
            new_password = request.form.get('password')
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            user.password = hashed_password
            db.session.commit()
            flash('Your password has been reset. You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
    except:
        flash('The reset link is invalid or has expired. Please try again.', 'error')
        return redirect(url_for('auth.forgot_password'))
    return render_template('reset_password.html')


def send_reset_email(email, token):
    reset_link = url_for('auth.reset_password', token=token, _external=True)

    
def send_reset_email(email, token):
    reset_link = url_for('auth.reset_password', token=token, _external=True)
    msg = Message('Password Reset Request', sender='renzoofama@gmail.com', recipients=[email])
    msg.body = f'''To reset your password, visit the following link:
{reset_link}
If you did not make this request, simply ignore this email and no changes will be made.
'''
    mail.send(msg)

   