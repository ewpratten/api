from ..flask import *
from ..util import trackAPICall
from ..util.fingerprint import getBrowserFingerprint

@app.route("/", methods=["GET", "POST"])
def index():
    trackAPICall("/", uid=getBrowserFingerprint())
    return jsonify({
        "success": True,
        "message":"welcome"
    })