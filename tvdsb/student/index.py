from flask import Flask, jsonify, request
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://17bc1fc34ba34bbd87952489ec351441@o398481.ingest.sentry.io/5352486",
    integrations=[FlaskIntegration()]
)

import pickle
import tvdsb_student
from base64 import b64encode, b64decode
app = Flask(__name__)

@app.route("/tvdsb/student/auth", methods=["POST"])
def auth():
    
    # Handle missing args
    if "username" not in request.form:
        return jsonify({
            "success": False,
            "message": "No username set"
        })
    if "password" not in request.form:
        return jsonify({
            "success": False,
            "message": "No password set"
        })

    # Get user and password
    user = request.form["username"]
    password = request.form["password"]

    # Get auth object
    creds = tvdsb_student.LoginCreds(user, password)

    # Make a dummy request to ensure creds are valid
    try:
        records = tvdsb_student.getAttendanceRecords(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        return jsonify({
            "success": False,
            "message": "Invalid auth"
        })

    # Return the creds
    return jsonify({
        "success": True,
        "token":b64encode(pickle.dumps(creds)).decode()
    })
    
@app.route("/tvdsb/student/attendance", methods=["GET"])
def attendance():

    # Get token
    token = request.args.get("token", default="")

    # Unpickle (and handle invalid token)
    try:
        creds = pickle.loads(b64decode(token.encode()))
    except EOFError as e:
        return jsonify({
            "success": False,
            "message": "Invalid token format, or no token specified"
        })

    # Get attendance
    try:
        records = tvdsb_student.getAttendanceRecords(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        return jsonify({
            "success": False,
            "message": "Invalid auth"
        })

    return jsonify({
        "success": True,
        "records":records
    })

@app.route("/tvdsb/student/marks", methods=["GET"])
def marks():

    # Get token
    token = request.args.get("token", default="")

    # Unpickle (and handle invalid token)
    try:
        creds = pickle.loads(b64decode(token.encode()))
    except EOFError as e:
        return jsonify({
            "success": False,
            "message": "Invalid token format, or no token specified"
        })

    # Get marks
    try:
        records = tvdsb_student.getMarkHistory(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        return jsonify({
            "success": False,
            "message": "Invalid auth"
        })

    return jsonify({
        "success": True,
        "marks":records
    })
    
@app.route("/tvdsb/student/payment", methods=["GET"])
def payment():

    # Get token
    token = request.args.get("token", default="")

    # Unpickle (and handle invalid token)
    try:
        creds = pickle.loads(b64decode(token.encode()))
    except EOFError as e:
        return jsonify({
            "success": False,
            "message": "Invalid token format, or no token specified"
        })

    # Get payment
    try:
        records = tvdsb_student.getPaymentInfo(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        return jsonify({
            "success": False,
            "message": "Invalid auth"
        })

    return jsonify({
        "success": True,
        "info":records
    })

@app.route("/tvdsb/student/timetable", methods=["GET"])
def timetable():

    # Get token
    token = request.args.get("token", default="")

    # Unpickle (and handle invalid token)
    try:
        creds = pickle.loads(b64decode(token.encode()))
    except EOFError as e:
        return jsonify({
            "success": False,
            "message": "Invalid token format, or no token specified"
        })

    # Get timetable
    try:
        records = tvdsb_student.getTimetable(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        return jsonify({
            "success": False,
            "message": "Invalid auth"
        })

    return jsonify({
        "success": True,
        "timetable":records
    })

if __name__ == "__main__":

    # Locally run the app
    app.run()