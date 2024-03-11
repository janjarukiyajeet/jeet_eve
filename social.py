import secrets
from flask import Flask, request, jsonify
import random
import smtplib
from email.mime.text import MIMEText
from flask_wtf.csrf import generate_csrf
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///about1.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['JWT_SECRET_KEY'] = 'dc6f8cf55952d4550b2a54a1a79b6398'
jwt = JWTManager(app)
db = SQLAlchemy(app)

csrf = CSRFProtect(app)


class User(db.Model):
    username = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(80))
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    email = db.Column(db.String(120))
    mobile = db.Column(db.String(10))
    gender = db.Column(db.String(10))
    otp = db.Column(db.Integer)


class ResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_username = db.Column(db.String(80), db.ForeignKey('user.username'))
    token = db.Column(db.String(100), unique=True, nullable=False)


def send_otp_email(receiver_email, subject, body, otp):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'etemp7354@gmail.com'
    smtp_password = 'fomx muls ofkf egdk'

    sender_email = 'My_Email@gmail.com'

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, [receiver_email], msg.as_string())


@app.route('/signup', methods=['POST'])
@csrf.exempt
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    mobile = data.get('mobile')
    email = data.get('email')
    gender = data.get('gender')

    if username and password and first_name and last_name and email and mobile and gender:
        existing_user = db.session.query(User).get(username)
        if existing_user:
            return jsonify({"error": "Username already exists"}), 400

        new_user = User(username=username, password=password, first_name=first_name, last_name=last_name, email=email,
                        mobile=mobile, gender=gender, otp=None)
        db.session.add(new_user)
        db.session.commit()

        csrf_token = generate_csrf()

        response = jsonify({"message": "Signup successful"})
        response.headers["X-CSRF-TOKEN"] = csrf_token
        return response, 200

    else:
        return jsonify({"error": "Username, password, email, mobile and gender are required"}), 400


@app.route('/login', methods=['POST'])
@csrf.exempt
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        existing_user = User.query.filter_by(username=username, password=password).first()

        if existing_user:
            otp = random.randint(1000, 9999)
            existing_user.otp = otp
            db.session.commit()

            subject = 'Your OTP for User Profile Management'
            body = f'Your OTP is: {otp}'

            send_otp_email(existing_user.email, subject, body, otp)

            return jsonify({"message": "Login successful. OTP generated and sent via email"}), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    return jsonify({"error": "Invalid request"}), 400


@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


@app.route('/verify_otp', methods=['POST'])
@csrf.exempt
def verify_otp():
    data = request.json
    username = data.get('username')
    otp_attempt = data.get('otp')

    existing_user = User.query.filter_by(username=username, otp=otp_attempt).first()

    if existing_user:
        existing_user.otp = None
        db.session.commit()
        return jsonify({"message": "OTP verification successful"}), 200
    else:
        return jsonify({"error": "Invalid OTP"}), 401


@app.route('/get_profile/<username>', methods=['GET'])
@csrf.exempt
def get_profile(username):
    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        user_profile = {
            'username': existing_user.username,
            'password': existing_user.password,
            'first_name': existing_user.first_name,
            'last_name': existing_user.last_name,
            'email': existing_user.email,
            'mobile': existing_user.mobile,
            'gender': existing_user.gender
        }
        return jsonify(user_profile), 200
    else:
        return jsonify({"error": "User not found"}), 404


@app.route('/update_profile/<username>', methods=['PUT'])
@csrf.exempt
def update_profile(username):
    data = request.json

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        existing_user.password = data.get('password', existing_user.password)
        existing_user.first_name = data.get('first_name', existing_user.first_name)
        existing_user.last_name = data.get('last_name', existing_user.last_name)
        existing_user.email = data.get('email', existing_user.email)
        existing_user.mobile = data.get('mobile', existing_user.mobile)
        existing_user.gender = data.get('gender', existing_user.gender)

        db.session.commit()

        return jsonify({"message": "Profile updated successfully"}), 200
    else:
        return jsonify({"error": "User not found"}), 404


@app.route('/forgot_password', methods=['POST'])
@csrf.exempt
def forgot_password():
    data = request.json
    username = data.get('username')

    user = User.query.filter_by(username=username).first()

    if user:
        reset_token = secrets.token_urlsafe(32)

        new_reset_token = ResetToken(user_username=user.username, token=reset_token)
        db.session.add(new_reset_token)
        db.session.commit()

        subject = 'Password Reset Instructions'
        body = f'Your reset token is:   {reset_token}'
        send_otp_email(user.email, subject, body, otp=None)

        return jsonify({"message": "Password reset instructions sent"}), 200
    else:
        return jsonify({"error": "User not found"}), 404


@app.route('/reset_password', methods=['PUT'])
@csrf.exempt
def reset_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('new_password')

    reset_token = ResetToken.query.filter_by(token=token).first()

    if reset_token:
        user = User.query.filter_by(username=reset_token.user_username).first()

        if user:
            user.password = new_password

            db.session.delete(reset_token)
            db.session.commit()

            return jsonify({"message": "Password reset successful"}), 200
        else:
            return jsonify({"error": "User not found"}), 404
    else:
        return jsonify({"error": "Invalid or expired reset token"}), 400


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True, port=80)