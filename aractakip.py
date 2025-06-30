import sys
import os
import sqlite3
import datetime
from PyQt5 import QtWidgets, QtGui, QtCore

DB_PATH = 'arac_takip.db'
LOGO_PATH = 'logo.png'

# Translation dictionaries
translations = {
    'tr': {
        'login': 'Giri\u015f',
        'username': 'Kullan\u0131c\u0131 Ad\u0131',
        'password': '\u015eifre',
        'home': 'Anasayfa',
        'vehicles': 'Ara\u00e7lar',
        'users': 'Kullan\u0131c\u0131lar',
        'logs': 'Loglar',
        'settings': 'Ayarlar',
        'change_password': '\u015eifre De\u011fi\u015ftir',
        'logout': '\u00c7\u0131k\u0131\u015f',
        'total_vehicles': 'Toplam {count} arac\u0131n\u0131z var.',
        'add': 'Ekle',
        'edit': 'D\u00fczenle',
        'delete': 'Sil',
        'plate': 'Plaka',
        'driver': '\u015eof\u00f6r',
        'km': 'KM',
        'last_maintenance': 'Son Bak\u0131m',
        'save': 'Kaydet',
        'cancel': '\u0130ptal',
        'new_user': 'Yeni Kullan\u0131c\u0131',
        'language': 'Dil',
        'theme': 'Tema',
        'light': 'A\u00e7\u0131k',
        'dark': 'Koyu',
        'turkish': 'T\u00fcrk\u00e7e',
        'german': 'Almanca',
        'current_password': 'Mevcut \u015eifre',
        'new_password': 'Yeni \u015eifre',
        'confirm_password': '\u015eifreyi Onayla',
        'password_changed': '\u015eifre de\u011fi\u015ftirildi',
        'incorrect_password': 'Hatal\u0131 \u015eifre',
        'user_exists': 'Kullan\u0131c\u0131 zaten var',
        'add_vehicle': 'Ara\u00e7 Ekle',
        'edit_vehicle': 'Ara\u00e7 D\u00fczenle',
        'add_user': 'Kullan\u0131c\u0131 Ekle',
        'login_failed': 'Giri\u015f ba\u015far\u0131s\u0131z'
    },
    'de': {
        'login': 'Anmeldung',
        'username': 'Benutzername',
        'password': 'Passwort',
        'home': 'Startseite',
        'vehicles': 'Fahrzeuge',
        'users': 'Benutzer',
        'logs': 'Logs',
        'settings': 'Einstellungen',
        'change_password': 'Passwort \u00e4ndern',
        'logout': 'Abmelden',
        'total_vehicles': 'Sie haben insgesamt {count} Fahrzeuge.',
        'add': 'Hinzuf\u00fcgen',
        'edit': 'Bearbeiten',
        'delete': 'L\u00f6schen',
        'plate': 'Kennzeichen',
        'driver': 'Fahrer',
        'km': 'KM',
        'last_maintenance': 'Letzte Wartung',
        'save': 'Speichern',
        'cancel': 'Abbrechen',
        'new_user': 'Neuer Benutzer',
        'language': 'Sprache',
        'theme': 'Thema',
        'light': 'Hell',
        'dark': 'Dunkel',
        'turkish': 'T\u00fcrkisch',
        'german': 'Deutsch',
        'current_password': 'Aktuelles Passwort',
        'new_password': 'Neues Passwort',
        'confirm_password': 'Passwort best\u00e4tigen',
        'password_changed': 'Passwort ge\u00e4ndert',
        'incorrect_password': 'Falsches Passwort',
        'user_exists': 'Benutzer existiert bereits',
        'add_vehicle': 'Fahrzeug hinzuf\u00fcgen',
        'edit_vehicle': 'Fahrzeug bearbeiten',
        'add_user': 'Benutzer hinzuf\u00fcgen',
        'login_failed': 'Anmeldung fehlgeschlagen'
    }
}

LIGHT_STYLE = ""
DARK_STYLE = """\
QWidget { background-color: #2b2b2b; color: #f0f0f0; }\
QLineEdit, QTableWidget { background-color: #3c3c3c; color: #f0f0f0; }\
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plate TEXT UNIQUE,
                    driver TEXT,
                    km INTEGER,
                    last_maintenance TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    user TEXT,
                    action TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings(
                    key TEXT PRIMARY KEY,
                    value TEXT)''')
    # default admin user
    c.execute('SELECT * FROM users WHERE username=?', ('knkbau',))
    if not c.fetchone():
        c.execute('INSERT INTO users(username,password) VALUES (?,?)',
                  ('knkbau','Herdemcan1'))
    # default settings
    for key, value in [('language','tr'), ('theme','light')]:
        c.execute('INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)', (key,value))
    conn.commit()
    conn.close()


def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key=?', (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ''


def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('REPLACE INTO settings(key,value) VALUES (?,?)', (key,value))
    conn.commit()
    conn.close()


def add_log(user, action):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO logs(timestamp,user,action) VALUES (?,?,?)',
              (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user, action))
    conn.commit()
    conn.close()


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, language):
        super().__init__()
        self.language = language
        self.setWindowTitle(translations[self.language]['login'])
        layout = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QFormLayout()
        self.user_edit = QtWidgets.QLineEdit()
        self.pass_edit = QtWidgets.QLineEdit()
        self.pass_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        form.addRow(translations[self.language]['username'], self.user_edit)
        form.addRow(translations[self.language]['password'], self.pass_edit)
        layout.addLayout(form)

        self.logo = QtWidgets.QLabel()
        if os.path.exists(LOGO_PATH):
            pix = QtGui.QPixmap(LOGO_PATH).scaledToWidth(100, QtCore.Qt.SmoothTransformation)
            self.logo.setPixmap(pix)
        layout.addWidget(self.logo, alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)

        btn = QtWidgets.QPushButton(translations[self.language]['login'])
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def get_credentials(self):
        return self.user_edit.text(), self.pass_edit.text()


class VehicleDialog(QtWidgets.QDialog):
    def __init__(self, language, data=None):
        super().__init__()
        self.language = language
        self.setWindowTitle(translations[self.language]['add_vehicle'] if data is None else translations[self.language]['edit_vehicle'])
        layout = QtWidgets.QFormLayout(self)
        self.plate = QtWidgets.QLineEdit()
        self.driver = QtWidgets.QLineEdit()
        self.km = QtWidgets.QLineEdit()
        self.last = QtWidgets.QLineEdit()
        layout.addRow(translations[self.language]['plate'], self.plate)
        layout.addRow(translations[self.language]['driver'], self.driver)
        layout.addRow(translations[self.language]['km'], self.km)
        layout.addRow(translations[self.language]['last_maintenance'], self.last)
        btns = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.box = QtWidgets.QDialogButtonBox(btns)
        self.box.accepted.connect(self.accept)
        self.box.rejected.connect(self.reject)
        layout.addWidget(self.box)
        if data:
            self.plate.setText(data['plate'])
            self.driver.setText(data['driver'])
            self.km.setText(str(data['km']))
            self.last.setText(data['last_maintenance'])

    def get_data(self):
        return {
            'plate': self.plate.text(),
            'driver': self.driver.text(),
            'km': self.km.text(),
            'last_maintenance': self.last.text()
        }


class UserDialog(QtWidgets.QDialog):
    def __init__(self, language):
        super().__init__()
        self.language = language
        self.setWindowTitle(translations[self.language]['add_user'])
        layout = QtWidgets.QFormLayout(self)
        self.username = QtWidgets.QLineEdit()
        self.password = QtWidgets.QLineEdit()
        layout.addRow(translations[self.language]['username'], self.username)
        layout.addRow(translations[self.language]['password'], self.password)
        btns = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.box = QtWidgets.QDialogButtonBox(btns)
        self.box.accepted.connect(self.accept)
        self.box.rejected.connect(self.reject)
        layout.addWidget(self.box)

    def get_data(self):
        return self.username.text(), self.password.text()


class PasswordDialog(QtWidgets.QDialog):
    def __init__(self, language):
        super().__init__()
        self.language = language
        self.setWindowTitle(translations[self.language]['change_password'])
        layout = QtWidgets.QFormLayout(self)
        self.current = QtWidgets.QLineEdit()
        self.current.setEchoMode(QtWidgets.QLineEdit.Password)
        self.new = QtWidgets.QLineEdit()
        self.new.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirm = QtWidgets.QLineEdit()
        self.confirm.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addRow(translations[self.language]['current_password'], self.current)
        layout.addRow(translations[self.language]['new_password'], self.new)
        layout.addRow(translations[self.language]['confirm_password'], self.confirm)
        btns = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.box = QtWidgets.QDialogButtonBox(btns)
        self.box.accepted.connect(self.accept)
        self.box.rejected.connect(self.reject)
        layout.addWidget(self.box)

    def get_data(self):
        return self.current.text(), self.new.text(), self.confirm.text()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.language = get_setting('language')
        self.theme = get_setting('theme')
        self.setWindowTitle('Ara\u00e7 Takip')
        self.resize(800, 600)
        self.central = QtWidgets.QWidget()
        self.setCentralWidget(self.central)
        self.create_ui()
        self.update_language()
        self.apply_theme()

    def create_ui(self):
        main_layout = QtWidgets.QHBoxLayout(self.central)
        self.menu = QtWidgets.QListWidget()
        self.menu.addItems([
            translations[self.language]['home'],
            translations[self.language]['vehicles'],
            translations[self.language]['users'],
            translations[self.language]['logs'],
            translations[self.language]['settings'],
            translations[self.language]['change_password'],
            translations[self.language]['logout']])
        self.menu.currentRowChanged.connect(self.display_page)
        main_layout.addWidget(self.menu)

        self.stack = QtWidgets.QStackedWidget()
        main_layout.addWidget(self.stack)

        # Home Page
        self.home_page = QtWidgets.QWidget()
        hlayout = QtWidgets.QVBoxLayout(self.home_page)
        self.home_label = QtWidgets.QLabel()
        hlayout.addWidget(self.home_label)
        self.stack.addWidget(self.home_page)

        # Vehicles Page
        self.vehicle_page = QtWidgets.QWidget()
        vlayout = QtWidgets.QVBoxLayout(self.vehicle_page)
        self.vehicle_table = QtWidgets.QTableWidget(0,4)
        self.vehicle_table.setHorizontalHeaderLabels([
            translations[self.language]['plate'],
            translations[self.language]['driver'],
            translations[self.language]['km'],
            translations[self.language]['last_maintenance']])
        vlayout.addWidget(self.vehicle_table)
        btn_layout = QtWidgets.QHBoxLayout()
        self.add_vehicle_btn = QtWidgets.QPushButton(translations[self.language]['add'])
        self.edit_vehicle_btn = QtWidgets.QPushButton(translations[self.language]['edit'])
        self.del_vehicle_btn = QtWidgets.QPushButton(translations[self.language]['delete'])
        self.add_vehicle_btn.clicked.connect(self.add_vehicle)
        self.edit_vehicle_btn.clicked.connect(self.edit_vehicle)
        self.del_vehicle_btn.clicked.connect(self.delete_vehicle)
        for b in [self.add_vehicle_btn, self.edit_vehicle_btn, self.del_vehicle_btn]:
            btn_layout.addWidget(b)
        vlayout.addLayout(btn_layout)
        self.stack.addWidget(self.vehicle_page)

        # Users Page
        self.user_page = QtWidgets.QWidget()
        ulayout = QtWidgets.QVBoxLayout(self.user_page)
        self.user_table = QtWidgets.QTableWidget(0,1)
        self.user_table.setHorizontalHeaderLabels([translations[self.language]['username']])
        ulayout.addWidget(self.user_table)
        self.add_user_btn = QtWidgets.QPushButton(translations[self.language]['add'])
        self.add_user_btn.clicked.connect(self.add_user)
        ulayout.addWidget(self.add_user_btn)
        self.stack.addWidget(self.user_page)

        # Logs Page
        self.log_page = QtWidgets.QWidget()
        llayout = QtWidgets.QVBoxLayout(self.log_page)
        self.log_table = QtWidgets.QTableWidget(0,3)
        self.log_table.setHorizontalHeaderLabels(['Time','User','Action'])
        llayout.addWidget(self.log_table)
        self.stack.addWidget(self.log_page)

        # Settings Page
        self.settings_page = QtWidgets.QWidget()
        slayout = QtWidgets.QFormLayout(self.settings_page)
        self.lang_combo = QtWidgets.QComboBox()
        self.lang_combo.addItem(translations['tr']['turkish'],'tr')
        self.lang_combo.addItem(translations['de']['german'],'de')
        self.lang_combo.setCurrentIndex(0 if self.language=='tr' else 1)
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItem(translations['tr']['light'],'light')
        self.theme_combo.addItem(translations['tr']['dark'],'dark')
        self.theme_combo.setCurrentIndex(0 if self.theme=='light' else 1)
        slayout.addRow(translations[self.language]['language'], self.lang_combo)
        slayout.addRow(translations[self.language]['theme'], self.theme_combo)
        save_btn = QtWidgets.QPushButton(translations[self.language]['save'])
        save_btn.clicked.connect(self.save_settings)
        slayout.addRow(save_btn)
        self.stack.addWidget(self.settings_page)

        # Password Page
        self.pass_page = QtWidgets.QWidget()
        playout = QtWidgets.QVBoxLayout(self.pass_page)
        self.pass_btn = QtWidgets.QPushButton(translations[self.language]['change_password'])
        self.pass_btn.clicked.connect(self.change_password)
        playout.addWidget(self.pass_btn)
        self.stack.addWidget(self.pass_page)

        # dummy page for logout
        self.logout_page = QtWidgets.QWidget()
        self.stack.addWidget(self.logout_page)

        self.menu.setCurrentRow(0)
        self.load_vehicles()
        self.load_users()
        self.load_logs()
        self.update_home()

    def update_language(self):
        t = translations[self.language]
        self.menu.setItemText(0,t['home'])
        self.menu.setItemText(1,t['vehicles'])
        self.menu.setItemText(2,t['users'])
        self.menu.setItemText(3,t['logs'])
        self.menu.setItemText(4,t['settings'])
        self.menu.setItemText(5,t['change_password'])
        self.menu.setItemText(6,t['logout'])
        self.add_vehicle_btn.setText(t['add'])
        self.edit_vehicle_btn.setText(t['edit'])
        self.del_vehicle_btn.setText(t['delete'])
        self.vehicle_table.setHorizontalHeaderLabels([t['plate'],t['driver'],t['km'],t['last_maintenance']])
        self.user_table.setHorizontalHeaderLabels([t['username']])
        self.add_user_btn.setText(t['add'])
        self.lang_combo.setItemText(0,translations['tr']['turkish'])
        self.lang_combo.setItemText(1,translations['de']['german'])
        self.theme_combo.setItemText(0,t['light'])
        self.theme_combo.setItemText(1,t['dark'])
        self.home_label.setText(t['total_vehicles'].format(count=self.vehicle_table.rowCount()))
        self.pass_btn.setText(t['change_password'])
        self.setWindowTitle('Ara\u00e7 Takip')

    def apply_theme(self):
        if self.theme=='dark':
            self.setStyleSheet(DARK_STYLE)
        else:
            self.setStyleSheet(LIGHT_STYLE)

    def display_page(self, index):
        if index==6:  # logout
            self.close()
            add_log(self.username, 'logout')
            self.parent().show_login()
        else:
            self.stack.setCurrentIndex(index)
            if index==2 and self.username!='knkbau':
                QtWidgets.QMessageBox.warning(self, 'Yetki', 'Bu b\u00f6l\u00fcm sadece admin i\u00e7in')
                self.menu.setCurrentRow(0)
            if index==3 and self.username!='knkbau':
                QtWidgets.QMessageBox.warning(self, 'Yetki', 'Bu b\u00f6l\u00fcm sadece admin i\u00e7in')
                self.menu.setCurrentRow(0)

    def update_home(self):
        t = translations[self.language]
        self.home_label.setText(t['total_vehicles'].format(count=self.vehicle_table.rowCount()))

    def load_vehicles(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, plate, driver, km, last_maintenance FROM vehicles')
        rows = c.fetchall()
        conn.close()
        self.vehicle_table.setRowCount(0)
        for row in rows:
            r = self.vehicle_table.rowCount()
            self.vehicle_table.insertRow(r)
            for i,val in enumerate(row[1:]):
                item = QtWidgets.QTableWidgetItem(str(val))
                self.vehicle_table.setItem(r,i,item)
            self.vehicle_table.setRowHeight(r,20)
        self.update_home()

    def add_vehicle(self):
        dlg = VehicleDialog(self.language)
        if dlg.exec_():
            data = dlg.get_data()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT INTO vehicles(plate,driver,km,last_maintenance) VALUES (?,?,?,?)',
                      (data['plate'], data['driver'], data['km'], data['last_maintenance']))
            conn.commit()
            conn.close()
            add_log(self.username, f"Add vehicle {data['plate']}")
            self.load_vehicles()

    def edit_vehicle(self):
        row = self.vehicle_table.currentRow()
        if row<0:
            return
        plate = self.vehicle_table.item(row,0).text()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, plate, driver, km, last_maintenance FROM vehicles WHERE plate=?', (plate,))
        data = c.fetchone()
        conn.close()
        if not data:
            return
        dlg = VehicleDialog(self.language, {'plate':data[1],'driver':data[2],'km':data[3],'last_maintenance':data[4]})
        if dlg.exec_():
            nd = dlg.get_data()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('UPDATE vehicles SET plate=?,driver=?,km=?,last_maintenance=? WHERE id=?',
                      (nd['plate'], nd['driver'], nd['km'], nd['last_maintenance'], data[0]))
            conn.commit()
            conn.close()
            add_log(self.username, f"Edit vehicle {plate}")
            self.load_vehicles()

    def delete_vehicle(self):
        row = self.vehicle_table.currentRow()
        if row<0:
            return
        plate = self.vehicle_table.item(row,0).text()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM vehicles WHERE plate=?', (plate,))
        conn.commit()
        conn.close()
        add_log(self.username, f"Delete vehicle {plate}")
        self.load_vehicles()

    def load_users(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT username FROM users')
        rows = c.fetchall()
        conn.close()
        self.user_table.setRowCount(0)
        for row in rows:
            r = self.user_table.rowCount()
            self.user_table.insertRow(r)
            self.user_table.setItem(r,0,QtWidgets.QTableWidgetItem(row[0]))

    def add_user(self):
        if self.username!='knkbau':
            return
        dlg = UserDialog(self.language)
        if dlg.exec_():
            u,p = dlg.get_data()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute('INSERT INTO users(username,password) VALUES (?,?)', (u,p))
                conn.commit()
                add_log(self.username, f"Add user {u}")
            except sqlite3.IntegrityError:
                QtWidgets.QMessageBox.warning(self, 'Hata', translations[self.language]['user_exists'])
            conn.close()
            self.load_users()

    def load_logs(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT timestamp,user,action FROM logs ORDER BY id DESC')
        rows = c.fetchall()
        conn.close()
        self.log_table.setRowCount(0)
        for row in rows:
            r = self.log_table.rowCount()
            self.log_table.insertRow(r)
            for i,val in enumerate(row):
                self.log_table.setItem(r,i,QtWidgets.QTableWidgetItem(str(val)))

    def save_settings(self):
        lang = self.lang_combo.currentData()
        theme = self.theme_combo.currentData()
        set_setting('language', lang)
        set_setting('theme', theme)
        self.language = lang
        self.theme = theme
        self.update_language()
        self.apply_theme()

    def change_password(self):
        dlg = PasswordDialog(self.language)
        if dlg.exec_():
            cur, new, conf = dlg.get_data()
            if new!=conf:
                QtWidgets.QMessageBox.warning(self, 'Hata', translations[self.language]['incorrect_password'])
                return
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT password FROM users WHERE username=?', (self.username,))
            row = c.fetchone()
            if row and row[0]==cur:
                c.execute('UPDATE users SET password=? WHERE username=?', (new,self.username))
                conn.commit()
                QtWidgets.QMessageBox.information(self, 'Ok', translations[self.language]['password_changed'])
                add_log(self.username, 'change password')
            else:
                QtWidgets.QMessageBox.warning(self, 'Hata', translations[self.language]['incorrect_password'])
            conn.close()

    def show_login(self):
        # placeholder for restarting login from main window; this will be overridden
        pass


class App(QtWidgets.QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        init_db()
        self.main_win = None
        self.show_login()

    def show_login(self):
        language = get_setting('language')
        login = LoginDialog(language)
        while True:
            if login.exec_() == QtWidgets.QDialog.Accepted:
                username, password = login.get_credentials()
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
                row = c.fetchone()
                conn.close()
                if row:
                    add_log(username,'login')
                    self.main_win = MainWindow(username)
                    self.main_win.show_login = self.show_login
                    self.main_win.show()
                    break
                else:
                    QtWidgets.QMessageBox.warning(None,'Hata',translations[language]['login_failed'])
            else:
                sys.exit()


def main():
    app = App(sys.argv)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
