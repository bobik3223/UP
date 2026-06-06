import random
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QFrame
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from .storage import save_result, load_results, clear_module_history

class SpatialReaction(QWidget):
    back_to_menu = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.results = []
        self.start_perf_time = 0
        self.is_active = False  # Видна ли мишень сейчас
        self.is_running = False  # Запущен ли процесс тренировки вообще

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.spawn_target)

        self.init_ui()
        self.load_history_from_file()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # 1. Заголовок
        header_layout = QHBoxLayout()
        self.info_label = QLabel("Нажмите СТАРТ для начала тренировки")
        self.info_label.setStyleSheet("color: #2491b3; font-weight: bold; font-size: 15px;")
        header_layout.addWidget(self.info_label)
        main_layout.addLayout(header_layout)

        # 2. Игровая область (пустая, без кнопок внутри)
        self.game_field = QFrame()
        self.game_field.setFixedSize(900, 350)
        self.game_field.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #2491b3;
                border-radius: 10px;
            }
        """)
        # Мишень (скрыта по умолчанию)
        self.target = QPushButton("🎯", self.game_field)
        self.target.setFixedSize(50, 50)
        self.target.setCursor(Qt.CursorShape.CrossCursor)
        self.target.hide()
        self.target.setStyleSheet(""" QPushButton { background-color: #2491b3; color: white; border-radius: 25px; font-size: 22px; border: 2px solid white; }
            QPushButton:hover { background-color: #2eb8e6; } """)
        self.target.clicked.connect(self.handle_target_click)
        main_layout.addWidget(self.game_field, alignment=Qt.AlignmentFlag.AlignCenter)

        # 3. Единая кнопка управления СТАРТ / СТОП
        self.control_btn = QPushButton("СТАРТ ТРЕНИРОВКИ")
        self.control_btn.setFixedHeight(45)
        self.control_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Стиль по умолчанию (СТАРТ)
        self.control_btn.setStyleSheet(""" QPushButton { background-color: #2491b3; color: #1a1a1a; border-radius: 10px; font-size: 18px; font-weight: bold; }
            QPushButton:hover { background-color: #4aa0ba; } """)
        self.control_btn.clicked.connect(self.toggle_session)
        main_layout.addWidget(self.control_btn)

        # 4. Панель статистики
        self.stats_label = QLabel("Последний: --- | Средний: ---")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("font-size: 18px; color: white; font-weight: bold; background: #222; padding: 10px; border-radius: 5px;")
        main_layout.addWidget(self.stats_label)

        # 5. Кнопка очистки (Справа)
        history_layout = QVBoxLayout()
        history_header = QHBoxLayout()

        history_title = QLabel("ИСТОРИЯ ПОПЫТОК:")
        history_title.setStyleSheet("color: #2491b3; font-weight:bold; font-size: 14px")

        self.clear_btn = QPushButton("Очистить историю результатов")
        self.clear_btn.setFixedSize(200, 30)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet(""" QPushButton { background-color: #333; color: #ff5555; border-radius: 4px; font-size: 10px; font-weight: bold; }
            QPushButton:hover { border: 1px solid #ff5555; } """)
        self.clear_btn.clicked.connect(self.clear_history)

        history_header.addWidget(history_title)
        history_header.addStretch()
        history_header.addWidget(self.clear_btn)

        # 6. Список истории
        self.history_list = QListWidget()
        self.history_list.setFixedHeight(120)
        self.history_list.setStyleSheet("background-color: #1a1a1a; color: #2491b3; border: 1px solid #333; border-radius: 10px;")

        history_layout.addLayout(history_header)
        history_layout.addWidget(self.history_list)
        main_layout.addLayout(history_layout)

        # 7. Навигация
        self.back_btn = QPushButton("В ГЛАВНОЕ МЕНЮ")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setFixedSize(220, 40)
        self.back_btn.setStyleSheet(""" QPushButton {background-color: #333; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #444; border: 1px solid #2491b3; } """)
        self.back_btn.clicked.connect(self.back_to_menu.emit)
        main_layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)

    def toggle_session(self):
        # Переключение между режимами Старт и Стоп
        if not self.is_running:
            self.is_running = True # Запуск
            self.control_btn.setText("СТОП ТРЕНИРОВКА")
            self.control_btn.setStyleSheet(""" QPushButton { background-color: #ff5555; color: white; border-radius: 10px; font-size: 18px; font-weight: bold; } """)
            self.info_label.setText("Приготовьтесь...")
            self.prepare_next_target()
        else:
            # Остановка (стиль СТАРТ из dual_module)
            self.is_running = False
            self.control_btn.setText("СТАРТ ТРЕНИРОВКИ")
            self.control_btn.setStyleSheet(""" QPushButton { background-color: #2491b3; color: #1a1a1a; border-radius: 10px; font-size: 18px; font-weight: bold; }
                QPushButton:hover { background-color: #4aa0ba; } """)
            self.timer.stop()
            self.target.hide()
            self.is_active = False
            self.info_label.setText("Тренировка приостановлена")

    def prepare_next_target(self):
        if self.is_running:
            delay = random.randint(1000, 2500)
            self.timer.start(delay)

    def spawn_target(self):
        if not self.is_running:
            return

        max_x = self.game_field.width() - self.target.width() - 10
        max_y = self.game_field.height() - self.target.height() - 10

        new_x = random.randint(10, max_x)
        new_y = random.randint(10, max_y)

        self.target.move(new_x, new_y)
        self.target.show()
        self.info_label.setText("ЛОВИ!")
        self.start_perf_time = time.perf_counter()
        self.is_active = True

    def handle_target_click(self):
        if self.is_active and self.is_running:
            reaction = (time.perf_counter() - self.start_perf_time) * 1000
            self.is_active = False
            self.target.hide()

            self.results.append(reaction)
            save_result("Координация и слежение", reaction)

            avg = sum(self.results) / len(self.results)
            self.history_list.insertItem(0, f"🎯 Попадание: {reaction:.1f} мс")
            self.stats_label.setText(f"Последний: {reaction:.1f} мс | Средний: {avg:.1f} мс")

            # Сразу зацикливаем, пока нажата кнопка СТОП
            self.prepare_next_target()

    def clear_history(self):
        self.results = []
        self.history_list.clear()
        self.stats_label.setText("Последний: --- | Средний: ---")
        self.info_label.setText("История очищена")
        clear_module_history("Координация и слежение")

    def load_history_from_file(self):
        """Загружает данные из файла при запуске приложения"""
        saved_data = load_results("Координация и слежение")

        for item in saved_data:
            reaction = item["reaction_ms"]
            date_str = item["date"]

            self.results.append(reaction)
            self.history_list.insertItem(0, f"💾 {date_str} - {reaction:.1f} мс")

        if self.results:
            avg = sum(self.results) / len(self.results)
            last = self.results[-1]
            self.stats_label.setText(f"Последний: {last:.1f} мс | Средний: {avg:.1f} мс")