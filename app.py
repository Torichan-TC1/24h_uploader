from flask import Flask, request, render_template, redirect, url_for, send_from_directory, session
import os
from datetime import datetime, timedelta
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'some_random_secret_key'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 24時間のタイマー
START_TIME = datetime.now()
END_TIME = START_TIME + timedelta(hours=24)

# パスワード
UPLOAD_PASS = "admin123"
VIEW_PASS = "guest123"

def is_expired():
    return datetime.now() > END_TIME

def clear_photos():
    shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.before_request
def expire_check():
    if is_expired():
        clear_photos()
        return "<h2>このサイトは終了しました。</h2>", 403

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pw = request.form.get('password')
        if pw == VIEW_PASS:
            session['auth'] = True
            return redirect(url_for('gallery'))
        return "パスワードが違います", 403
    return render_template('login.html', end_time=END_TIME)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        pw = request.form.get('password')
        file = request.files['file']
        if pw != UPLOAD_PASS:
            return "アップロード用パスワードが違います", 403
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return redirect(url_for('upload'))
    return render_template('upload.html', end_time=END_TIME)

@app.route('/gallery')
def gallery():
    if not session.get('auth'):
        return redirect(url_for('login'))
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('gallery.html', files=files, end_time=END_TIME)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# for Render
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
