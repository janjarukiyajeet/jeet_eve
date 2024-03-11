import json
import os
import ssl

import razorpay
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient('mongodb+srv://jeetj:9FFVZMC6eU1qrson@jeetdb.trviwgp.mongodb.net/', ssl_cert_reqs=ssl.CERT_NONE)
db = client.jeet  # Your database name

data_file_path = 'data.json'

# Initialize waiting_list as an empty list
waiting_list = []

# Check if the file exists and is not empty
if os.path.exists(data_file_path) and os.path.getsize(data_file_path) > 0:
    # Load existing data from the JSON file
    with open(data_file_path, 'r') as json_file:
        loaded_data = json.load(json_file)

        # Ensure the loaded data is a list
        if isinstance(loaded_data, list):
            waiting_list = loaded_data

@app.route('/test/count', methods=['GET'])
def get_waiting_list():
    return jsonify({'count': len(waiting_list)})

@app.route('/test', methods=['POST'])
def add_to_waiting_list():
    data = request.get_json()

    if 'Email' not in data:
        return jsonify({'error': 'Invalid data format'}), 400

    waiting_list.append({
        'Email': data['Email'],
        # 'paymentId': data['paymentId']
    })

    # Save the updated data back to the JSON file
    with open(data_file_path, 'w') as json_file:
        json.dump(waiting_list, json_file, indent=2)

    # Insert data into MongoDB
    db.admin.insert_one({'Email': data['Email']})

    return jsonify({})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=100)
