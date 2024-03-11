from flask import Flask, request, jsonify
import json
import ssl
from pymongo import MongoClient

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient('mongodb+srv://jeetj:9FFVZMC6eU1qrson@jeetdb.trviwgp.mongodb.net/', ssl_cert_reqs=ssl.CERT_NONE)
db = client['company']
collection = db['Empinfo']

@app.route('/show_data', methods=['GET'])
def show_data():
    try:
        # Retrieve data from MongoDB
        existing_data = list(collection.find({}, {'_id': 0}))

        if not existing_data:
            return jsonify({"message": "No data found"}), 404

        return jsonify(existing_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/store_data', methods=['POST'])
def store_data():
    try:
        data = request.get_json()

        # Assuming data includes 'firstName', 'lastName', 'phoneNumber', and 'email'
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        mobile = data.get('phoneNumber')
        email = data.get('email')

        # Store data in MongoDB
        job_data = {
            "firstName": first_name,
            "lastName": last_name,
            "phoneNumber": mobile,
            "email": email
        }
        collection.insert_one(job_data)

        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=70)
