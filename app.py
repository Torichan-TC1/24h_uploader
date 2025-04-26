import os
from flask import Flask, request, render_template, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import zipfile
import io

# Flask アプリケーション設定
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッション用の秘密鍵

# アップロードフォルダ設定
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# アップロードフォルダがなければ作成
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 拡張子チェック関数
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ログインページ
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'hato_0421':  # ログインパスワード
            session['logged_in'] = True
            return redirect(url_for('upload_file'))  # アップロード画面にリダイレクト
        else:
            return "パスワードが違います", 403
    return render_template('login.html')

# アップロードページ
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        # 複数ファイルアップロード対応
        if 'file' not in request.files:
            return redirect(request.url)
        files = request.files.getlist('file')  # 複数ファイルを取得
        for file in files:
            if file.filename == '':
                continue
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('gallery'))
    return render_template('upload.html')

# ギャラリーページ
@app.route('/gallery')
def gallery():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    images = os.listdir(app.config['UPLOAD_FOLDER'])

    # 翌日の0時を end_time に設定
    if 'end_time' not in session:
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        end_of_day = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
        session['end_time'] = end_of_day.isoformat()

    end_time = datetime.fromisoformat(session['end_time'])
    return render_template('gallery.html', images=images, end_time=end_time)

# 写真アップロード
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

# 24時間経過後に写真を削除
@app.route('/delete_photos')
def delete_photos():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if datetime.now() >= datetime.fromisoformat(session['end_time']):
        for image in os.listdir(app.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image))
        session.pop('end_time', None)
    return redirect(url_for('gallery'))

# アプリ起動
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
