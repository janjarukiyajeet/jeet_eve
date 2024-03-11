import secrets
import ssl

from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
import random
import smtplib
from email.mime.text import MIMEText
from flask_wtf.csrf import generate_csrf, CSRFProtect
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from pymongo import MongoClient

from mongo_conn import client

app = Flask(__name__)
CORS(app)

client = MongoClient('mongodb+srv://jeetj:9FFVZMC6eU1qrson@jeetdb.trviwgp.mongodb.net/', ssl_cert_reqs=ssl.CERT_NONE)
db = client['company']


app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['JWT_SECRET_KEY'] = 'dc6f8cf55952d4550b2a54a1a79b6398'

csrf = CSRFProtect(app)

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


def send_welcome_email(receiver_email, username):
    subject = 'Welcome to User Profile Management'
    body = f'Hello {username},\n\nThank you for registering with User Profile Management. We are excited to have you on board!'
    send_otp_email(receiver_email, subject, body, otp=None)


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
        existing_user = db.users.find_one({'username': username})

        if existing_user:
            return jsonify({"error": "Username already exists"}), 400

        new_user = {
            'username': username,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'mobile': mobile,
            'gender': gender,
            'otp': None
        }

        db.users.insert_one(new_user)

        send_welcome_email(email, username)


        csrf_token = generate_csrf()

        response = jsonify({"message": "Signup successful"})
        response.headers["X-CSRF-TOKEN"] = csrf_token
        return response, 200

    else:
        return jsonify({"error": "Username, password, email, mobile and gender are required"}), 400


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



@app.route('/reset_password', methods=['PUT'])
@csrf.exempt
def reset_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('new_password')

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
