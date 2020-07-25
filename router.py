# Welcome to the RetryLife API router script!
# You may be thinking, "why is this so big?"
# The API is hosted as a set serverless functions,
# and It costs too much to break this script up
#
# Have fun! ;)

# All needed imports
import os
import hashlib
import random
import requests
import tvdsb_student
import base64
import pickle
import flask
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Set up flask
sentry_sdk.init(
    dsn="https://17bc1fc34ba34bbd87952489ec351441@o398481.ingest.sentry.io/5352486",
    integrations=[FlaskIntegration()]
)
app = flask.Flask(__name__)

### Crash Tracking & Analytics ###

# Fingerprinting

def getBrowserFingerprint() -> str:
    return hashlib.md5(flask.request.headers.get('User-Agent').encode()).hexdigest()

# Load the GA tracking ID
GA_TRACKING_ID = os.environ.get("GA_TRACKING_ID", "NO-GA-ID")
print(f"Loaded GA token: {GA_TRACKING_ID}")

# Google analytics namespace

def ga_generateRandomUID() -> str:
    """Generate a random UID string for a tracking identifier

    Returns:
        str: Random tracking UID
    """
    return hashlib.md5(str(random.random()).encode()).hexdigest()


def ga_trackPath(url, uid=ga_generateRandomUID()):
    data = {
        'v': '1',  # API Version.
        'tid': GA_TRACKING_ID,  # Tracking ID / Property ID.
        # Anonymous Client Identifier. Ideally, this should be a UUID that
        # is associated with particular user, device, or browser instance.
        'cid': uid,
        't': "pageview",
        'dp': url
    }

    # Call the collection system
    ga_mkGACollectionRequest(data)
    
    
def ga_trackEvent(category, action, uid=ga_generateRandomUID()):
    data = {
        'v': '1',  # API Version.
        'tid': GA_TRACKING_ID,  # Tracking ID / Property ID.
        # Anonymous Client Identifier. Ideally, this should be a UUID that
        # is associated with particular user, device, or browser instance.
        'cid': uid,
        't': 'event',  # Event hit type.
        'ec': category,  # Event category.
        'ea': action,  # Event action.
        'el': None,  # Event label.
        'ev': 0,  # Event value, must be an integer
        # 'ua': 'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14'
    }

    # Call the collection system
    ga_mkGACollectionRequest(data)



def ga_mkGACollectionRequest(data: dict):
    requests.post(
        'https://www.google-analytics.com/collect', data=data)

def trackAPICall(url, uid=ga_generateRandomUID()):

    # Make a log entry
    print(f"A request has been made to {url} with a UID of {uid}")

    # Call event tracker
    ga_trackEvent(
        "APICall",
        url,
        uid
    )

    # Call path tracker
    ga_trackPath(
        url,
        uid
    )

def trackError(url, error, uid=ga_generateRandomUID()):
    trackAPICall(f"{url}?internal_error={error}", uid=uid)



######################################## API Routes #####################################################

## Errors

@app.errorhandler(404)
def error404(e):

    # Track this event with GA
    trackAPICall(
        "/404"
    )

    return flask.jsonify({
        "success": False,
        "message": "not found",
        "error":str(e)
    }), 404

@app.errorhandler(500)
def error500(e):

    # Track this event with GA
    trackError(
        "/error",
        "500"
    )

    # Log the event in sentry
    sentry_sdk.capture_exception(e)

    return flask.jsonify({
        "success": False,
        "message":"an application error ocurred",
        "error":str(e)
    }), 500

## Index

@app.route("/", methods=["GET", "POST"])
def index():
    trackAPICall("/", uid=getBrowserFingerprint())
    return flask.jsonify({
        "success": True,
        "message":"welcome"
    })

## TVDSB

@app.route("/tvdsb/student/auth", methods=["POST"])
def auth():
    
    # Handle missing args
    if "username" not in flask.request.form:
        return flask.jsonify({
            "success": False,
            "message": "No username set"
        }),401
    if "password" not in flask.request.form:
        return flask.jsonify({
            "success": False,
            "message": "No password set"
        }),401

    # Get user and password
    user = flask.request.form["username"]
    password = flask.request.form["password"]

    # Get auth object
    creds = tvdsb_student.LoginCreds(user, password)

    # Inject a random number into the object for some padding
    creds.rand = random.randint(1000, 1000000)

    # Make a dummy request to ensure creds are valid
    try:
        records = tvdsb_student.getAttendanceRecords(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        trackError(
            "/tvdsb/student/auth",
            "InvalidAuth",
            uid=creds.username
        )
        return flask.jsonify({
            "success": False,
            "message": "Invalid auth"
        }),401

    # Log a success
    trackAPICall(
        "/tvdsb/student/auth",
        uid=creds.username
    )

    # Return the creds
    return flask.jsonify({
        "success": True,
        "token":base64.b64encode(pickle.dumps(creds)).decode()
    })
    
@app.route("/tvdsb/student/attendance", methods=["GET"])
def attendance():

    # Get token
    token = flask.request.args.get("token", default="")

    # Unpickle (and handle invalid token)
    try:
        creds = pickle.loads(base64.b64decode(token.encode()))
    except EOFError as e:
        return flask.jsonify({
            "success": False,
            "message": "Invalid token format, or no token specified"
        }),401

    # Get attendance
    try:
        records = tvdsb_student.getAttendanceRecords(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        trackError(
            "/tvdsb/student/attendance",
            "InvalidAuth",
            uid=creds.username
        )
        return flask.jsonify({
            "success": False,
            "message": "Invalid auth"
        }),401

    # Log a success
    trackAPICall(
        "/tvdsb/student/attendance",
        uid=creds.username
    )

    return flask.jsonify({
        "success": True,
        "records":records
    })

@app.route("/tvdsb/student/marks", methods=["GET"])
def marks():

    # Get token
    token = flask.request.args.get("token", default="")

    # Unpickle (and handle invalid token)
    try:
        creds = pickle.loads(base64.b64decode(token.encode()))
    except EOFError as e:
        return flask.jsonify({
            "success": False,
            "message": "Invalid token format, or no token specified"
        }),401

    # Get marks
    try:
        records = tvdsb_student.getMarkHistory(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        trackError(
            "/tvdsb/student/marks",
            "InvalidAuth",
            uid=creds.username
        )
        return flask.jsonify({
            "success": False,
            "message": "Invalid auth"
        }),401

    # Log a success
    trackAPICall(
        "/tvdsb/student/marks",
        uid=creds.username
    )

    return flask.jsonify({
        "success": True,
        "marks":records
    })
    
@app.route("/tvdsb/student/payment", methods=["GET"])
def payment():

    # Get token
    token = flask.request.args.get("token", default="")

    # Unpickle (and handle invalid token)
    try:
        creds = pickle.loads(base64.b64decode(token.encode()))
    except EOFError as e:
        return flask.jsonify({
            "success": False,
            "message": "Invalid token format, or no token specified"
        }),401

    # Get payment
    try:
        records = tvdsb_student.getPaymentInfo(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        trackError(
            "/tvdsb/student/payment",
            "InvalidAuth",
            uid=creds.username
        )
        return flask.jsonify({
            "success": False,
            "message": "Invalid auth"
        }),401

    # Log a success
    trackAPICall(
        "/tvdsb/student/payment",
        uid=creds.username
    )

    return flask.jsonify({
        "success": True,
        "info":records
    })

@app.route("/tvdsb/student/timetable", methods=["GET"])
def timetable():

    # Get token
    token = flask.request.args.get("token", default="")

    # Unpickle (and handle invalid token)
    try:
        creds = pickle.loads(base64.b64decode(token.encode()))
    except EOFError as e:
        return flask.jsonify({
            "success": False,
            "message": "Invalid token format, or no token specified"
        }),401

    # Get timetable
    try:
        records = tvdsb_student.getTimetable(creds)
    except tvdsb_student.auth.InvalidAuth as e:
        trackError(
            "/tvdsb/student/timetable",
            "InvalidAuth",
            uid=creds.username
        )
        return flask.jsonify({
            "success": False,
            "message": "Invalid auth"
        }),401

    # Log a success
    trackAPICall(
        "/tvdsb/student/timetable",
        uid=creds.username
    )

    return flask.jsonify({
        "success": True,
        "timetable":records
    })

## raider robotics

@app.route("/frc/5024/lib5k/version")
def lib5kVersion():

    # Read from the API
    data = requests.get("https://api.github.com/repos/frc5024/lib5k/releases/latest").json()

    # Get the metadata
    tag_name = data["tag_name"]
    publish_date = data["published_at"]
    changelog = data["body"]

    # Track this request
    trackAPICall(
        "/frc/5024/lib5k/version",
        uid= getBrowserFingerprint()
    )

    # Give back data
    return flask.jsonify({
        "success": True,
        "version": tag_name,
        "date": publish_date,
        "changelog": changelog
    }), 200

@app.route("/tracking/external/<path>")
def trackExternal(path):

    print(f"An external service made a tracking request with path: {path}")

    # Track this request
    trackAPICall(
        f"/tracking/external/{path}",
        uid= getBrowserFingerprint()
    )

    return flask.jsonify(
        {
            "success": True,
            "message": "Logged event"
        }
    ), 200


# endroutes

# Create a little runner for starting Flask locally
if __name__ == "__main__":
    app.run()