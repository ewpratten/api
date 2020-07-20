from flask import Flask, jsonify
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