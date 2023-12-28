from datetime import datetime
import math
import os
import random
import re
import smtplib
from urllib.request import urlopen
import json
from flask_app import app
from flask_app.models.user import User
from flask_app.models.interest import Interest
from flask_app.models.articles import Article

from flask import jsonify, render_template, redirect, session, request, flash
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)
from werkzeug.utils import secure_filename
from .env import ADMINEMAIL, ALLOWED_EXTENSIONS, API_KEY, PASSWORD, UPLOAD_FOLDER

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
from newsapi import NewsApiClient

newsapi = NewsApiClient(api_key=API_KEY)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$")


def sendemail(emailaddr, verificationCode):
    LOGIN = ADMINEMAIL
    TOADDRS = emailaddr
    SENDER = ADMINEMAIL
    SUBJECT = "Verify Your Email"
    msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (
        (SENDER),
        "".join(TOADDRS),
        SUBJECT,
    )
    msg += f"Use this verification code to activate your account: {verificationCode}"
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.set_debuglevel(1)
    server.ehlo()
    server.starttls()
    server.login(LOGIN, PASSWORD)
    server.sendmail(SENDER, TOADDRS, msg)
    server.quit()


# Check if the format is right
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.errorhandler(404)
def invalid_route(e):
    return render_template("404.html")


@app.route("/")
def index():
    if "user_id" in session:
        return redirect("/dashboard")
    return render_template("index.html")


@app.route("/h")
def home():
    return render_template("homepage.html")


@app.route("/register", methods=["POST"])
def register():
    if "user_id" in session:
        return redirect("/")

    # Validate the form data.
    errors = {}
    if User.get_user_by_email(request.form):
        errors["email"] = "This email already exists"

    if not EMAIL_REGEX.match(request.form["email"]):
        errors["email"] = "Invalid email address!"

    if not request.form["email"]:
        errors["email"] = "Email address is required."

    if len(request.form["last_name"]) < 2:
        errors["last_name"] = "Last name should be more than 2 characters!"

    if not request.form["last_name"]:
        errors["last_name"] = "Last Name is required."

    if len(request.form["password"]) < 8:
        errors["password"] = "Password must be longer than 8 characters"

    if not request.form["password"]:
        errors["password"] = "Password is required."

    if len(request.form["first_name"]) < 2:
        errors["first_name"] = "First name should be more than 2 characters!"

    if not request.form["first_name"]:
        errors["first_name"] = "First Name is required."

    if request.form["password"] != request.form["confirmpass"]:
        errors["confirmpass"] = "Passwords do not match!"

    if not request.form["confirmpass"]:
        errors["confirmpass"] = "Confirm Password is required."

    if errors:
        return jsonify({"valid": False, "errors": errors})

    string = "0123456789ABCDEFGHIJKELNOPKQSTUV"
    vCode = ""
    length = len(string)
    for i in range(6):
        vCode += string[math.floor(random.random() * length)]
    verificationCode = vCode
    data = {
        "first_name": request.form["first_name"],
        "last_name": request.form["last_name"],
        "email": request.form["email"],
        "password": bcrypt.generate_password_hash(request.form["password"]),
        "isVerified": 0,
        "verification_code": verificationCode,
    }
    User.save(data)

    sendemail(request.form["email"], verificationCode)

    user = User.get_user_by_email(data)
    session["user_id"] = user["id"]
    return jsonify({"valid": True, "path": "/verify/email"})


@app.route("/getstarted")
def getstarted():
    if "user_id" not in session:
        return redirect("/")
    data = {"user_id": session["user_id"]}
    user = User.get_user_by_id(data)
    if user["isVerified"] == 0:
        return redirect("/verify/email")
    if len(Interest.get_all_User_Interest(data)) > 0:
        return redirect("/dashboard")
    return render_template(
        "choosePreferences.html", loggedUser=User.get_user_by_id(session["user_id"])
    )


@app.route("/login", methods=["POST"])
def login():
    if "user_id" in session:
        return redirect("/")
    errors = {}

    if not User.get_user_by_email(request.form):
        errors["email"] = "This email doesnt appear to be in our system!"

    if not request.form["email"]:
        errors["email"] = "Email address is required."
    user = User.get_user_by_email(request.form)
    if user:
        if not bcrypt.check_password_hash(user["password"], request.form["password"]):
            errors["password"] = "Wrong Password"

    if not request.form["password"]:
        errors["password"] = "Password is required."

    # If the form is invalid, return a list of validation errors.
    if errors:
        return jsonify({"valid": False, "errors": errors})

    user = User.get_user_by_email(request.form)

    session["user_id"] = user["id"]

    return jsonify({"valid": True, "path": "/verify/email"})


@app.route("/verify/email")
def verifyEmail():
    if "user_id" not in session:
        return redirect("/")
    data = {"user_id": session["user_id"]}
    user = User.get_user_by_id(data)
    if user["isVerified"] == 1:
        return redirect("/getstarted")
    return render_template("verifyEmail.html", loggedUser=user)


@app.route("/activate/account", methods=["POST"])
def activateAccount():
    if "user_id" not in session:
        return redirect("/")
    data = {"user_id": session["user_id"]}
    user = User.get_user_by_id(data)
    if user["isVerified"] == 1:
        return redirect("/getstarted")

    if not request.form["verificationCode"]:
        flash("Verification Code is required", "wrongCode")
        return redirect(request.referrer)

    if request.form["verificationCode"] != user["verification_code"]:
        string = "0123456789ABCDEFGHIJKELNOPKQSTUV"
        vCode = ""
        length = len(string)
        for i in range(6):
            vCode += string[math.floor(random.random() * length)]
        verificationCode = vCode
        dataUpdate = {
            "verification_code": verificationCode,
            "user_id": session["user_id"],
        }
        User.updateVerificationCode(dataUpdate)
        sendemail(user["email"], verificationCode)

        flash("Verification Code is wrong. We just sent you a new one", "wrongCode")
        return redirect(request.referrer)

    User.activateAccount(data)
    return redirect("/getstarted")


@app.route("/resend/verification/email")
def resendCode():
    if "user_id" not in session:
        return redirect("/")
    data = {"user_id": session["user_id"]}
    user = User.get_user_by_id(data)
    if user["isVerified"] == 1:
        return redirect("/dashboard")
    string = "0123456789ABCDEFGHIJKELNOPKQSTUV"
    vCode = ""
    length = len(string)
    for i in range(6):
        vCode += string[math.floor(random.random() * length)]
    verificationCode = vCode
    dataUpdate = {
        "verification_code": verificationCode,
        "user_id": session["user_id"],
    }
    User.updateVerificationCode(dataUpdate)
    print("update verification")
    sendemail(user["email"], verificationCode)

    flash(
        "Verification Code has been resent. Make sure to check Spam Inbox", "codeResent"
    )
    return redirect(request.referrer)


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    data = {"user_id": session["user_id"]}
    loggedUser = User.get_user_by_id(data)
    if loggedUser["isVerified"] == 0:
        return redirect("/verify/email")
    articles = []
    keywords = []
    userinterests = Interest.get_all_User_Interest(data)
    qu = ""
    for i in range(len(userinterests)):
        keywords.append(userinterests[i].key_word)
        if i != len(userinterests) - 1:
            qu += f"{userinterests[i].key_word}+OR+"
        else:
            qu += userinterests[i].key_word
    url = f"https://newsapi.org/v2/everything?q={qu}&language=en&apiKey=bf1cb8dc1df74505a310b9dc5301942e"
    response = urlopen(url)
    articles = json.loads(response.read())['articles']
    savedArticles = []
    ids = []
    for a in Article.get_all_User_Articles(data):
        savedArticles.append(a.url)
        ids.append(a.id)
    return render_template(
        "dashboard.html",
        articles=articles,
        loggedUser=loggedUser,
        savedArticles=savedArticles,
        keywords=keywords,
        savedArticlesids=ids
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/profile/<int:user_id>")
def show_profile(user_id):
    if "user_id" not in session or user_id != session["user_id"]:
        return redirect("/")
    data = {
        "user_id": session["user_id"],
    }
    return render_template(
        "profile.html",
        loggedUser=User.get_user_by_id(data),
        topics=Interest.get_all_User_Interest(data),
        saved=Article.get_all_User_Articles(data),
    )


@app.route("/editProfile", methods=["POST"])
def editProfile():
    if "user_id" not in session:
        return redirect("/")
    errors = {}
    if User.get_user_by_email(request.form):
        errors["email"] = "This email already exists"

    if not EMAIL_REGEX.match(request.form["email"]):
        errors["email"] = "Invalid email address!"

    if not request.form["email"]:
        errors["email"] = "Email address is required."

    if len(request.form["last_name"]) < 2:
        errors["last_name"] = "Last name should be more than 2 characters!"

    if not request.form["last_name"]:
        errors["last_name"] = "Last Name is required."

    if len(request.form["first_name"]) < 2:
        errors["first_name"] = "First name should be more than 2 characters!"

    if not request.form["first_name"]:
        errors["first_name"] = "First Name is required."

    if errors:
        return jsonify({"valid": False, "errors": errors})

    data = {
        "user_id": session["user_id"],
        "first_name": request.form["first_name"],
        "last_name": request.form["last_name"],
        "email": request.form["email"],
    }
    User.update(data)
    return jsonify({"valid": True, "path": "/edit/<session['user_id']>"})


# to do
# update pass, update profile pic


@app.route("/editPassword", methods=["POST"])
def editPass():
    if "user_id" not in session:
        return redirect("/")
    data = {"user_id": session["user_id"], "password": request.form["newpsw"]}
    errors = {}
    if not bcrypt.check_password_hash(
        User.get_user_by_id(data)["password"], request.form["oldpsw"]
    ):
        errors["oldpsw"] = "Old password is not correct"
    if len(request.form["newpsw"]) < 8:
        errors["newpsw"] = "Password should be more than 2 characters"
    if request.form["newpsw"] != request.form["confirmnewpsw"]:
        errors["confirmnewpsw"] = "New passwords should match!"
    if errors:
        return jsonify({"valid": False, "errors": errors})
    User.updatePass(data)
    return jsonify({"valid": True, "path": "/edit/<session['user_id']>"})


@app.route("/editprofilepic", methods=["POST"])
def updatePic():
    if "user_id" not in session:
        return redirect("/")
    if not request.files["image"]:
        flash("Image is required!", "Image")
        return redirect(request.referrer)
    image = request.files["image"]
    if not allowed_file(image.filename):
        flash("Image should be in png, jpg, jpeg format!", "Image")
        return redirect(request.referrer)

    filename1 = secure_filename(image.filename)
    time = datetime.now().strftime("%d%m%Y%S%f")
    time += filename1
    filename1 = time
    image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename1))

    data = {
        "user_id": session["user_id"],
        "profile_pic": filename1,
    }

    User.updateProfilePic(data)
    flash("Update Succesful", "success")
    return redirect(request.referrer)
