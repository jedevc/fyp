import argparse
import os
import datetime
import string
import random
import re
from secrets import compare_digest
from pathlib import Path

from flask import Flask, send_from_directory, abort, request, render_template, make_response, redirect

from .challenge import Challenge
from .database import Session

app = Flask(__name__, template_folder="../templates")

DEFAULT_EXPIRE = datetime.timedelta(days=14)


def validate_flag(flag: str) -> bool:
    match = re.match("FLAG{([^_]+)_([^_]+)}", request.form["flag"])
    if match:
        return match.group(1) == match.group(1)
    else:
        return False


@app.route("/", methods=["GET", "POST"])
def index():
    if "id" in request.cookies:
        seed = request.cookies["id"]
    else:
        seed = ''.join(random.choice(string.ascii_lowercase) for _ in range(16))

    flag_error = False

    if "flag" in request.cookies:
        flag = request.cookies["flag"]
    else:
        flag = ""
        if request.method == "POST":
            if validate_flag(request.form["flag"]):
                flag = request.form["flag"]
                resp = redirect("/survey", code=303)
                resp.set_cookie("flag", request.form["flag"], max_age=DEFAULT_EXPIRE)
                return resp
            else:
                flag_error = True

    resp = make_response(render_template("index.html", seed=seed, flag=flag, flag_error=flag_error))
    resp.set_cookie("id", seed, max_age=DEFAULT_EXPIRE)
    return resp


@app.route("/survey", methods=["GET", "POST"])
def survey():
    if "id" in request.cookies:
        seed = request.cookies["id"]
    else:
        seed = ''.join(random.choice(string.ascii_lowercase) for _ in range(16))

    if request.method == "POST":
        flag = request.cookies.get("flag")
        print(request.form, seed, flag)

        resp = redirect("/", code=303)
        resp.set_cookie("submitted", "yes", max_age=DEFAULT_EXPIRE)
        return resp

    resp = make_response(render_template("survey.html", submitted=request.cookies.get("submitted")))
    resp.set_cookie("id", seed, max_age=DEFAULT_EXPIRE)
    return resp


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


def create_app():
    secret = os.environ.get("SECRET")

    app.config["challenges"] = Path(__file__).parent.parent / "challenges"
    app.config["secret"] = secret

    return app


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

