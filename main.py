import os
import sys
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets

DB_PATH = 'workers.db'
IMAGE_DIR = 'images'

translations = {
    'tr': {
        'title': 'Ceza Takip Sistemi',
        'search': 'Ara...',
        'add_worker': 'Yeni İşçi Ekle',
        'add_penalty': 'Ceza Ekle',
        'name': 'Ad',
        'surname': 'Soyad',
        'select_photo': 'Fotoğraf Seç',
        'amount': 'Tutar',
        'date': 'Tarih',
        'save': 'Kaydet',
        'cancel': 'İptal',
        'language': 'Dil',
        'turkish': 'Türkçe',
        'german': 'Deutsch',
        'no_worker': 'Lütfen işçi seçin.',
        'error': 'Hata'
    },
    'de': {
        'title': 'Bußgeld Verfolgungssystem',
        'search': 'Suchen...',
        'add_worker': 'Neuer Arbeiter',
        'add_penalty': 'Bußgeld hinzufügen',
        'name': 'Name',
        'surname': 'Nachname',
        'select_photo': 'Foto auswählen',
        'amount': 'Betrag',
        'date': 'Datum',
        'save': 'Speichern',
        'cancel': 'Abbrechen',
        'language': 'Sprache',
        'turkish': 'Türkisch',
        'german': 'Deutsch',
        'no_worker': 'Bitte Arbeiter wählen.',
        'error': 'Fehler'
    }
}


def init_db():
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS workers(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT,
                    last_name TEXT,
                    photo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS penalties(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_id INTEGER,
                    amount REAL,
                    date TEXT,
                    FOREIGN KEY(worker_id) REFERENCES workers(id))''')
    conn.commit()
    conn.close()


class WorkerDialog(QtWidgets.QDialog):
    def __init__(self, lang):
        super().__init__()
        self.lang = lang
        self.path = ''
        self.setWindowTitle(translations[lang]['add_worker'])
        layout = QtWidgets.QFormLayout(self)
        self.first = QtWidgets.QLineEdit()
        self.last = QtWidgets.QLineEdit()
        self.photo_btn = QtWidgets.QPushButton(translations[lang]['select_photo'])
        self.photo_btn.clicked.connect(self.select_photo)
        layout.addRow(translations[lang]['name'], self.first)
        layout.addRow(translations[lang]['surname'], self.last)
        layout.addRow(self.photo_btn)
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def select_photo(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, translations[self.lang]['select_photo'], '', 'Images (*.png *.jpg *.jpeg)')
        if path:
            self.path = path
            self.photo_btn.setText(os.path.basename(path))

    def get_data(self):
        return self.first.text(), self.last.text(), self.path


class PenaltyDialog(QtWidgets.QDialog):
    def __init__(self, lang):
        super().__init__()
        self.lang = lang
        self.setWindowTitle(translations[lang]['add_penalty'])
        layout = QtWidgets.QFormLayout(self)
        self.amount = QtWidgets.QDoubleSpinBox()
        self.amount.setMaximum(1e9)
        self.date = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.date.setCalendarPopup(True)
        layout.addRow(translations[lang]['amount'], self.amount)
        layout.addRow(translations[lang]['date'], self.date)
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_data(self):
        return self.amount.value(), self.date.date().toString('yyyy-MM-dd')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = 'tr'
        self.current_worker = None
        self.setWindowTitle(translations[self.lang]['title'])
        self.resize(800, 500)
        self.setup_ui()
        self.load_workers()
        self.update_texts()

    def setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        h = QtWidgets.QHBoxLayout(central)
        # Left panel
        left = QtWidgets.QVBoxLayout()
        self.search = QtWidgets.QLineEdit()
        self.search.textChanged.connect(self.filter_workers)
        self.worker_list = QtWidgets.QListWidget()
        self.worker_list.currentRowChanged.connect(self.display_worker)
        self.add_worker_btn = QtWidgets.QPushButton()
        self.add_worker_btn.clicked.connect(self.add_worker)
        left.addWidget(self.search)
        left.addWidget(self.worker_list)
        left.addWidget(self.add_worker_btn)
        h.addLayout(left, 1)
        # Right panel
        right = QtWidgets.QVBoxLayout()
        self.photo = QtWidgets.QLabel()
        self.photo.setFixedSize(200,200)
        self.photo.setStyleSheet('border:1px solid gray;')
        self.photo.setAlignment(QtCore.Qt.AlignCenter)
        self.name_label = QtWidgets.QLabel()
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.penalty_table = QtWidgets.QTableWidget(0,2)
        self.penalty_table.setHorizontalHeaderLabels(['', ''])
        self.penalty_table.horizontalHeader().setStretchLastSection(True)
        self.add_penalty_btn = QtWidgets.QPushButton()
        self.add_penalty_btn.clicked.connect(self.add_penalty)
        right.addWidget(self.photo)
        right.addWidget(self.name_label)
        right.addWidget(self.penalty_table)
        right.addWidget(self.add_penalty_btn)
        h.addLayout(right, 2)
        # Menu
        lang_menu = self.menuBar().addMenu(translations[self.lang]['language'])
        self.tr_action = lang_menu.addAction(translations['tr']['turkish'])
        self.de_action = lang_menu.addAction(translations['de']['german'])
        self.tr_action.triggered.connect(lambda: self.set_language('tr'))
        self.de_action.triggered.connect(lambda: self.set_language('de'))

    def set_language(self, lang):
        self.lang = lang
        self.update_texts()

    def update_texts(self):
        t = translations[self.lang]
        self.setWindowTitle(t['title'])
        self.search.setPlaceholderText(t['search'])
        self.add_worker_btn.setText(t['add_worker'])
        self.add_penalty_btn.setText(t['add_penalty'])
        self.penalty_table.setHorizontalHeaderLabels([t['amount'], t['date']])
        self.menuBar().clear()
        lang_menu = self.menuBar().addMenu(t['language'])
        self.tr_action = lang_menu.addAction(translations['tr']['turkish'])
        self.de_action = lang_menu.addAction(translations['de']['german'])
        self.tr_action.triggered.connect(lambda: self.set_language('tr'))
        self.de_action.triggered.connect(lambda: self.set_language('de'))
        # refresh list names and penalty labels
        for i in range(self.worker_list.count()):
            item = self.worker_list.item(i)
            item.setText(item.data(QtCore.Qt.UserRole + 1))
        self.display_worker(self.worker_list.currentRow())

    def load_workers(self):
        self.worker_list.clear()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, first_name, last_name FROM workers')
        for wid, f, l in c.fetchall():
            item = QtWidgets.QListWidgetItem(f'{f} {l}')
            item.setData(QtCore.Qt.UserRole, wid)
            item.setData(QtCore.Qt.UserRole + 1, f'{f} {l}')
            self.worker_list.addItem(item)
        conn.close()
        self.filter_workers(self.search.text())

    def filter_workers(self, text):
        text = text.lower()
        for i in range(self.worker_list.count()):
            item = self.worker_list.item(i)
            item.setHidden(text not in item.text().lower())

    def display_worker(self, index):
        if index < 0:
            self.current_worker = None
            self.photo.clear()
            self.name_label.clear()
            self.penalty_table.setRowCount(0)
            return
        item = self.worker_list.item(index)
        wid = item.data(QtCore.Qt.UserRole)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT first_name,last_name,photo FROM workers WHERE id=?', (wid,))
        row = c.fetchone()
        if row:
            self.current_worker = wid
            fname, lname, photo = row
            self.name_label.setText(f'{fname} {lname}')
            if photo and os.path.exists(photo):
                pix = QtGui.QPixmap(photo).scaled(200,200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                self.photo.setPixmap(pix)
            else:
                self.photo.clear()
            self.load_penalties(wid)
        conn.close()

    def load_penalties(self, wid):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT amount, date FROM penalties WHERE worker_id=? ORDER BY id DESC', (wid,))
        rows = c.fetchall()
        conn.close()
        self.penalty_table.setRowCount(0)
        for amt, date in rows:
            r = self.penalty_table.rowCount()
            self.penalty_table.insertRow(r)
            self.penalty_table.setItem(r,0, QtWidgets.QTableWidgetItem(str(amt)))
            self.penalty_table.setItem(r,1, QtWidgets.QTableWidgetItem(date))

    def add_worker(self):
        dlg = WorkerDialog(self.lang)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            first, last, path = dlg.get_data()
            if path:
                filename = os.path.join(IMAGE_DIR, os.path.basename(path))
                base, ext = os.path.splitext(filename)
                i = 1
                while os.path.exists(filename):
                    filename = f"{base}_{i}{ext}"
                    i += 1
                QtGui.QImage(path).save(filename)
            else:
                filename = ''
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT INTO workers(first_name,last_name,photo) VALUES (?,?,?)', (first,last,filename))
            conn.commit()
            conn.close()
            self.load_workers()

    def add_penalty(self):
        if self.current_worker is None:
            QtWidgets.QMessageBox.warning(self, translations[self.lang]['error'], translations[self.lang]['no_worker'])
            return
        dlg = PenaltyDialog(self.lang)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            amount, date = dlg.get_data()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT INTO penalties(worker_id,amount,date) VALUES (?,?,?)', (self.current_worker, amount, date))
            conn.commit()
            conn.close()
            self.load_penalties(self.current_worker)


def main():
    init_db()
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    font = QtGui.QFont('Arial', 10)
    app.setFont(font)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
