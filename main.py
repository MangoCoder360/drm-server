from flask import Flask, request
import random, string, json

app = Flask(__name__)

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

def generate_license_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5502)