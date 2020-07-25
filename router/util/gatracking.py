import requests
import random
import hashlib
import os

# Load the GA tracker
GA_TRACKING_ID = os.environ.get("GA_TRACKING_ID", "NO-GA-ID")

def generateRandomUID() -> str:
    """Generate a random UID string for a tracking identifier

    Returns:
        str: Random tracking UID
    """
    return hashlib.md5(str(random.random()).encode()).hexdigest()

def trackPath(url, uid=generateRandomUID()):
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
    _mkGACollectionRequest(data)
    


def trackEvent(category, action, uid=generateRandomUID()):
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
    _mkGACollectionRequest(data)


def _mkGACollectionRequest(data: dict):
    requests.post(
        'https://www.google-analytics.com/collect', data=data)