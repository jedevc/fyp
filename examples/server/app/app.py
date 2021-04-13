import argparse
import os
from secrets import compare_digest
from pathlib import Path

from flask import Flask, send_from_directory, abort, request

from .challenge import Challenge

app = Flask(__name__)


@app.route("/")
def index():
    return ""


FILE_WHITELIST = {
    "challenge",
}


@app.route("/challenges/<string:name>/<string:seed>/<path:filename>")
def challenge_file(name: str, seed: str, filename: str):
    if filename not in FILE_WHITELIST:
        secret = app.config["secret"]
        if not secret:
            pass
        elif compare_digest(request.headers.get("x-auth", ""), secret):
            pass
        else:
            return abort(404)

    try:
        path = app.config["challenges"] / (name + ".spec")
        chal = Challenge.create(path, seed)
    except FileNotFoundError:
        return abort(404)

    return send_from_directory(chal.output, filename)


def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    secret = os.environ.get("SECRET")

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=host)
    parser.add_argument("--port", default=port, type=int)
    parser.add_argument("--secret", default=secret)
    args = parser.parse_args()

    host, port = args.host, args.port

    app.config["challenges"] = Path(__file__).parent.parent / "challenges"
    app.config["secret"] = args.secret

    app.run(host=host, port=port)

