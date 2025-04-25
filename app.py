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
        if password == '7':  # ✅ ログインパスワード
            session['logged_in'] = True
            return redirect(url_for('gallery'))
        else:
            return "パスワードが違います", 403
    return render_template('login.html')

# ギャラリーページ
@app.route('/gallery')
def gallery():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    images = os.listdir(app.config['UPLOAD_FOLDER'])
    
    # 24時間後の終了時間がセッションにない場合はセット
    if 'end_time' not in session:
        session['end_time'] = (datetime.now() + timedelta(hours=24)).isoformat()
    
    end_time = datetime.fromisoformat(session['end_time'])
    return render_template('gallery.html', images=images, end_time=end_time)

# 写真アップロード
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('gallery'))
    return render_template('upload.html')

# 選択された画像を ZIP ダウンロード
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
