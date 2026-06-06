import random
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QListWidget, QSpinBox
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from .storage import save_result, load_results, clear_module_history

class DualReaction(QWidget):
    back_to_menu = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.results = []
        self.is_active = False  # Горит ли сейчас вспышка
        self.is_running = False  # Запущен ли бесконечный цикл игры
        self.start_perf_time = 0
        self.target_side = ""

        # Таймер для задержки появления вспышки
        self.stimulus_timer = QTimer()
        self.stimulus_timer.setSingleShot(True)
        self.stimulus_timer.timeout.connect(self.activate_stimulus)

        # Таймер для паузы МЕЖДУ раундами (чтобы результаты не слипались)
        self.next_round_timer = QTimer()
        self.next_round_timer.setSingleShot(True)
        self.next_round_timer.timeout.connect(self.start_new_attempt)

        self.init_ui()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.load_history_from_file()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # 1. ПАНЕЛЬ НАСТРОЕК
        settings_layout = QHBoxLayout()
        label_delay = QLabel("Макс. задержка (мс):")
        label_delay.setStyleSheet("color: #2491b3; font-weight: bold; font-size: 14px;")

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1000, 10000)
        self.interval_spin.setValue(3000)
        self.interval_spin.setSingleStep(500)
        self.interval_spin.setStyleSheet(""" QSpinBox { background-color: #222; color: #2491b3; border: 1px solid #2491b3; border-radius: 5px; padding: 5px; font-size: 14px; } """)

        settings_layout.addWidget(label_delay)
        settings_layout.addWidget(self.interval_spin)
        settings_layout.addStretch()

        # 2. ИНСТРУКЦИЯ
        self.info_label = QLabel("Нажми СТАРТ и используй стрелочки ⇽ (влево) и ⇾ (вправо)")
        self.info_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 3. ИГРОВЫЕ ЗОНЫ
        field_layout = QHBoxLayout()
        self.left_zone = QFrame()
        self.left_zone.setFixedSize(380, 280)
        self.left_zone.setStyleSheet("background-color: #1a1a1a; border: 2px solid #333; border-radius: 15px;")

        self.right_zone = QFrame()
        self.right_zone.setFixedSize(380, 280)
        self.right_zone.setStyleSheet("background-color: #1a1a1a; border: 2px solid #333; border-radius: 15px;")

        field_layout.addWidget(self.left_zone)
        field_layout.addWidget(self.right_zone)

        # 4. КНОПКА УПРАВЛЕНИЯ (СТАРТ/СТОП)
        self.action_btn = QPushButton("СТАРТ ТРЕНИРОВКИ")
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.setStyleSheet(""" QPushButton {  background-color: #2491b3; color: black; font-weight: bold; font-size: 18px; border-radius: 5px; padding: 10px; }
                QPushButton:hover { background-color: #4aa0ba; } """)
        self.action_btn.clicked.connect(self.toggle_game)

        # 5. СТАТИСТИКА И ИСТОРИЯ
        self.stats_label = QLabel("Последний: --- | Средний: ---")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet( "font-size: 18px; color: white; font-weight: bold; background: #222; padding: 10px; border-radius: 5px;" )

        # Блок истории (Заголовок, кнопка очистки и список)
        history_layout = QVBoxLayout()
        history_header = QHBoxLayout()

        history_title = QLabel("ИСТОРИЯ ПОПЫТОК:")
        history_title.setStyleSheet("color: #2491b3; font-weight:bold; font-size: 14px")

        self.clear_btn = QPushButton("Очистить историю результатов")
        self.clear_btn.setFixedSize(200, 30)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet(""" QPushButton { background-color: #333; color: #ff5555; border-radius: 4px; font-size: 10px; font-weight: bold;}
                QPushButton:hover { border: 1px solid #ff5555; } """)
        self.clear_btn.clicked.connect(self.clear_history)

        history_header.addWidget(history_title)
        history_header.addStretch()
        history_header.addWidget(self.clear_btn)

        self.history_list = QListWidget()
        self.history_list.setFixedHeight(120)
        self.history_list.setStyleSheet( "background-color: #1a1a1a; color: #2491b3; border: 1px solid #333; border-radius: 10px; padding: 5px;" )

        history_layout.addLayout(history_header)
        history_layout.addWidget(self.history_list)

        # 6. ВЫХОД
        self.back_btn = QPushButton("В ГЛАВНОЕ МЕНЮ")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setFixedSize(220, 40)
        self.back_btn.setStyleSheet(""" QPushButton {background-color: #333; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #444; border: 1px solid #2491b3; } """)
        self.back_btn.clicked.connect(self.back_to_menu.emit)

        main_layout.addLayout(settings_layout)
        main_layout.addWidget(self.info_label)
        main_layout.addLayout(field_layout)
        main_layout.addWidget(self.action_btn)
        main_layout.addWidget(self.stats_label)
        main_layout.addLayout(history_layout)
        main_layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)

    def toggle_game(self):
        if not self.is_running:
            self.is_running = True
            self.action_btn.setText("СТОП")
            self.action_btn.setStyleSheet( "background-color: #ff5555; color: white; font-weight: bold; border-radius: 5px; padding: 10px; font-size: 18px;" )
            self.start_new_attempt()
        else:
            self.stop_game()

    def stop_game(self):
        self.is_running = False
        self.is_active = False
        self.stimulus_timer.stop()
        self.next_round_timer.stop()
        self.action_btn.setText("СТАРТ ТРЕНИРОВКИ")
        self.action_btn.setStyleSheet(""" QPushButton { background-color: #2491b3; color: black; border-radius: 5px; padding: 10px; font-size: 18px; font-weight: bold; }
            QPushButton:hover { background-color: #4aa0ba; } """)
        self.reset_zones()
        self.info_label.setText("Тест остановлен.")

    def start_new_attempt(self):
        if not self.is_running: return
        self.is_active = False
        self.reset_zones()
        self.info_label.setText("Приготовьтесь...")

        # Задержка перед вспышкой из настроек
        delay = random.randint(1000, self.interval_spin.value())
        self.stimulus_timer.start(delay)
        self.setFocus()

    def activate_stimulus(self):
        if not self.is_running: return
        self.is_active = True
        self.target_side = random.choice(["left", "right"])
        self.start_perf_time = time.perf_counter()

        if self.target_side == "left":
            self.left_zone.setStyleSheet("background-color: #2491b3; border: 4px solid white; border-radius: 15px;")
            self.info_label.setText("<<< ЛЕВО")
        else:
            self.right_zone.setStyleSheet("background-color: #2491b3; border: 4px solid white; border-radius: 15px;")
            self.info_label.setText("ПРАВО >>>")

    def keyPressEvent(self, event):
        if not self.is_running: return

        # Обработка фальстарта
        if not self.is_active:
            if event.key() in [Qt.Key.Key_Left, Qt.Key.Key_Right]:
                self.handle_error("ФАЛЬСТАРТ!")
            return

        reaction = (time.perf_counter() - self.start_perf_time) * 1000

        # Проверка правильности нажатия
        if event.key() == Qt.Key.Key_Left and self.target_side == "left":
            self.record_success(reaction, "Лево")
        elif event.key() == Qt.Key.Key_Right and self.target_side == "right":
            self.record_success(reaction, "Право")
        elif event.key() in [Qt.Key.Key_Left, Qt.Key.Key_Right]:
            self.handle_error("ОШИБКА СТОРОНЫ!")

    def record_success(self, reaction, side):
        self.is_active = False
        self.results.append(reaction)

        save_result("Реакция на сложный выбор", reaction)
        avg = sum(self.results) / len(self.results)

        self.stats_label.setText(f"Последний: {reaction:.1f} мс | Средний: {avg:.1f} мс")
        self.history_list.insertItem(0, f"✅ {side}: {reaction:.1f} мс")
        self.info_label.setText(f"Отлично! ({reaction:.0f} мс)")

        # Подсвечиваем зеленым на мгновение
        color = "#155a15"
        if side == "Лево":
            self.left_zone.setStyleSheet(f"background-color: {color}; border-radius: 15px;")
        else:
            self.right_zone.setStyleSheet(f"background-color: {color}; border-radius: 15px;")

        # Запускаем следующий раунд через 1 секунду
        self.next_round_timer.start(1000)

    def handle_error(self, msg):
        self.is_active = False
        self.stimulus_timer.stop()
        self.info_label.setText(msg)
        self.left_zone.setStyleSheet("background-color: #700; border: 2px solid red; border-radius: 15px;")
        self.right_zone.setStyleSheet("background-color: #700; border: 2px solid red; border-radius: 15px;")
        self.history_list.insertItem(0, f"❌ {msg}")
        # Пауза перед перезапуском после ошибки
        self.next_round_timer.start(1500)

    def reset_zones(self):
        self.left_zone.setStyleSheet("background-color: #1a1a1a; border: 2px solid #333; border-radius: 15px;")
        self.right_zone.setStyleSheet("background-color: #1a1a1a; border: 2px solid #333; border-radius: 15px;")

    def clear_history(self):
        self.results = []
        self.history_list.clear()
        self.stats_label.setText("Последний: --- | Средний: ---")
        self.info_label.setText("История очищена. Можно продолжать.")
        self.setFocus()
        clear_module_history("Реакция на сложный выбор")

    def load_history_from_file(self):
        """Загружает данные из файла при запуске приложения"""
        saved_data = load_results("Реакция на сложный выбор")

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