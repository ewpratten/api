from ..flask import *
from ..util.gatracking import trackEvent
from ..util.crashreporting import sentry_sdk

@app.errorhandler(404)
def error404(e):

    # Track this event with GA
    trackEvent(
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

    # Track this event with GA
    trackEvent(
        "Error",
        "500"
    )

    # Log the event in sentry
    sentry_sdk.capture_exception(e)

    return jsonify({
        "success": False,
        "message":"an application error ocurred",
        "error":str(e)
    }), 500