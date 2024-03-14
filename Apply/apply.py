from flask import Flask, request, jsonify
import json
from bson import json_util
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

client = MongoClient('mongodb+srv://jeetj:9FFVZMC6eU1qrson@jeetdb.trviwgp.mongodb.net/', tlsAllowInvalidCertificates=True)
db = client['jeet']
collection = db['apply_data']

@app.route('/show_data', methods=['GET'])
def show_data():
    try:
        data = list(collection.find())

        json_data = json_util.dumps(data)
        return json_data, 200, {'Content-Type': 'application/json'}

    except FileNotFoundError:
        return jsonify({"message": "No data found"}), 404


@app.route('/store_data', methods=['POST'])
def store_data():
    data = request.get_json()


    first_name = data.get('firstName')
    last_name = data.get('lastName')
    mobile = data.get('phoneNumber')
    email = data.get('email')
    job_title = data.get('jobTitle')
    gender = data.get('gender')


    job_data = {
        "firstName": first_name,
        "lastName": last_name,
        "phoneNumber": mobile,
        "email": email,
        "jobTitle": job_title,
        "gender": gender
    }
    collection.insert_one(job_data)

    return jsonify({"message": "Data stored successfully"}), 200


if __name__ == '__main__':
    app.run(debug=True)
