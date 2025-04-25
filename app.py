import os
import threading
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import time

# Flaskアプリケーションの設定
app = Flask(__name__)

# アップロードフォルダの設定
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# アップロードされるファイルの拡張子を制限する
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# パスがディレクトリでない or 存在しない場合のみ作成
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print(f"Checking if {UPLOAD_FOLDER} exists and is a directory...")

# アップロード可能なファイルの拡張子を確認する関数
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ログインページ
@app.route('/')
def login():
    return render_template('login.html')

# ギャラリー表示ページ
@app.route('/gallery')
def gallery():
    images = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('gallery.html', images=images)

# アップロードページ
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if not allowed_file(file.filename):
            return "File extension not allowed", 400  # 拡張子が許可されていない場合のエラーメッセージ
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('gallery'))
    return render_template('upload.html')

# タイマー機能 (24時間後に写真を削除する)
def delete_photos_in_background():
    time.sleep(24 * 60 * 60)  # 24時間待機
    for image in os.listdir(app.config['UPLOAD_FOLDER']):
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image)
        os.remove(image_path)

@app.route('/delete_photos', methods=['GET'])
def delete_photos():
    # 非同期でバックグラウンド処理を開始
    threading.Thread(target=delete_photos_in_background).start()
    return redirect(url_for('gallery'))

# アプリケーションの実行
if __name__ == '__main__':
    app.run(debug=True)
