import os
from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

# Flaskアプリケーションの設定
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッションのための秘密鍵

# アップロードフォルダの設定
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# アップロードされるファイルの拡張子を制限する
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# パスがディレクトリでない or 存在しない場合のみ作成
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# アップロード可能なファイルの拡張子を確認する関数
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ログインページ
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'correctpassword':  # ここでパスワードをチェック
            session['logged_in'] = True
            return redirect(url_for('gallery'))
        else:
            return "パスワードが違います", 403
    return render_template('login.html')

# ギャラリー表示ページ
@app.route('/gallery')
def gallery():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    images = os.listdir(app.config['UPLOAD_FOLDER'])
    if 'end_time' not in session:
        session['end_time'] = (datetime.now() + timedelta(hours=24)).isoformat()  # 24時間後の終了時間を設定
    
    end_time = datetime.fromisoformat(session['end_time'])
    return render_template('gallery.html', images=images, end_time=end_time)

# アップロードページ
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

# タイマー機能 (24時間後に写真を削除する)
@app.route('/delete_photos', methods=['GET'])
def delete_photos():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if datetime.now() >= datetime.fromisoformat(session['end_time']):
        for image in os.listdir(app.config['UPLOAD_FOLDER']):
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image)
            os.remove(image_path)
        session.pop('end_time', None)  # 終了時間を削除
    return redirect(url_for('gallery'))

# アプリケーションの実行
if __name__ == '__main__':
    # Renderではポートを環境変数で指定しているため、指定されたポートにバインドする
    port = int(os.environ.get('PORT', 5000))  # 環境変数からポートを取得
    app.run(host='0.0.0.0', port=port, debug=True)
