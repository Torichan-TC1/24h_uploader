import os
from flask import Flask, request, render_template, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import zipfile
import io

# Flask アプリケーション設定
app = Flask(__name__, static_folder='assets')
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == '7':
            session['logged_in'] = True
            return redirect(url_for('gallery'))
        else:
            return "パスワードが違います", 403
    return render_template('login.html')

@app.route('/gallery')
def gallery():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    images = os.listdir(app.config['UPLOAD_FOLDER'])

    if 'end_time' not in session:
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        end_of_day = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
        session['end_time'] = end_of_day.isoformat()

    end_time = datetime.fromisoformat(session['end_time'])
    return render_template('gallery.html', images=images, end_time=end_time)

@app.route('/upload', methods=['POST'])
def upload_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if 'files' not in request.files:
        print("ファイルが見つかりません")
        return redirect(request.url)

    files = request.files.getlist('files')
    if not files:
        print("ファイルが空です")
        return redirect(request.url)

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            print(f"保存: {filename}")
        else:
            print(f"無効なファイル形式: {file.filename}")

    return redirect(url_for('gallery'))

@app.route('/download_selected', methods=['POST'])
def download_selected():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    selected_files = request.form.getlist('selected_images')
    if not selected_files:
        return redirect(url_for('gallery'))

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for filename in selected_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            zip_file.write(file_path, arcname=filename)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name='selected_photos.zip',
        mimetype='application/zip'
    )

@app.route('/delete_photos')
def delete_photos():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if datetime.now() >= datetime.fromisoformat(session['end_time']):
        for image in os.listdir(app.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image))
        session.pop('end_time', None)

    return redirect(url_for('gallery'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
