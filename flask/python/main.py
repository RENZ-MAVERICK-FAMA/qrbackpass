from website import create_app
from flask_mail import Mail

app = create_app()
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'renzoofama@gmail.com'
app.config['MAIL_PASSWORD'] = 'fhxm zopa etlh lcmu'

mail = Mail(app)  # Initialize Flask-Mail

if __name__ == '__main__':
    app.run(debug=True, port=8000)
