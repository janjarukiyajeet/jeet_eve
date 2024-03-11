from flask import Flask, request, jsonify
import json

app = Flask(__name__)


@app.route('/show_data', methods=['get'])
def show_data():
    try:
        with open('job_apply.json', 'r') as file:
            existing_data = json.load(file)

        return jsonify(existing_data), 200

    except FileNotFoundError:
        return jsonify({"message": "No data found"}), 404


@app.route('/store_data', methods=['POST'])
def store_data():
    data = request.get_json()

    # Assuming data includes 'first_name', 'last_name', 'mobile', and 'email'
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    mobile = data.get('phoneNumber')
    email = data.get('email')

    # Read existing data from job_apply.json
    try:
        with open('job_apply.json', 'r') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = []

    # Check if existing_data is a list or a dictionary
    if isinstance(existing_data, list):
        # Append the new data to the list
        job_data = {
            "firstName": first_name,
            "lastName": last_name,
            "phoneNumber": mobile,
            "email": email
        }
        existing_data.append(job_data)
    else:
        # Create a new list with the existing data and the new data
        existing_data = [
            existing_data,
            {
                "firstName": first_name,
                "lastName": last_name,
                "phoneNumber": mobile,
                "email": email
            }
        ]

    # Write the updated data back to job_apply.json
    with open('job_apply.json', 'w') as file:
        json.dump(existing_data, file, indent=2)

    return jsonify({"message": "Data stored successfully"}), 200


if __name__ == '__main__':
    app.run(debug=True)
