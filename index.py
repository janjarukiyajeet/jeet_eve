import secrets
import ssl
from email.mime.multipart import MIMEMultipart

import requests
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
import random
import smtplib
from email.mime.text import MIMEText
from flask_wtf.csrf import generate_csrf, CSRFProtect
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from pymongo import MongoClient



app = Flask(__name__)
CORS(app)

client = MongoClient('mongodb+srv://jeetj:9FFVZMC6eU1qrson@jeetdb.trviwgp.mongodb.net/', tlsAllowInvalidCertificates=True)
db = client['info']


app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['JWT_SECRET_KEY'] = 'dc6f8cf55952d4550b2a54a1a79b6398'

csrf = CSRFProtect(app)

def send_otp_email(receiver_email, subject, body, otp):
    # Zoho Mail SMTP Configuration
    smtp_server = 'smtppro.zoho.in'
    smtp_port = 587
    smtp_username = 'jeet.j@buone.in'
    smtp_password = 'atEFF0UMQ4mx'

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()

    server.login(smtp_username, smtp_password)

    server.sendmail(smtp_username, receiver_email, msg.as_string())

    server.quit()

def generate_reset_token(username):
    reset_token = secrets.token_urlsafe(32)
    db.reset_tokens.insert_one({'user_username': username, 'token': reset_token})
    return reset_token


def send_reset_email(receiver_email, reset_token):
    subject = 'Password Reset Instructions'
    body = f'Click the following link to reset your password: http://your-reset-url/    {reset_token}'
    send_otp_email(receiver_email, subject, body, otp=None)


@app.route('/signup', methods=['POST'])
@csrf.exempt
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    mobile = data.get('mobile')
    email = data.get('email')
    gender = data.get('gender')

    if password != confirm_password:
        return jsonify({"error": "Password and confirm password do not match"}), 400


    if username and password and first_name and last_name and email and mobile and gender:
        existing_user = db.users.find_one({'username': username})

        if existing_user:
            return jsonify({"error": "Username already exists"}), 400

        new_user = {
            'username': username,
            'password': password,
            'confirm_password': confirm_password,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'mobile': mobile,
            'gender': gender,
            'otp': None
        }

        db.users.insert_one(new_user)

        reset_token = generate_reset_token(username)

        email_data = {
            'to_email': email,
            'subject': 'Password Reset Instructions',
            'message': f'Click the following link to reset your password: http://your-reset-url/    {reset_token}'
        }
        #requests.post('http://localhost:5000/send_email', json=email_data)

        csrf_token = generate_csrf()

        response = jsonify({"message": "Signup successful"})
        response.headers["X-CSRF-TOKEN"] = csrf_token
        return response, 200

    else:
        return jsonify({"error": "Username, password, email, mobile, and gender are required"}), 400


@app.route('/login', methods=['POST'])
@csrf.exempt
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    existing_user = db.users.find_one({'username': username, 'password': password})

    if existing_user:
        otp = random.randint(1000, 9999)
        db.users.update_one({'username': username}, {'$set': {'otp': otp}})

        subject = 'Your OTP for User Profile Management'
        body = f'Your OTP is: {otp}'

        send_otp_email(existing_user['email'], subject, body, otp)

        return jsonify({"message": "Login successful. OTP generated and sent via email"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401


@app.route('/verify_otp', methods=['POST'])
@csrf.exempt
def verify_otp():
    data = request.json
    username = data.get('username')
    otp_attempt = data.get('otp')

    existing_user = db.users.find_one({'username': username, 'otp': int(otp_attempt)})

    if existing_user:
        db.users.update_one({'username': username}, {'$set': {'otp': None}})
        return jsonify({"message": "OTP verification successful"}), 200
    else:
        return jsonify({"error": "Invalid OTP"}), 401



@app.route('/get_profile/<username>', methods=['GET'])
@csrf.exempt
def get_profile(username):
    existing_user = db.users.find_one({'username': username})

    if existing_user:
        user_profile = {
            'username': existing_user['username'],
            'password': existing_user['password'],
            'first_name': existing_user['first_name'],
            'last_name': existing_user['last_name'],
            'email': existing_user['email'],
            'mobile': existing_user['mobile'],
            'gender': existing_user['gender']
        }
        return jsonify(user_profile), 200
    else:
        return jsonify({"error": "User not found"}), 404


@app.route('/update_profile/<username>', methods=['PUT'])
@csrf.exempt
def update_profile(username):
    data = request.json

    existing_user = db.users.find_one({'username': username})

    if existing_user:
        update_data = {
            'password': data.get('password', existing_user['password']),
            'first_name': data.get('first_name', existing_user['first_name']),
            'last_name': data.get('last_name', existing_user['last_name']),
            'email': data.get('email', existing_user['email']),
            'mobile': data.get('mobile', existing_user['mobile']),
            'gender': data.get('gender', existing_user['gender']),
        }

        db.users.update_one({'username': username}, {'$set': update_data})

        return jsonify({"message": "Profile updated successfully"}), 200
    else:
        return jsonify({"error": "User not found"}), 404



@app.route('/forgot_password', methods=['POST'])
@csrf.exempt
def forgot_password():
    data = request.json
    username = data.get('username')

    user = db.users.find_one({'username': username})

    if user:
        reset_token = secrets.token_urlsafe(32)

        new_reset_token = {
            'user_username': user['username'],
            'token': reset_token
        }

        db.reset_tokens.insert_one(new_reset_token)

        subject = 'Password Reset Instructions'
        body = f'Your reset token is:   {reset_token}'
        send_otp_email(user['email'], subject, body, otp=None)

        return jsonify({"message": "Password reset instructions sent"}), 200
    else:
        return jsonify({"error": "User not found"}), 404



@app.route('/reset_password', methods=['POST'])
@csrf.exempt
def reset_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('new_password')

    if not token:
        return jsonify({"error": "Reset token not provided"}), 400

    reset_token = db.reset_tokens.find_one({'token': token})

    if reset_token:
        user = db.users.find_one({'username': reset_token['user_username']})

        if user:
            db.users.update_one({'username': user['username']}, {'$set': {'password': new_password}})
            db.reset_tokens.delete_one({'token': token})

            return jsonify({"message": "Password reset successful"}), 200
        else:
            return jsonify({"error": "User not found"}), 404
    else:
        return jsonify({"error": "Invalid or expired reset token"}), 400


if __name__ == '__main__':
    app.run(debug=True, port=90)
