from .gatracking import trackEvent, trackPath, generateRandomUID


def trackAPICall(url, uid=generateRandomUID()):

    # Make a log entry
    print(f"A request has been made to {url} with a UID of {uid}")

    # Call event tracker
    trackEvent(
        "APICall",
        url,
        uid
    )

    # Call path tracker
    trackEvent(
        url,
        uid
    )