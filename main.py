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
        'min_amount': 'Min Tutar',
        'max_amount': 'Max Tutar',
        'start_date': 'Başlangıç',
        'end_date': 'Bitiş',
        'save': 'Kaydet',
        'cancel': 'İptal',
        'language': 'Dil',
        'turkish': 'Türkçe',
        'german': 'Deutsch',
        'no_worker': 'Lütfen işçi seçin.',
        'error': 'Hata',
        'edit': 'Düzenle',
        'delete': 'Sil',
        'confirm_delete': 'Silmek istediğinize emin misiniz?',
        'pdf': 'PDF Oluştur'
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
        'min_amount': 'Min Betrag',
        'max_amount': 'Max Betrag',
        'start_date': 'Von',
        'end_date': 'Bis',
        'save': 'Speichern',
        'cancel': 'Abbrechen',
        'language': 'Sprache',
        'turkish': 'Türkisch',
        'german': 'Deutsch',
        'no_worker': 'Bitte Arbeiter wählen.',
        'error': 'Fehler',
        'edit': 'Bearbeiten',
        'delete': 'Löschen',
        'confirm_delete': 'Sind Sie sicher, dass Sie löschen möchten?',
        'pdf': 'PDF Erstellen'
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


class ClickableLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class PhotoDialog(QtWidgets.QDialog):
    def __init__(self, path):
        super().__init__()
        self.setWindowTitle('Foto')
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel()
        pix = QtGui.QPixmap(path)
        label.setPixmap(pix.scaled(800, 600, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        layout.addWidget(label)


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
        self.preview = QtWidgets.QLabel()
        self.preview.setFixedSize(120, 120)
        self.preview.setStyleSheet('border:1px solid gray;')
        self.preview.setAlignment(QtCore.Qt.AlignCenter)
        layout.addRow(translations[lang]['name'], self.first)
        layout.addRow(translations[lang]['surname'], self.last)
        layout.addRow(self.photo_btn)
        layout.addRow(self.preview)
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def select_photo(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, translations[self.lang]['select_photo'], '', 'Images (*.png *.jpg *.jpeg)')
        if path:
            self.path = path
            self.photo_btn.setText(os.path.basename(path))
            pix = QtGui.QPixmap(path).scaled(120, 120, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.preview.setPixmap(pix)

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
        self.min_amount = QtWidgets.QDoubleSpinBox()
        self.min_amount.setMaximum(1e9)
        self.min_amount.valueChanged.connect(self.filter_workers)
        self.max_amount = QtWidgets.QDoubleSpinBox()
        self.max_amount.setMaximum(1e9)
        self.max_amount.valueChanged.connect(self.filter_workers)
        self.start_date = QtWidgets.QDateEdit(QtCore.QDate.currentDate().addYears(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.dateChanged.connect(self.filter_workers)
        self.end_date = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.dateChanged.connect(self.filter_workers)
        self.worker_list = QtWidgets.QListWidget()
        self.worker_list.currentRowChanged.connect(self.display_worker)
        self.add_worker_btn = QtWidgets.QPushButton()
        self.add_worker_btn.clicked.connect(self.add_worker)
        left.addWidget(self.search)
        left.addWidget(self.min_amount)
        left.addWidget(self.max_amount)
        left.addWidget(self.start_date)
        left.addWidget(self.end_date)
        left.addWidget(self.worker_list)
        left.addWidget(self.add_worker_btn)
        h.addLayout(left, 1)
        # Right panel
        right = QtWidgets.QVBoxLayout()
        self.photo = ClickableLabel()
        self.photo.setFixedSize(200,200)
        self.photo.setStyleSheet('border:1px solid gray;')
        self.photo.setAlignment(QtCore.Qt.AlignCenter)
        self.photo.clicked.connect(self.show_full_photo)
        self.name_label = QtWidgets.QLabel()
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.penalty_table = QtWidgets.QTableWidget(0,2)
        self.penalty_table.setHorizontalHeaderLabels(['', ''])
        self.penalty_table.horizontalHeader().setStretchLastSection(True)
        self.penalty_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.penalty_table.customContextMenuRequested.connect(self.penalty_menu)
        self.add_penalty_btn = QtWidgets.QPushButton()
        self.add_penalty_btn.clicked.connect(self.add_penalty)
        self.pdf_btn = QtWidgets.QPushButton()
        self.pdf_btn.clicked.connect(self.generate_pdf)
        right.addWidget(self.photo)
        right.addWidget(self.name_label)
        right.addWidget(self.penalty_table)
        right.addWidget(self.add_penalty_btn)
        right.addWidget(self.pdf_btn)
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
        self.min_amount.setPrefix(t['min_amount'] + ': ')
        self.max_amount.setPrefix(t['max_amount'] + ': ')
        self.start_date.setDisplayFormat('yyyy-MM-dd')
        self.start_date.setToolTip(t['start_date'])
        self.end_date.setDisplayFormat('yyyy-MM-dd')
        self.end_date.setToolTip(t['end_date'])
        self.add_worker_btn.setText(t['add_worker'])
        self.add_penalty_btn.setText(t['add_penalty'])
        self.pdf_btn.setText(t['pdf'])
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
        self.filter_workers()

    def filter_workers(self, *args):
        text = self.search.text().lower()
        min_amt = self.min_amount.value()
        max_amt = self.max_amount.value() if self.max_amount.value() > 0 else 1e9
        start = self.start_date.date().toString('yyyy-MM-dd')
        end = self.end_date.date().toString('yyyy-MM-dd')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for i in range(self.worker_list.count()):
            item = self.worker_list.item(i)
            wid = item.data(QtCore.Qt.UserRole)
            name_match = text in item.text().lower()
            c.execute('''SELECT 1 FROM penalties WHERE worker_id=? AND amount>=? AND amount<=? AND date>=? AND date<=? LIMIT 1''',
                      (wid, min_amt, max_amt, start, end))
            has_penalty = bool(c.fetchone()) or (min_amt == 0 and max_amt == 1e9)
            item.setHidden(not (name_match and has_penalty))
        conn.close()

    def display_worker(self, index):
        if index < 0:
            self.current_worker = None
            self.photo_path = ''
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
            self.photo_path = photo if photo else ''
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
        c.execute('SELECT id, amount, date FROM penalties WHERE worker_id=? ORDER BY id DESC', (wid,))
        rows = c.fetchall()
        conn.close()
        self.penalty_table.setRowCount(0)
        for pid, amt, date in rows:
            r = self.penalty_table.rowCount()
            self.penalty_table.insertRow(r)
            item_amt = QtWidgets.QTableWidgetItem(str(amt))
            item_amt.setData(QtCore.Qt.UserRole, pid)
            self.penalty_table.setItem(r,0, item_amt)
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
                img = QtGui.QImage(path)
                if not img.isNull():
                    img = img.scaled(500, 300, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                    img.save(filename)
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

    def penalty_menu(self, pos):
        index = self.penalty_table.indexAt(pos)
        if not index.isValid():
            return
        menu = QtWidgets.QMenu()
        t = translations[self.lang]
        edit_act = menu.addAction(t['edit'])
        del_act = menu.addAction(t['delete'])
        action = menu.exec_(self.penalty_table.mapToGlobal(pos))
        row = index.row()
        if action == edit_act:
            self.edit_penalty(row)
        elif action == del_act:
            self.delete_penalty(row)

    def edit_penalty(self, row):
        item = self.penalty_table.item(row, 0)
        if not item:
            return
        pid = item.data(QtCore.Qt.UserRole)
        amount = float(item.text())
        date_text = self.penalty_table.item(row, 1).text()
        dlg = PenaltyDialog(self.lang)
        dlg.amount.setValue(amount)
        dlg.date.setDate(QtCore.QDate.fromString(date_text, 'yyyy-MM-dd'))
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            new_amt, new_date = dlg.get_data()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('UPDATE penalties SET amount=?, date=? WHERE id=?', (new_amt, new_date, pid))
            conn.commit()
            conn.close()
            self.load_penalties(self.current_worker)

    def delete_penalty(self, row):
        item = self.penalty_table.item(row, 0)
        if not item:
            return
        pid = item.data(QtCore.Qt.UserRole)
        if QtWidgets.QMessageBox.question(self, translations[self.lang]['delete'], translations[self.lang]['confirm_delete']) == QtWidgets.QMessageBox.Yes:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('DELETE FROM penalties WHERE id=?', (pid,))
            conn.commit()
            conn.close()
            self.load_penalties(self.current_worker)

    def show_full_photo(self):
        if hasattr(self, 'photo_path') and self.photo_path and os.path.exists(self.photo_path):
            PhotoDialog(self.photo_path).exec_()

    def generate_pdf(self):
        if self.current_worker is None:
            QtWidgets.QMessageBox.warning(self, translations[self.lang]['error'], translations[self.lang]['no_worker'])
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT first_name,last_name FROM workers WHERE id=?', (self.current_worker,))
        fname, lname = c.fetchone()
        c.execute('SELECT amount, date FROM penalties WHERE worker_id=? ORDER BY date', (self.current_worker,))
        rows = c.fetchall()
        conn.close()
        total = sum(r[0] for r in rows)
        filename = f'rapor_{fname}_{lname}.pdf'
        writer = QtGui.QPdfWriter(filename)
        painter = QtGui.QPainter(writer)
        y = 40
        painter.setFont(QtGui.QFont('Arial', 16))
        painter.drawText(100, y, f'{fname} {lname}')
        y += 30
        painter.setFont(QtGui.QFont('Arial', 12))
        for amt, date in rows:
            painter.drawText(100, y, f'{amt:.2f} - {date}')
            y += 20
        y += 20
        painter.drawText(100, y, f'Total: {total:.2f}')
        painter.end()
        QtWidgets.QMessageBox.information(self, 'PDF', filename)


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
