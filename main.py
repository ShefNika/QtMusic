import sys
import sqlite3
import re

from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize, QSortFilterProxyModel
import ui_main
import ui_song_dialog

'''
    Класс главного окна, для вывода таблицы плейлиста. Наследуется от QMainWindow.
    Поля:  
        ui - экземпляр интерфейса главного онка, созданный в designer
        model - модель данных для таблицы (экземпляр QStandartModel)
        proxy-model - прокси модель для сортировки и поиска (экземпляр QSortFilterProxyModel)
        conn - подключение к БД SQLite
        cursor - курсор для выполнения SQL-запросов
    '''
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = ui_main.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Музыкальный плейлист")
        self.model = QStandardItemModel(0, 4)
        self.model.setHorizontalHeaderLabels(["Превью", "Название", "Исполнитель", "Продолжительность"])

        self.proxy_model = QSortFilterProxyModel(self) # Для сортировки и поиска
        self.proxy_model.setSourceModel(self.model)  # Установка исходной модели
        self.proxy_model.setFilterKeyColumn(-1)  # Фильтр по всем столбцам (для поиска)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)  # Игнорирование регистра
        self.ui.songTable.setModel(self.proxy_model)  # Привязка прокси-модели к таблице (она над основной моделью)
        self.ui.songTable.setSortingEnabled(True)  # Включение сортировки по клику на заголовки

        self.ui.songTable.setColumnWidth(0, 70)
        self.ui.songTable.setIconSize(QSize(60, 60))
        self.ui.songTable.setColumnWidth(1, 210)
        self.ui.songTable.setColumnWidth(2, 210)
        self.ui.songTable.setColumnWidth(3, 152)
        self.ui.CreateButton.clicked.connect(self.create_song)
        self.ui.EditButton.clicked.connect(self.edit_song)
        self.ui.DeleteButton.clicked.connect(self.delete_song)
        self.ui.SaveButton.clicked.connect(self.save_data)
        self.ui.searchEdit.textChanged.connect(self.search_songs)
        self.init_database()
        self.load_data()

    '''Инициализация БД.'''
    def init_database(self) -> None:
        self.conn = sqlite3.connect('playlist.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS songs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        artist TEXT NOT NULL,
                        duration TEXT,
                        preview BLOB,
                        rating INTEGER
                    )
                ''')
        self.conn.commit()

    '''Поиск-фильтрация (по всем столбцам).'''
    def search_songs(self, text):
        self.proxy_model.setFilterWildcard(f"*{text}*")  # Фильтр по подстроке (+игнорирование регистра)

    '''Обновление строк в таблице (при создании или редактировании).'''
    def update_row(self, row, data) -> None:
        preview = QStandardItem()
        if isinstance(data['preview'], str) and data['preview']:
            with open(data['preview'], 'rb') as f:
                preview_data = f.read()
        elif isinstance(data['preview'], bytes):
            preview_data = data['preview']
        if preview_data:
            pixmap = QPixmap()
            pixmap.loadFromData(preview_data)
            pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            preview.setIcon(QIcon(pixmap))
        preview.setData(data['rating'], Qt.UserRole)
        preview.setData(preview_data, Qt.UserRole + 1)  # Сохраняем байты
        self.model.setItem(row, 0, preview)
        self.model.setItem(row, 1, QStandardItem(data['title']))
        self.model.setItem(row, 2, QStandardItem(data['artist']))
        self.model.setItem(row, 3, QStandardItem(data['duration']))

    '''Добавление новой строки (обработка нажатия кнопки "Создать").'''
    def create_song(self) -> None:
        dialog = SongDialog(self)
        if dialog.exec_() == QDialog.Accepted: #.exec() - отображает QDialog окно и возвращает закрытыие
            data = dialog.data
            row = self.model.rowCount()
            self.update_row(row, data)

    '''Редактирование строки (обработка нажатия кнопки "Редактировать").'''
    def edit_song(self):
        selected = self.ui.songTable.selectedIndexes()
        if selected:
            index = selected[0]
            row = self.proxy_model.mapToSource(index).row()
            cur_preview_data = self.model.item(row, 0).data(Qt.UserRole + 1)  # Текущие байты изображения
            data = {
                'title': self.model.item(row, 1).text(),
                'artist': self.model.item(row, 2).text(),
                'duration': self.model.item(row, 3).text(),
                'preview': cur_preview_data if isinstance(cur_preview_data, bytes) else '',
                'rating': self.model.item(row, 0).data(Qt.UserRole) or 1
            }
            dialog = SongDialog(self, data)
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.data
                if not data['preview'] or data['preview'] == '':
                    data['preview'] = cur_preview_data
                self.update_row(row, data)

    '''Удаление строки (обработка нажатия кнопки "Редактировать").'''
    def delete_song(self):
        selected = self.ui.songTable.selectedIndexes()
        if selected:
            index = selected[0]
            self.model.removeRow(self.proxy_model.mapToSource(index).row())

    '''Сохранение таблицы в БД (обработка нажатия кнопки "Сохранить").'''
    def save_data(self):
        self.cursor.execute('DELETE FROM songs')
        for row in range(self.model.rowCount()):
            title = self.model.item(row, 1).text()
            artist = self.model.item(row, 2).text()
            duration = self.model.item(row, 3).text()
            preview = self.model.item(row, 0).data(Qt.UserRole + 1)
            rating = self.model.item(row, 0).data(Qt.UserRole) or 1
            self.cursor.execute('INSERT INTO songs (title, artist, duration, preview, rating) VALUES (?, ?, ?, ?, ?)',
                                (title, artist, duration, sqlite3.Binary(preview), rating))
        self.conn.commit()
        QMessageBox.information(self, 'Сохранение', 'Данные успешно сохранены в playlist.db.')

    '''Загрузка данных в таблицу из БД при открытии.'''
    def load_data(self):
        self.model.removeRows(0, self.model.rowCount())
        self.cursor.execute('SELECT title, artist, duration, preview, rating FROM songs')
        for song in self.cursor.fetchall():
            row = self.model.rowCount()
            preview_item = QStandardItem()
            pixmap = QPixmap()
            pixmap.loadFromData(song[3])
            pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            preview_item.setIcon(QIcon(pixmap))
            preview_item.setData(song[4], Qt.UserRole)
            preview_item.setData(song[3], Qt.UserRole + 1)
            self.model.setItem(row, 0, preview_item)
            self.model.setItem(row, 1, QStandardItem(song[0]))
            self.model.setItem(row, 2, QStandardItem(song[1]))
            self.model.setItem(row, 3, QStandardItem(song[2]))

'''
    Класс диалогового окна для создания/редактирования строк таблицы.
    Наследуется от QDialog.
    Поля:
        ui - экземпляр интерфейса диалогового окна, созданного в designer
        data - словарь, для хранения данных о песне:
                                                    - Название (title)
                                                    - Исполнитель (Artist)
                                                    - Продолжительность (Duration)
                                                    - Превью (Preview)
                                                    - Оценка (Rating)
    '''
class SongDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.ui = ui_song_dialog.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.browseButton.clicked.connect(self.load_image)
        self.data = None
        if data:
            self.ui.titleEdit.setText(data['title'])
            self.ui.artistEdit.setText(data['artist'])
            self.ui.durationEdit.setText(data['duration'])
            self.ui.previewPathEdit.setText(data['preview']if isinstance(data['preview'], str) else '')
            self.ui.ratingSpin.setValue(data['rating'])

    '''Открывает диалог для выбора файла загрузки preview, записывает путь к файлу.'''
    def load_image(self):
        file = QFileDialog.getOpenFileName(self, "Выберите превью", "", "Images (*.png *.jpeg *.jpg)")[0]
        if file:
            self.ui.previewPathEdit.setText(file)

    '''Обработка кнопки "Ок" диалогового окна.'''
    def accept(self):
        if not self.ui.titleEdit.text() or not self.ui.artistEdit.text() or not self.ui.durationEdit.text() or not self.ui.ratingSpin.text():
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля: Название, Исполнитель, Продолжительность и Оценка")
            return
        if not re.match(r"^([0-5][0-9]):([0-5][0-9])$", self.ui.durationEdit.text()):
            QMessageBox.warning(self, "Ошибка", "Введите продолжительность в формате <мм:сс>")
            return
        self.data = {
            'title': self.ui.titleEdit.text(),
            'artist': self.ui.artistEdit.text(),
            'duration': self.ui.durationEdit.text(),
            'preview': self.ui.previewPathEdit.text(),
            'rating': self.ui.ratingSpin.value()
        }
        super().accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()