from flask import Flask, request, redirect, render_template, session
import random, string, json

app = Flask(__name__)
app.secret_key = str(random.randint(0, 1000000000))

# UTILITY FUNCTIONS
def generate_license_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

def enumerate_applications():
    allKeysForApplication = json.loads(open("license-keys.json").read())
    keys = allKeysForApplication.keys()
    array = []
    for key in keys:
        array.append(key)
    return array

def get_licenses_for_user(username):
    with open("license-keys.json", "r") as file:
        all_keys_for_application = json.load(file)
    licenses = {}
    for application, keys in all_keys_for_application.items():
        for key, details in keys.items():
            if details.get("dashboardOwner") == username:
                licenses[key] = details
                licenses[key]["application"] = application

    return licenses

def get_licenses_for_application(application):
    with open("license-keys.json", "r") as file:
        all_keys_for_application = json.load(file)
    return all_keys_for_application.get(application, {})

# API ENDPOINTS
@app.route("/api/applications/<string:application>/license-keys/check")
def license_key_check(application):
    licenseKey = request.args.get('key')
    allKeysForApplication = json.loads(open("license-keys.json").read())
    if application in allKeysForApplication:
        if licenseKey in allKeysForApplication[application]:
            return allKeysForApplication[application][licenseKey]
        else:
            return {"status": "invalid", "minVersion": 1}
    else:
        return {"status": "invalid", "minVersion": 1}
  
# UI ENDPOINTS
@app.route("/")
def index():
    if "username" in session:
        if session["login_area"] == "admin":
            return redirect("/admin")
        elif session["login_area"] == "user":
            return redirect("/user")
    else:
        return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    login_area = request.form.get("login_area")
    if username != "admin" and login_area == "admin":
        return redirect("/")
    else:
        with open("passwords.json", "r") as file:
            passwords = json.load(file)
        if username in passwords and passwords[username] == password:
            session["username"] = username
            session["login_area"] = login_area
            return redirect("/")
        else:
            return redirect("/")
    
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        with open("passwords.json", "r") as file:
            passwords = json.load(file)
        
        if username in passwords:
            return redirect("/register")
        else:
            passwords[username] = password

        with open("passwords.json", "w") as file:
            json.dump(passwords, file)
        
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")

@app.route("/admin")
def admin():
    return render_template("admin-dash.html", applications=enumerate_applications())

@app.route("/admin/<string:application>")
def admin_application(application):
    return render_template("admin-dash-appspecific.html", application=application, licenses=get_licenses_for_application(application))

@app.route("/admin/<string:application>/licenses/<string:license_key>")
def admin_manage_license(application, license_key):
    return render_template("admin-manage-license.html")

@app.route("/user")
def user():
    return render_template("user-dash.html", licenses=get_licenses_for_user(session["username"]))

# ENTRY FUNCTION
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5502)