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

app = Flask(__name__)

if __name__ == "__main__":
    app.run()

## App ##

@app.route("/frc/5024/lib5k/version")
def lib5kVersion():

    # Read from the API
    data = requests.open("https://api.github.com/repos/frc5024/lib5k/releases/latest").json()

    # Get the metadata
    tag_name = data["tag_name"]
    publish_date = data["published_at"]
    changelog = data["body"]

    # Track this request
    track_event(
        "APICall.frc.5024",
        "lib5k_version"
    )

    # Give back data
    return jsonify({
        "success": True,
        "version": tag_name,
        "date": publish_date,
        "changelog": changelog
    }), 200