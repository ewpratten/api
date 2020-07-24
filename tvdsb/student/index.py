from flask import Flask, jsonify, request

## Sentry Tracking ##
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://17bc1fc34ba34bbd87952489ec351441@o398481.ingest.sentry.io/5352486",
    integrations=[FlaskIntegration()]
)

## Google analytics ##
import requests
import random
import hashlib
GA_TRACKING_ID = "UA-74118570-5"

def track_event(category, action, uid=hashlib.md5(str(random.random()).encode()).hexdigest(), label=None, value=0):
    data = {
        'v': '1',  # API Version.
        'tid': GA_TRACKING_ID,  # Tracking ID / Property ID.
        # Anonymous Client Identifier. Ideally, this should be a UUID that
        # is associated with particular user, device, or browser instance.
        'cid': '555',
        't': 'event',  # Event hit type.
        'ec': category,  # Event category.
        'ea': action,  # Event action.
        'el': label,  # Event label.
        'ev': value,  # Event value, must be an integer
        'ua': 'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14'
    }

    response = requests.post(
        'https://www.google-analytics.com/collect', data=data)

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
        }),401
    if "password" not in request.form:
        return jsonify({
            "success": False,
            "message": "No password set"
        }),401

    # Get user and password
    user = request.form["username"]
    password = request.form["password"]

    # Get auth object
    creds = tvdsb_student.LoginCreds(user, password)

    # Inject a random number into the object for some padding
    creds.rand = random.randint(1000, 1000000)

    # Make a dummy request to ensure creds are valid
    try:
        records = tvdsb_student.getAttendanceRecords(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        track_event(
            "APICall.tvdsb_student",
            "InvalidAuth",
            uid=creds.username
        )
        return jsonify({
            "success": False,
            "message": "Invalid auth"
        }),401

    # Log a success
    track_event(
        "APICall.tvdsb_student",
        "GotAuthToken",
        uid=creds.username
    )

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
        }),401

    # Get attendance
    try:
        records = tvdsb_student.getAttendanceRecords(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        track_event(
            "APICall.tvdsb_student",
            "InvalidAuth",
            uid=creds.username
        )
        return jsonify({
            "success": False,
            "message": "Invalid auth"
        }),401

    # Log a success
    track_event(
        "APICall.tvdsb_student",
        "GotAttendance",
        uid=creds.username
    )

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
        }),401

    # Get marks
    try:
        records = tvdsb_student.getMarkHistory(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        track_event(
            "APICall.tvdsb_student",
            "InvalidAuth",
            uid=creds.username
        )
        return jsonify({
            "success": False,
            "message": "Invalid auth"
        }),401

    # Log a success
    track_event(
        "APICall.tvdsb_student",
        "GotMarkHistory",
        uid=creds.username
    )

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
        }),401

    # Get payment
    try:
        records = tvdsb_student.getPaymentInfo(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        track_event(
            "APICall.tvdsb_student",
            "InvalidAuth",
            uid=creds.username
        )
        return jsonify({
            "success": False,
            "message": "Invalid auth"
        }),401

    # Log a success
    track_event(
        "APICall.tvdsb_student",
        "GotPaymentInfo",
        uid=creds.username
    )

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
        }),401

    # Get timetable
    try:
        records = tvdsb_student.getTimetable(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        track_event(
            "APICall.tvdsb_student",
            "InvalidAuth",
            uid=creds.username
        )
        return jsonify({
            "success": False,
            "message": "Invalid auth"
        }),401

    # Log a success
    track_event(
        "APICall.tvdsb_student",
        "GotTimeTable",
        uid=creds.username
    )

    return jsonify({
        "success": True,
        "timetable":records
    })

if __name__ == "__main__":

    # Locally run the app
    app.run()