# Import flask runner
from .flask import *

# Import all routes
from .routes import *

# Handle running locally
if __name__ == "__main__":
    app.run()