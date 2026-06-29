from flask import Blueprint, request, session, jsonify, render_template
from models.users import (get_all_users,
    get_user_stats,
    get_all_divisions_for_form,
    get_all_customers_for_form,
    create_user,
    update_user,
    deactivate_user,
    get_by_email
)
import hashlib

auth = Blueprint("auth", __name__)

@auth.route("/")
def index():
    return render_template("loginpage.html", active_page="login")

@auth.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = get_by_email(email)

    if user:
        stored = user["userPassword"]
        hashed_part, salt = stored.split(":")
        attempt = hashlib.md5((password + salt).encode()).hexdigest()

        if attempt == hashed_part:
            session["user_id"] = user["userID"]
            session["user_name"] = user["userName"]
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Invalid credentials"})
    else:
        return jsonify({"success": False, "message": "User not found"})