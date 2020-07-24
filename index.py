from flask import Flask, jsonify

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


app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    track_event(
        "APICall",
        "Index"
    )
    return jsonify({
        "success": True,
        "message":"welcome"
    })

@app.errorhandler(404)
def error404(e):
    track_event(
        "Error",
        "404"
    )
    return jsonify({
        "success": False,
        "message": "not found",
        "error":str(e)
    }), 404

@app.errorhandler(500)
def error500(e):
    track_event(
        "Error",
        "500"
    )
    return jsonify({
        "success": False,
        "message":"an application error ocurred",
        "error":str(e)
    }), 500

if __name__ == "__main__":

    # Locally run the app
    app.run()