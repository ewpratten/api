from flask import Flask, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://17bc1fc34ba34bbd87952489ec351441@o398481.ingest.sentry.io/5352486",
    integrations=[FlaskIntegration()]
)

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    return jsonify({
        "success": True,
        "message":"welcome"
    })

if __name__ == "__main__":

    # Locally run the app
    app.run()