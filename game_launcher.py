import sys
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, 
                             QLabel, QLineEdit, QFileDialog, QScrollArea, QFrame, QMessageBox, QHBoxLayout,
                             QSizePolicy, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from models import Session, Game
from sqlalchemy.exc import IntegrityError
import subprocess
import os
import ctypes

ICON = "MAINICON-20240501.ico"
INVITE = "https://www.discord.gg/k5HBFXqtCB"

class GameScanner(QThread):
    progress_updated = pyqtSignal(int)
    games_found = pyqtSignal(list)

    def run(self):
        common_dirs = [
            "C:/Program Files",
            "C:/Program Files (x86)",
            "C:/Games",
            "D:/Games"
        ]
        total_files = sum(len(files) for dir in common_dirs for _, _, files in os.walk(dir))
        progress = 0
        found_games = []
        for dir in common_dirs:
            for root, _, files in os.walk(dir):
                for file in files:
                    if file.endswith(".exe"):
                        found_games.append({"name": file, "path": os.path.join(root, file)})
                    progress += 1
                    percentage = int(progress / total_files * 100)
                    self.progress_updated.emit(percentage)  # Emit progress signal
        self.games_found.emit(found_games)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Launcher")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(ICON))  # Add an application icon

        self.session = Session()
        
        self.initUI()
        self.load_games()
        
        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)
        self.progress_bar.setVisible(False)

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(20)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search games...")
        self.search_bar.textChanged.connect(self.search_games)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
                border: 1px solid #ccc;
                background-color: #f9f9f9;
            }
        """)
        self.layout.addWidget(self.search_bar)

        self.buttons_layout = QHBoxLayout()

        self.add_game_btn = QPushButton("Add Game")
        self.add_game_btn.clicked.connect(self.add_game)
        self.add_game_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 16px;
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
        """)
        self.buttons_layout.addWidget(self.add_game_btn)

        self.scan_games_btn = QPushButton("Scan for Games")
        self.scan_games_btn.clicked.connect(self.scan_for_games)
        self.scan_games_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 16px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.buttons_layout.addWidget(self.scan_games_btn)

        self.clear_games_btn = QPushButton("Clear Games")
        self.clear_games_btn.clicked.connect(self.clear_games)
        self.clear_games_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 16px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.buttons_layout.addWidget(self.clear_games_btn)

        self.help_btn = QPushButton("Help")
        self.help_btn.clicked.connect(self.open_discord_server)
        self.help_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 16px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #484e54;
            }
        """)
        self.buttons_layout.addWidget(self.help_btn)

        self.layout.addLayout(self.buttons_layout)

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)
        self.progress_bar.setVisible(False)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #2c2c2c; border: none;")
        self.layout.addWidget(self.scroll_area)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_area.setWidget(self.scroll_content)

    def load_games(self):
        games = self.session.query(Game).all()
        self.display_games(games)

    def display_games(self, games):
        for i in reversed(range(self.scroll_layout.count())): 
            widget_to_remove = self.scroll_layout.itemAt(i).widget()
            if widget_to_remove:
                self.scroll_layout.removeWidget(widget_to_remove)
                widget_to_remove.setParent(None)

        row_layout = QHBoxLayout()
        for game in games:
            game_frame = QFrame()
            game_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            game_layout = QVBoxLayout(game_frame)
            game_frame.setStyleSheet("""
                QFrame {
                    background-color: #404040;
                    border-radius: 10px;
                    padding: 10px;
                    margin: 5px;
                }
            """)

            # Placeholder for game icons, replace with actual icon paths if available
            game_icon = QLabel()
            pixmap = QPixmap(ICON)  # Default icon for games
            pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            game_icon.setPixmap(pixmap)
            game_layout.addWidget(game_icon)

            game_name_label = QLabel(game.name)
            game_name_label.setStyleSheet("color: white; font-size: 18px;")
            game_layout.addWidget(game_name_label)

            game_button = QPushButton("Launch")
            game_button.clicked.connect(lambda _, path=game.path: self.launch_game(path))
            game_button.setStyleSheet("""
                QPushButton {
                    padding: 5px 10px;
                    font-size: 14px;
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
            game_layout.addWidget(game_button)

            row_layout.addWidget(game_frame)
            if row_layout.count() == 2:
                self.scroll_layout.addLayout(row_layout)
                row_layout = QHBoxLayout()

        if row_layout.count() > 0:
            self.scroll_layout.addLayout(row_layout)

    def add_game(self):
        name, _ = QFileDialog.getOpenFileName(self, "Select Game Executable", "", "Executables (*.exe)")
        if name:
            game_name = os.path.basename(name)
            new_game = Game(name=game_name, path=name)
            self.session.add(new_game)
            try:
                self.session.commit()
            except IntegrityError:
                self.session.rollback()
                messagebox = QMessageBox()
                messagebox.setText(f"The game {game_name} is already added.")
                messagebox.exec()
            self.load_games()

    def launch_game(self, path):
        try:
            if self.is_admin():
                subprocess.Popen(path)
            else:
                self.request_elevation_and_launch(path)
        except Exception as e:
            messagebox = QMessageBox()
            messagebox.setText(f"Failed to launch game: {e}")
            messagebox.exec()

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def request_elevation_and_launch(self, path):
        try:
            # Request elevation to run the game executable directly
            ctypes.windll.shell32.ShellExecuteW(None, "runas", path, None, None, 1)
        except Exception as e:
            messagebox = QMessageBox()
            messagebox.setText(f"Failed to request elevation: {e}")
            messagebox.exec()

    def search_games(self, text):
        games = self.session.query(Game).filter(Game.name.contains(text)).all()
        self.display_games(games)

    def scan_for_games(self):
        self.game_scanner = GameScanner()
        self.game_scanner.progress_updated.connect(self.update_progress_bar)  # Connect progress signal
        self.game_scanner.games_found.connect(self.add_found_games)
        self.progress_bar.setVisible(True)  # Make progress bar visible before scanning starts
        self.game_scanner.start()

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)
        if value == 100:
            self.progress_bar.setVisible(False)

    def add_found_games(self, games):
        for game in games:
            new_game = Game(name=game["name"], path=game["path"])
            self.session.add(new_game)
            try:
                self.session.commit()
            except IntegrityError:
                self.session.rollback()
        self.load_games()

    def clear_games(self):
        confirmation = QMessageBox.question(self, "Confirmation", "Are you sure you want to clear all games?",
                                            QMessageBox.Yes | QMessageBox.No)
        if confirmation == QMessageBox.Yes:
            self.session.query(Game).delete()
            self.session.commit()
            self.load_games()
            app.exit()  # Exit the current instance of the application
            os.execv(sys.executable, [sys.executable] + sys.argv)  # Restart the application



    def open_discord_server(self):
        webbrowser.open(INVITE)

    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
