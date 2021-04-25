import argparse
import datetime
import os
import random
import re
import string
from pathlib import Path
from secrets import compare_digest

from flask import (
    Flask,
    abort,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
)

from .challenge import Challenge
from .survey import submit

app = Flask(__name__, template_folder="../templates")


@app.context_processor
def inject_app_title():
    return dict(title=os.environ.get("TITLE", "Vulnspec Server"))


DEFAULT_EXPIRE = datetime.timedelta(days=14)


def validate_flag(flag: str) -> bool:
    match = re.match(r"FLAG{(\d+)_(\d+)}", flag)
    if match:
        a = int(match.group(1))
        b = int(match.group(2))
        return a * 2 + 42 == b
    else:
        return False


@app.route("/notice")
def notice():
    if request.args.get("confirm"):
        if "id" in request.cookies:
            seed = request.cookies["id"]
        else:
            seed = "".join(random.choice(string.ascii_lowercase) for _ in range(16))

        resp = make_response(redirect("/", code=303))
        resp.set_cookie("id", seed, max_age=DEFAULT_EXPIRE, secure=True)
        return resp
    else:
        return render_template("notice.html")


@app.route("/", methods=["GET", "POST"])
def index():
    if not "id" in request.cookies:
        return redirect("/notice", 302)
    seed = request.cookies["id"]

    flag_error = False

    if "flag" in request.cookies:
        flag = request.cookies["flag"]
    else:
        flag = ""
        if request.method == "POST":
            if validate_flag(request.form["flag"]):
                flag = request.form["flag"]
                resp = redirect("/success", code=303)
                resp.set_cookie(
                    "flag", request.form["flag"], max_age=DEFAULT_EXPIRE, secure=True
                )
                return resp
            else:
                flag_error = True

    return render_template("index.html", seed=seed, flag=flag, flag_error=flag_error)


@app.route("/success")
def success():
    if "flag" not in request.cookies:
        return redirect("/", code=302)

    flag = request.cookies["flag"]
    return render_template("success.html", flag=flag)


@app.route("/survey", methods=["GET", "POST"])
def survey():
    if not "id" in request.cookies:
        return redirect("/notice", 302)
    seed = request.cookies["id"]

    flag = request.cookies.get("flag")

    if request.method == "POST":
        submit(request.form)

        resp = make_response(redirect("/", code=303))
        resp.set_cookie("submitted", "yes", max_age=DEFAULT_EXPIRE, secure=True)
        return resp

    return render_template(
        "survey.html",
        seed=seed,
        flag=flag,
        submitted=request.cookies.get("submitted"),
    )


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
