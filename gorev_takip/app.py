from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3, os, datetime
import dropbox
import bcrypt

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'tasks.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
# Dropbox API token must be provided via environment variable
DROPBOX_TOKEN = os.environ.get('DROPBOX_TOKEN')
if not DROPBOX_TOKEN:
    raise RuntimeError('DROPBOX_TOKEN environment variable not set')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizli_knk_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

dbx = dropbox.Dropbox(DROPBOX_TOKEN)

# ----- Database -----
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password BLOB NOT NULL,
                is_admin INTEGER DEFAULT 0
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                firma TEXT,
                santiye TEXT,
                tarih TEXT,
                aciklama TEXT,
                dosya_adi TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )"""
        )
        conn.commit()

class User(UserMixin):
    def __init__(self, id_, username, is_admin):
        self.id = id_
        self.username = username
        self.is_admin = bool(is_admin)

@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, is_admin FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        if row:
            return User(*row)
    return None

# ----- Helper -----
def save_file(username, firma, santiye, file):
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    local_dir = os.path.join(UPLOAD_FOLDER, firma, santiye, date_str)
    os.makedirs(local_dir, exist_ok=True)
    filename = f"{date_str}_{username}_{file.filename}"
    local_path = os.path.join(local_dir, filename)
    file.save(local_path)

    dropbox_path = f"/{firma}/{santiye}/{date_str}/{filename}"
    with open(local_path, 'rb') as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
    return os.path.relpath(local_path, UPLOAD_FOLDER)

# ----- Routes -----
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT id, password, is_admin FROM users WHERE username=?", (username,))
            row = c.fetchone()
            if row and bcrypt.checkpw(password, row[1]):
                user = User(row[0], username, row[2])
                login_user(user)
                return redirect(url_for('dashboard'))
        flash('Giriş başarısız')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users(username, password, is_admin) VALUES (?,?,0)", (username, password))
                conn.commit()
                flash('Kayıt başarılı, giriş yapabilirsiniz')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Kullanıcı adı zaten var')
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT firma, santiye, tarih, aciklama, dosya_adi FROM tasks WHERE user_id=?", (current_user.id,))
        tasks = c.fetchall()
    return render_template('dashboard.html', tasks=tasks)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        firma = request.form['firma']
        santiye = request.form['santiye']
        aciklama = request.form['aciklama']
        tarih = request.form['tarih']
        file = request.files['foto']
        saved_path = save_file(current_user.username, firma, santiye, file)
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO tasks(user_id, firma, santiye, tarih, aciklama, dosya_adi) VALUES (?,?,?,?,?,?)",
                (current_user.id, firma, santiye, tarih, aciklama, saved_path)
            )
            conn.commit()
        flash('Görev kaydedildi')
        return redirect(url_for('dashboard'))
    return render_template('add_task.html')

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT u.username, t.firma, t.santiye, t.tarih, t.aciklama, t.dosya_adi FROM tasks t JOIN users u ON t.user_id=u.id"
        )
        tasks = c.fetchall()
    return render_template('admin.html', tasks=tasks)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    app.run(debug=True)
