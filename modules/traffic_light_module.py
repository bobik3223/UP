import random
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QListWidget
from PyQt6.QtCore import QTimer, Qt, pyqtSignal

from .storage import save_result, load_results, clear_module_history

class TrafficLight(QWidget):
    back_to_menu = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.min_interval = 500
        self.max_interval = 15000

        self.is_waiting = False
        self.is_active = False
        self.start_perf_time = 0
        self.results = []

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.activate_light)

        self.init_ui()
        self.load_history_from_file()

    def init_ui(self):
        # Основной вертикальный контейнер
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)  # Отступы между элементами

        # 1. Панель настроек (верх)
        settings_layout = QHBoxLayout()
        label_settings = QLabel("Макс. задержка (мс):")
        label_settings.setStyleSheet("color: #2491b3; font-weight: bold; font-size: 14px;")

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(500, 15000)
        self.interval_spin.setValue(3000)
        self.interval_spin.setSingleStep(500)
        self.interval_spin.setStyleSheet(""" QSpinBox { background-color: #222; color: #2491b3; border: 1px solid #2491b3;  border-radius: 5px; padding: 5px; font-size: 14px; } """)
        self.interval_spin.valueChanged.connect(self.update_settings)

        settings_layout.addWidget(label_settings)
        settings_layout.addWidget(self.interval_spin)
        settings_layout.addStretch()

        # 2. Игровое окно (центр)
        self.screen = QPushButton("НАЖМИТЕ ДЛЯ СТАРТА")
        self.screen.setFixedHeight(270)
        self.screen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.screen.setStyleSheet(""" QPushButton { background-color: #1a1a1a; color: #2491b3; border: 2px solid #2491b3; border-radius: 15px; font-size: 40px;font-weight: bold;}""")
        self.screen.clicked.connect(self.handle_click)

        # 3. Информационный лейбл (подсказки)
        self.hint_label = QLabel("Настройте время задержки и нажмите кнопку выше")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("color: #888; font-style: italic; font-size: 13px; margin-bottom: 20px; margin-top: 20px;")

        # 4. Панель статистики
        self.stats_label = QLabel("Последний: --- | Средний: ---")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet(""" font-size: 18px; color: white; font-weight: bold;  background: #222; padding: 16px; border-radius: 5px;  """)

        # 5. Окно истории
        history_layout = QVBoxLayout()
        header_layout = QHBoxLayout() # (заголовок + кнопка)
        history_title = QLabel("ИСТОРИЯ ПОПЫТОК:")
        history_title.setStyleSheet("color: #2491b3; font-size: 12px; font-weight: bold;")

        self.clear_btn = QPushButton("Очистить историю результатов")
        self.clear_btn.setFixedSize(200, 30)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet(""" QPushButton { background-color: #333; color: #ff5555; border-radius: 4px; font-size: 10px; font-weight: bold; }
            QPushButton:hover { border: 1px solid #ff5555; } """)
        self.clear_btn.clicked.connect(self.clear_history)

        header_layout.addWidget(history_title)
        # header_layout.addStretch()
        header_layout.addWidget(self.clear_btn)

        self.history_list = QListWidget()
        self.history_list.setFixedHeight(150)
        self.history_list.setStyleSheet(""" QListWidget { background-color: #1a1a1a; color: #2491b3; border: 1px solid #333; border-radius: 10px; padding: 5px;} """)
        history_layout.addLayout(header_layout)
        history_layout.addWidget(self.history_list)

        # 6. Кнопка выхода
        self.back_btn = QPushButton("В ГЛАВНОЕ МЕНЮ")
        self.back_btn.setFixedSize(220, 40)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet(""" QPushButton { background-color: #333; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #444; border: 1px solid #2491b3; } """)
        self.back_btn.clicked.connect(self.back_to_menu.emit)

        # Сборка слоев
        main_layout.addLayout(settings_layout)
        main_layout.addWidget(self.screen)
        main_layout.addWidget(self.hint_label)
        main_layout.addWidget(self.stats_label)
        main_layout.addLayout(history_layout)
        main_layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)

    # Логика работы
    def update_settings(self):
        self.max_interval = self.interval_spin.value()

    def handle_click(self):
        if not self.is_waiting and not self.is_active:
            self.start_waiting()
        elif self.is_waiting:
            self.trigger_false_start()
        elif self.is_active:
            self.finish_round()

    def start_waiting(self):
        self.is_waiting = True
        self.is_active = False
        self.screen.setText("ЖДИТЕ...")
        self.screen.setStyleSheet("background-color: #222; color: #444; border: 2px solid #444; font-size: 28px;")
        self.hint_label.setText("Приготовьтесь! Внимание на экран...")

        delay = random.randint(self.min_interval, self.max_interval)
        self.timer.start(delay)

    def activate_light(self):
        self.is_waiting = False
        self.is_active = True
        self.screen.setText("КЛИКАЙТЕ!")
        self.screen.setStyleSheet(
            "background-color: #2491b3; color: black; border: 3px solid white; font-size: 38px; font-weight: bold;")
        self.hint_label.setText("БЫСТРЕЕ!")
        self.start_perf_time = time.perf_counter()

    def trigger_false_start(self):
        self.timer.stop()
        self.is_waiting = False
        self.screen.setText("ФАЛЬСТАРТ!")
        self.screen.setStyleSheet("background-color: #770000; color: white; border: 2px solid red; font-size: 28px;")
        self.hint_label.setText("Слишком рано. Нажмите на экран, чтобы попробовать снова.")
        self.history_list.insertItem(0, "🔴 Фальстарт")

    def finish_round(self):
        reaction = (time.perf_counter() - self.start_perf_time) * 1000
        self.is_active = False
        self.results.append(reaction)
        save_result("Простая реакция", reaction)
        avg = sum(self.results) / len(self.results)

        res_text = f"{reaction:.1f} мс"
        self.screen.setText(res_text)
        self.screen.setStyleSheet( "background-color: #1a1a1a; color: #2491b3; border: 3px solid #2491b3; font-size: 38px;")
        self.stats_label.setText(f"Последний: {reaction:.1f} мс | Средний: {avg:.1f} мс")
        self.hint_label.setText("Отличный результат! Нажмите еще раз, чтобы продолжить сессию.")
        self.history_list.insertItem(0, f"🟢 Попытка {len(self.results)}: {res_text}")

    def clear_history(self):
        self.results = []
        self.history_list.clear()
        self.stats_label.setText("Последний: --- | Средний: ---")

        clear_module_history("Простая реакция")

        self.hint_label.setText("История очищена. Готовы к новому тесту?")
        self.screen.setText("НАЖМИТЕ ДЛЯ СТАРТА")
        self.screen.setStyleSheet(""" QPushButton { background-color: #1a1a1a; color: #2491b3; border: 2px solid #2491b3; border-radius: 15px; font-size: 26px; font-weight: bold; } """)

    def load_history_from_file(self):
        """Загружает данные из файла при запуске приложения"""
        saved_data = load_results("Простая реакция")

        for item in saved_data:
            reaction = item["reaction_ms"]
            date_str = item["date"]

            self.results.append(reaction)  # Добавляем в локальный массив для расчета среднего
            self.history_list.insertItem(0, f"💾 {date_str} - {reaction:.1f} мс")

        # Если данные загрузились, обновляем табло статистики
        if self.results:
            avg = sum(self.results) / len(self.results)
            last = self.results[-1]
            self.stats_label.setText(f"Последний: {last:.1f} мс | Средний: {avg:.1f} мс")