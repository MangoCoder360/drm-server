from flask import Flask, request, redirect, render_template, session, send_file, abort
from functools import wraps
import random, string, json, time

app = Flask(__name__)
app.secret_key = str(random.randint(0, 1000000000))

# AUTHENTICATION DECORATORS
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not "username" in session or session["login_area"] != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not "username" in session or session["login_area"] != "user":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

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

def get_ota_info_for_application(application):
    with open("ota.json", "r") as file:
        ota_info = json.load(file)
    return ota_info.get(application, {})

def get_ota_info_for_license(application, license_key, parameter):
    with open("ota.json", "r") as file:
        ota_info = json.load(file)
    return ota_info[application]["clientConfigs"][license_key].get(parameter, None)

def update_ota_app_config(application, parameter, value):
    with open("ota.json", "r") as file:
        ota_info = json.load(file)
    ota_info[application][parameter] = value
    with open("ota.json", "w") as file:
        json.dump(ota_info, file)

def update_ota_client_config(application, license_key, parameter, value):
    with open("ota.json", "r") as file:
        ota_info = json.load(file)
    ota_info[application]["clientConfigs"][license_key][parameter] = value
    with open("ota.json", "w") as file:
        json.dump(ota_info, file)
    

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
    
@app.route("/api/applications/<string:application>/ota/latest-version")
def ota_current_version(application):
    license_key = request.args.get("key")
    key_file = json.loads(open("license-keys.json").read())
    if application in key_file:
        if license_key in key_file[application]:
            return get_ota_info_for_application(application)["latestVersion"]
        else:
            return "403 Forbidden", 403
    else:
        return "403 Forbidden", 403

@app.route("/api/applications/<string:application>/ota/url")
def ota_url(application):
    license_key = request.args.get("key")
    key_file = json.loads(open("license-keys.json").read())
    if application in key_file:
        if license_key in key_file[application]:
            return get_ota_info_for_application(application)["url"]
        else:
            return "403 Forbidden", 403
    else:
        return "403 Forbidden", 403
    
@app.route("/api/applications/<string:application>/ota/client-config")
def ota_client_config(application):
    license_key = request.args.get("key")
    installed_version = request.args.get("version")
    build_number = request.args.get("build")

    if installed_version is None or build_number is None:
        return "400 Bad Request", 400
    
    key_file = json.loads(open("license-keys.json").read())
    if application in key_file:
        if license_key in key_file[application]:
            update_ota_client_config(application, license_key, "currentVersion", installed_version)
            update_ota_client_config(application, license_key, "buildNumber", build_number)
            update_ota_client_config(application, license_key, "lastConfigFetchTime", int(time.time()))
            return get_ota_info_for_application(application)["clientConfigs"][license_key]
        else:
            return "403 Forbidden", 403
    else:
        return "403 Forbidden", 403

@app.route("/ota/<string:application>/<string:version>/<string:filename>")
def ota_download(application, version, filename):
    license_key = request.args.get("key")
    key_file = json.loads(open("license-keys.json").read())
    if application in key_file:
        if license_key in key_file[application]:
            filepath = "ota/" + application + "-" + version + "-" + filename
            try:
                return send_file(filepath)
            except:
                return "404 Not Found", 404
    return "403 Forbidden", 403

  
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
@admin_required
def admin():
    return render_template("admin-dash.html", applications=enumerate_applications())

@app.route("/admin/<string:application>")
@admin_required
def admin_application(application):
    return render_template("admin-dash-appspecific.html", application=application, licenses=get_licenses_for_application(application), current_version=get_ota_info_for_application(application).get("latestVersion", "0.0.0"))

@app.route("/admin/<string:application>/publishing", methods=["POST","GET"])
@admin_required
def admin_publishing(application): 
    if request.method == "POST":
        version = request.form.get("version")
        file = request.files["file"]
        filepath = "ota/" + application + "-" + version.replace(".","-") + "-" + file.filename
        file.save(filepath)
        update_ota_app_config(application, "latestVersion", version)
        update_ota_app_config(application, "url", "/ota/" + application + "/" + version.replace(".","-") + "/" + file.filename)
        return redirect("/admin/" + application)
    return render_template("admin-publish-update.html", application=application, current_version=get_ota_info_for_application(application).get("latestVersion", "0.0.0"))

@app.route("/admin/<string:application>/licenses/<string:license_key>")
@admin_required
def admin_manage_license(application, license_key):
    license = get_licenses_for_application(application).get(license_key, {})
    secondsSinceLastConfigFetch = int(time.time()) - get_ota_info_for_license(application, license_key, "lastConfigFetchTime")
    buildNumber = get_ota_info_for_license(application, license_key, "buildNumber")
    return render_template("admin-manage-license.html", license=license, key=license_key, application=application, secondsSinceLastConfigFetch=secondsSinceLastConfigFetch, buildNumber=buildNumber)

@app.route("/user")
@user_required
def user():
    return render_template("user-dash.html", licenses=get_licenses_for_user(session["username"]))

# ENTRY FUNCTION
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5502)