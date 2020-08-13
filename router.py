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
import feedparser

# Set up flask
sentry_sdk.init(
    dsn="https://17bc1fc34ba34bbd87952489ec351441@o398481.ingest.sentry.io/5352486",
    integrations=[FlaskIntegration()]
)
app = flask.Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# List of endpoints to check for the status page. As long as
# one of the endpoints in a list is good, the status will be OK
statuspage_endpoints = {
    "retrylife.ca": {
        "description":"The retrylife.ca homepage",
        "check_code": {
            "urls": ["https://retrylife.ca", "http://retrylife.ca"],
            "status_code":200
        }
    },
    "RetryLife API": {
        "description":"The RetryLife API's production deployment",
        "check_code": {
            "urls": ["https://api.retrylife.ca"],
            "status_code":200
        }
    },
    "RetryLife Development API": {
        "description":"The RetryLife API's development deployment",
        "check_code": {
            "urls": ["https://beta.api.retrylife.ca"],
            "status_code":200
        }
    },
    "RetryLife API Global Infrastructure": {
        "description":"The distributed backend infrastructure that hosts the RetryLife API",
        "check_json_equal": {
            "url": "https://www.vercel-status.com/api/v2/status.json",
            "key":"status.description",
            "value": "All Systems Operational"
        }
    },
    "RetryLife API Backend Logging": {
        "description":"The error logging service that keeps track of RetryLife API errors and events",
        "check_json_equal": {
            "url": "https://status.datadoghq.com/api/v2/status.json",
            "key":"status.description",
            "value": "All Systems Operational"
        }
    },
    "RetryLife API Crash Tracking": {
        "description":"The crash tracker for the RetryLife API, and some of Evan's apps",
        "check_json_equal": {
            "url": "https://status.sentry.io/api/v2/status.json",
            "key":"status.description",
            "value": "All Systems Operational"
        }
    },
    "RetryLife Services Backend": {
        "description":"The docker swarm master and main compute host powering the backend of most RetryLife services",
        "check_code": {
            "urls": [
                "http://thisdoesnotexist.retrylife.ca"
                # "https://admin.rtlroute.cc"
                ],
            "status_code":200
        }
    },
    "RetryLife DNS Frontend": {
        "description":"The admin panel for RetryLife DNS",
        "check_code": {
            "urls": ["http://s2.retrylife.ca/admin/"],
            "status_code":200
        }
    },
    "RetryLife DNS Backend": {
        "description":"The RetryLife DNS server",
        "check_json_equal": {
            "url": "http://s2.retrylife.ca/admin/api.php",
            "key": "status",
            "value": "enabled"
        }
    },
    "remains.xyz": {
        "description":"The remains.xyz gameservers",
        "check_code": {
            "urls": [
                "http://thisdoesnotexist.retrylife.ca"
                # "https://remains.xyz"
                ],
            "status_code":200
        }
    },
    "Unofficial Student Portal": {
        "description":"My TVDSB Student Portal frontend service",
        "check_code": {
            "urls": ["https://studentportal.retrylife.ca/"],
            "status_code":200
        }
    },
    "RetryLife Maven": {
        "description":"The RetryLife maven server",
        "check_code": {
            "urls": [
                "http://thisdoesnotexist.retrylife.ca"
                # "https://mvn.retrylife.ca/"
            ],
            "status_code":200
        }
    },
    "cs.5024.ca": {
        "description":"The Raider Robotics software development team's primary web server",
        "check_code": {
            "urls": ["https://cs.5024.ca"],
            "status_code":200
        }
    },
    "frc5024.github.io":{
        "description":"The Raider Robotics software development team's fallback web server",
        "check_code": {
            "urls": ["https://frc5024.github.io"],
            "status_code":200
        }
    },
    "5024 Webdocs": {
        "description":"The Raider Robotics software development team's documentation website",
        "check_code": {
            "urls": ["https://cs.5024.ca/webdocs", "https://frc5024.github.io/webdocs"],
            "status_code":200
        }
    },
    "Snapcode Backend": {
        "description":"The Snapchat deeplink server that handles snapcode generation",
        "check_code": {
            "urls": ["https://app.snapchat.com/web/deeplink/snapcode?username=testuser&type=PNG"],
            "status_code":200
        }
    },
    "TheBlueAlliance Backend": {
        "description":"TheBlueAlliance's backend server",
        "check_code": {
            "urls": ["https://www.thebluealliance.com/api/v3/status"],
            "status_code":401
        }
    },
    "FRC Field Management Database": {
        "description":"The primary API server for connecting to FRC game databases",
        "check_json_equal": {
            "url": "https://frc-api.firstinspires.org/v2.0/",
            "key":"status",
            "value": "normal"
        }
    },
}


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
        'dp': url,
        'ua': 'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14'
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
        'ua': 'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14'
    }

    # Call the collection system
    ga_mkGACollectionRequest(data)



def ga_mkGACollectionRequest(data: dict):
    try:
        requests.post(
            'https://www.google-analytics.com/collect', data=data)
    except requests.exceptions.ConnectionError as e:
        print("Failed to make tracking request")


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

## Add headers to all requests
@app.after_request
def allRequests(response):
    if __name__ == "__main__":
        print("Injecting localhost CORS headers")
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "authorization"
    return response

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

## Static files

@app.route('/apidocs')
def staticAPIDocsIndex():
    return flask.send_from_directory('apidocs', "index.html")

@app.route('/apidocs/<path:path>')
def staticAPIDocs(path):
    return flask.send_from_directory('apidocs', path)

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
        }), 401
    except IndexError as e:
        trackError(
            "/tvdsb/student/auth",
            "FailedToParse",
            uid=creds.username
        )
        sentry_sdk.capture_exception(e)
        return flask.jsonify({
            "success": False,
            "message": "TVDSB API responded with an unsupported response"
        }), 500


    # Log a success
    trackAPICall(
        "/tvdsb/student/auth",
        uid=creds.username
    )

    # Return the creds
    return flask.jsonify({
        "success": True,
        "token":base64.b64encode(f"{creds.username}:{creds.password}".encode()).decode()
    })
    
@app.route("/tvdsb/student/attendance", methods=["GET"])
def attendance():

    # Get token
    token = flask.request.args.get("token", default="")

    if token:
        # Unpickle (and handle invalid token)
        try:
            creds = pickle.loads(base64.b64decode(token.encode()))
        except EOFError as e:
            return flask.jsonify({
                "success": False,
                "message": "Invalid token format, or no token specified"
            }), 401
    
    # Handle auth header
    if flask.request.authorization:
        creds = tvdsb_student.LoginCreds(flask.request.authorization.username, flask.request.authorization.password)
    else:
        return flask.jsonify({
                "success": False,
                "message": "Authorization header not set"
            }), 401

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
        }), 401
    except IndexError as e:
        trackError(
            "/tvdsb/student/attendance",
            "FailedToParse",
            uid=creds.username
        )
        sentry_sdk.capture_exception(e)
        return flask.jsonify({
            "success": False,
            "message": "TVDSB API responded with an unsupported response"
        }), 500

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

    if token:
        # Unpickle (and handle invalid token)
        try:
            creds = pickle.loads(base64.b64decode(token.encode()))
        except EOFError as e:
            return flask.jsonify({
                "success": False,
                "message": "Invalid token format, or no token specified"
            }), 401
    
    # Handle auth header
    if flask.request.authorization:
        creds = tvdsb_student.LoginCreds(flask.request.authorization.username, flask.request.authorization.password)
    else:
        return flask.jsonify({
                "success": False,
                "message": "Authorization header not set"
            }), 401

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
        }), 401
    except IndexError as e:
        trackError(
            "/tvdsb/student/marks",
            "FailedToParse",
            uid=creds.username
        )
        sentry_sdk.capture_exception(e)
        return flask.jsonify({
            "success": False,
            "message": "TVDSB API responded with an unsupported response"
        }), 500

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

    if token:
        # Unpickle (and handle invalid token)
        try:
            creds = pickle.loads(base64.b64decode(token.encode()))
        except EOFError as e:
            return flask.jsonify({
                "success": False,
                "message": "Invalid token format, or no token specified"
            }), 401
    
    # Handle auth header
    if flask.request.authorization:
        creds = tvdsb_student.LoginCreds(flask.request.authorization.username, flask.request.authorization.password)
    else:
        return flask.jsonify({
                "success": False,
                "message": "Authorization header not set"
            }), 401

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
        }), 401
    except IndexError as e:
        trackError(
            "/tvdsb/student/payment",
            "FailedToParse",
            uid=creds.username
        )
        sentry_sdk.capture_exception(e)
        return flask.jsonify({
            "success": False,
            "message": "TVDSB API responded with an unsupported response"
        }), 500

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

    if token:
        # Unpickle (and handle invalid token)
        try:
            creds = pickle.loads(base64.b64decode(token.encode()))
        except EOFError as e:
            return flask.jsonify({
                "success": False,
                "message": "Invalid token format, or no token specified"
            }), 401
    
    # Handle auth header
    if flask.request.authorization:
        creds = tvdsb_student.LoginCreds(flask.request.authorization.username, flask.request.authorization.password)
    else:
        return flask.jsonify({
                "success": False,
                "message": "Authorization header not set"
            }), 401

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
        }), 401
    except IndexError as e:
        trackError(
            "/tvdsb/student/timetable",
            "FailedToParse",
            uid=creds.username
        )
        sentry_sdk.capture_exception(e)
        return flask.jsonify({
            "success": False,
            "message": "TVDSB API responded with an unsupported response"
        }), 500

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

## External tracking

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

## Deviantart

@app.route("/deviantart/<user>/content")
def deviantartContent(user):

    # Get the browser fingerprint
    fingerprint = getBrowserFingerprint()

    # Track this request
    trackAPICall(
        f"/deviantart/{user}/content",
        uid=fingerprint
    )

    # Call the RSS API
    rss = feedparser.parse(f"https://backend.deviantart.com/rss.xml?type=deviation&q=by%3A{user}+sort%3Atime+meta%3Aall")

    # Handle non-existant user
    if rss["feed"]["subtitle"] == "Error generating RSS.":
        return flask.jsonify(
            {
                "success": False,
                "message": "User not found"
            }
        ), 404

    # Parse the RSS
    data = {
        "metadata":{},
        "content":[]
    }

    # Load in metadata
    data["metadata"]["username"] = user
    
    # Load all entries
    for entry in rss["entries"]:
        data["content"].append(
            {
                "url": entry["link"],
                "media": entry["media_content"],
                "nsfw": entry["media_rating"]["content"] != "nonadult",
                "title": entry["title"]
            }
        )

    # Respond
    return flask.jsonify(
        {
            "success": True,
            "data":data
        }
    ), 200

# Snapchat

@app.route("/snapchat/<user>/snapcode.png")
def getPNGSnapCode(user):

    # Get the browser fingerprint
    fingerprint = getBrowserFingerprint()

    # Track this request
    trackAPICall(
        f"/snapchat/{user}/snapcode.png",
        uid=fingerprint
    )

    # Make remote API call
    image = requests.get(f"https://app.snapchat.com/web/deeplink/snapcode?username={user}&type=PNG&size=240", stream = True)
    image.raw.decode_content = True

    response = flask.make_response(image.raw.data)
    response.headers.set('Content-Type', 'image/png')

    return response

@app.route("/snapchat/<user>/snapcode.svg")
def getSVGSnapCode(user):

    # Get the browser fingerprint
    fingerprint = getBrowserFingerprint()

    # Track this request
    trackAPICall(
        f"/snapchat/{user}/snapcode.svg",
        uid=fingerprint
    )

    # Make remote API call
    image = requests.get(f"https://app.snapchat.com/web/deeplink/snapcode?username={user}&type=SVG&size=240", stream = True)
    image.raw.decode_content = True

    response = flask.make_response(image.raw.data)
    response.headers.set('Content-Type', 'image/svg')

    return response

# Status

@app.route("/status")
def getStatus():

    # Get the browser fingerprint
    fingerprint = getBrowserFingerprint()

    # Track this request
    trackAPICall(
        f"/status",
        uid=fingerprint
    )

    # Possable messages
    STATUS_OK = "Operational"
    STATUS_FAIL = "Degraded or Down"

    # Build an output dict
    output = {}

    # Interate through every endpoint to check
    for endpoint in statuspage_endpoints:

        try:
            # Default to failure if no type
            output[endpoint] = {
                "ok":False,
                "message": STATUS_FAIL,
                "service_info": statuspage_endpoints[endpoint]["description"]
            }

            # Handle check type
            if "check_code" in statuspage_endpoints[endpoint]:

                # Get check data
                urls = statuspage_endpoints[endpoint]["check_code"]["urls"]
                code = statuspage_endpoints[endpoint]["check_code"]["status_code"]

                # Check every URL
                for url in urls:
                    if requests.get(url).status_code == code:
                        output[endpoint]["ok"] = True
                        output[endpoint]["message"] = STATUS_OK
                        break
                else:
                    output[endpoint]["ok"] = False
                    output[endpoint]["message"] = STATUS_FAIL
            elif "check_json_equal" in statuspage_endpoints[endpoint]:

                # Get data
                url = statuspage_endpoints[endpoint]["check_json_equal"]["url"]
                key = statuspage_endpoints[endpoint]["check_json_equal"]["key"]
                value = statuspage_endpoints[endpoint]["check_json_equal"]["value"]

                # Get response from remote
                data = requests.get(url)

                # Try to get JSON data
                try:
                    json = data.json()
                except:
                    output[endpoint]["ok"] = False
                    output[endpoint]["message"] = STATUS_FAIL
                
                # Recurse to get the value
                try:
                    remote_data = json
                    for subkey in key.split("."):
                        remote_data = remote_data[subkey]
                except KeyError as e:
                    output[endpoint]["ok"] = False
                    output[endpoint]["message"] = STATUS_FAIL
                    continue

                # Check equality
                if str(remote_data) == str(value):
                    output[endpoint]["ok"] = True
                    output[endpoint]["message"] = STATUS_OK
                else:
                    output[endpoint]["ok"] = False
                    output[endpoint]["message"] = STATUS_FAIL
        except requests.exceptions.ConnectionError as e:
            trackError(
                "/status",
                "FailedToResolve."+base64.b64encode("endpoint".encode()).decode(),
                uid=fingerprint
            )
            sentry_sdk.capture_exception(e)

    # Build a response
    response = flask.make_response(flask.jsonify(
        {
            "success": True,
            "services":output
        }
    ))

    # Enable Vercel caching, since this endpoint takes so long to load
    response.headers.set('Cache-Control', 's-maxage=1, stale-while-revalidate')

    # Return the status info
    return response

# James' activity tracking stuff
@app.route("/rsninja722/activity")
def rsNinjaActivity():

    # Get the browser fingerprint
    fingerprint = getBrowserFingerprint()

    # Track this request
    trackAPICall(
        f"/rsninja722/activity",
        uid=fingerprint
    )

    # Storage for data
    datapoints = []

    # Get his lookup table
    lut = requests.get("https://rsninja.dev/timeUse/definitions.csv").text

    # Convert to KVP data
    lut_kvp = {}
    for entry in lut.split("\n")[1:]:
        entry = entry.split(",")

        # Ignore empty lines
        if len(entry) < 2:
            continue

        # Set the kay and value
        lut_kvp[entry[0]] = entry[1]

    # Get his daily info
    day_info_raw = requests.get("https://rsninja.dev/timeUse/timeUse.csv").text.split("\n")[1:]

    # Iterate every day
    for day_data in day_info_raw:
        day_data = day_data.split(",")

        # Get date info
        year = day_data[0]
        month = day_data[1]
        day = day_data[2]

        # Get only his day, not his comment at the end
        day_data_points = day_data[3:][:48]

        # Build the day's datapoint
        output = {
            "date":f"{year}/{month}/{day}",
            "data":{

            },
            "comment":""
        }

        # Add his comment if it exists
        if len(day_data) >= 52:
            output["comment"] = day_data[51].strip()

        # Accumulate time data
        for point in day_data_points:
            
            # Add any new point
            if lut_kvp[point] not in output["data"]:
                output["data"][lut_kvp[point]] = 0.5
            else:
                output["data"][lut_kvp[point]] += 0.5

        # Add day's datapoint to the list 
        datapoints.append(output)


    # Build a response
    response = flask.make_response(flask.jsonify(
        {
            "success": True,
            "daily_data":datapoints
        }
    ))

    # Enable Vercel caching, since this endpoint takes so long to load
    response.headers.set('Cache-Control', 's-maxage=1, stale-while-revalidate')

    # Return the status info
    return response

## FRC Tools

def getFRCSeasonData():
    return requests.get("https://frc-api.firstinspires.org/v2.0/").json()

def getCSASupportedYears():

    # Get the supported years list
    year_list = requests.get("https://raw.githubusercontent.com/JamieSinn/CSA-USB-Tool/master/Years.txt").text.split("\n")

    # Create the output
    output = []
    for year in year_list:
        if "FRC" in year:
            output.append(year.strip("FRC"))

    output.sort()
    return output
    

@app.route("/frc/year")
def getFRCYear():

    # Get the browser fingerprint
    fingerprint = getBrowserFingerprint()

    # Track this request
    trackAPICall(
        f"/frc/year",
        uid=fingerprint
    )

    # Make a request to FMS API to get the FRC year
    season_data = getFRCSeasonData()

    # Return the data
    return flask.jsonify({
        "success":True,
        "year":season_data["currentSeason"]
    })

@app.route("/frc/password")
def getFRCSeasonPassword():

    # Get the browser fingerprint
    fingerprint = getBrowserFingerprint()

    # Track this request
    trackAPICall(
        f"/frc/year",
        uid=fingerprint
    )

    # Get the latest CSA year
    latest_year = getCSASupportedYears()[-1]

    # Get the latest password file
    password = requests.get(f"https://raw.githubusercontent.com/JamieSinn/CSA-USB-Tool/master/{latest_year}Password.txt").text.strip()

    # Return the data
    return flask.jsonify({
        "success":True,
        "year":int(latest_year),
        "password": password
    })

# endroutes

# Create a little runner for starting Flask locally
if __name__ == "__main__":
    app.run()