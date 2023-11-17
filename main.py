from flask import Flask, redirect, render_template, url_for

AUTH_SECRET = 'OurHardWorkGuardedByTheseWordsPleaseDontSteal'
app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('admin'))

@app.route("/api/application/<string:app_name>")

@app.route("/admin")
def admin():
    return render_template('dashboard.html')

if __name__ == '__main__':
    print("Launching DRM Server...")
    app.run()