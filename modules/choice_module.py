import random
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QListWidget, QFrame
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from .storage import save_result, load_results, clear_module_history

class ChoiceReaction(QWidget):
    back_to_menu = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.shapes = ["⭕", "🔘", "🌑", "🌕", "⚫", "⚪"]
        self.target_shape = ""
        self.current_shape = ""
        self.results = []
        self.start_perf_time = 0
        self.is_active = False

        self.cycle_timer = QTimer()
        self.cycle_timer.timeout.connect(self.next_step)

        self.init_ui()
        self.load_history_from_file()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # 1. Панель настроек (верх)
        top_frame = QFrame()
        top_frame.setStyleSheet("background: #1a1a1a; border-radius: 10px; border: 1px solid #333;")
        top_layout = QHBoxLayout(top_frame)

        self.target_display = QLabel("ЦЕЛЬ: ---")
        self.target_display.setStyleSheet("color: #2491b3; font-weight: bold; font-size: 28px; border: none;")

        speed_label = QLabel("Смена (мс):")
        speed_label.setStyleSheet("color: #888; border: none; font-size: 14px;")
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(500, 15000)
        self.speed_spin.setValue(3000)
        self.speed_spin.setSingleStep(500)  # По умолчанию чуть быстрее для сложности
        self.speed_spin.setStyleSheet("background: #222; color: #2491b3; border: 1px solid #2491b3; border-radius: 5px; padding: 5px; font-size: 14px;")

        top_layout.addWidget(self.target_display)
        top_layout.addStretch()
        top_layout.addWidget(speed_label)
        top_layout.addWidget(self.speed_spin)

        # 2. Игровое окно (центр)
        self.screen = QPushButton("НАЖМИТЕ ДЛЯ СТАРТА")
        self.screen.setFixedHeight(270)
        self.screen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.screen.setStyleSheet(""" QPushButton { background-color: #1a1a1a; color: #2491b3; border: 2px solid #2491b3; border-radius: 15px; font-size: 40px; font-weight: bold;} """)
        self.screen.clicked.connect(self.handle_input)

        # 3. Информационный лейбл (подсказки)
        self.hint_label = QLabel("Нажмите СТАРТ, чтобы начать поиск")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("color: #888; font-size: 13px; font-style: italic; margin-bottom: 20px; margin-top: 20px; ")

        # 4. Панель статистики
        self.stats_label = QLabel("Последний: --- | Средний: ---")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet(""" font-size: 18px; color: white; font-weight: bold; background: #222; padding: 16px; border-radius: 5px; """)

        # 5. Окно истории
        history_layout = QVBoxLayout()
        history_header = QHBoxLayout()
        hist_title = QLabel("ИСТОРИЯ ПОПЫТОК:")
        hist_title.setStyleSheet("color: #2491b3; font-size: 12px; font-weight: bold;")

        self.clear_btn = QPushButton("Очистить историю результатов")
        self.clear_btn.setFixedSize(200, 30)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet(""" QPushButton { background-color: #333; color: #ff5555; border-radius: 4px; font-size: 10px; font-weight: bold; }
            QPushButton:hover { border: 1px solid #ff5555; } """)
        self.clear_btn.clicked.connect(self.clear_history)

        history_header.addWidget(hist_title)
        history_header.addStretch()
        history_header.addWidget(self.clear_btn)

        self.history_list = QListWidget()
        self.history_list.setFixedHeight(150)
        self.history_list.setStyleSheet(""" QListWidget { background-color: #1a1a1a; color: #2491b3; border: 1px solid #333; border-radius: 10px; padding: 5px;}
            QListWidget::item { border-bottom: 1px solid #222; padding: 3px; } """)

        history_layout.addLayout(history_header)
        history_layout.addWidget(self.history_list)

        # 6. Кнопка выхода
        self.back_btn = QPushButton("В ГЛАВНОЕ МЕНЮ")
        self.back_btn.setFixedSize(220, 40)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet(""" QPushButton { background-color: #333; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #444; border: 1px solid #2491b3; } """)
        self.back_btn.clicked.connect(self.back_to_menu_action)

        # Сборка слоев
        main_layout.addWidget(top_frame)
        main_layout.addWidget(self.screen)
        main_layout.addWidget(self.hint_label)
        main_layout.addWidget(self.stats_label)
        main_layout.addLayout(history_layout)
        main_layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)

    def handle_input(self):
        if not self.cycle_timer.isActive():
            self.start_session()
        elif self.is_active:
            self.check_reaction()

    def start_session(self):
        self.target_shape = random.choice(self.shapes)
        self.target_display.setText(f"ЦЕЛЬ: {self.target_shape}")
        self.screen.setText("...")
        self.screen.setStyleSheet("background-color: #111; border: 3px solid #444; color: #444; font-size: 120px;")
        self.hint_label.setText(f"Жмите только когда появится {self.target_shape}!")
        self.is_active = False
        self.cycle_timer.start(self.speed_spin.value())

    def next_step(self):
        # 25% шанс появления цели для усложнения ожидания
        if random.random() < 0.25:
            self.current_shape = self.target_shape
        else:
            self.current_shape = random.choice([s for s in self.shapes if s != self.target_shape])

        self.screen.setText(self.current_shape)
        self.screen.setStyleSheet( "background-color: #1a1a1a; border: 3px solid #2491b3; color: white; font-size: 120px;")
        self.start_perf_time = time.perf_counter()
        self.is_active = True

    def check_reaction(self):
        reaction = (time.perf_counter() - self.start_perf_time) * 1000
        if self.current_shape == self.target_shape:
            # УСПЕХ
            self.cycle_timer.stop()
            self.results.append(reaction)
            save_result("Реакция на выбор", reaction)

            avg = sum(self.results) / len(self.results)
            self.stats_label.setText(f"Последний: {reaction:.1f} мс | Средний: {avg:.1f} мс")
            self.history_list.insertItem(0, f"✅ {self.target_shape}: {reaction:.1f} мс")
            self.screen.setText("🎯")
            self.hint_label.setText("Попали! Нажмите на поле для нового поиска.")
            self.is_active = False
        else:
            # ОШИБКА
            self.trigger_error()

    def trigger_error(self):
        self.cycle_timer.stop()
        self.screen.setText("❌")
        self.screen.setStyleSheet("background-color: #500; color: white; border: 3px solid red; font-size: 120px;")
        self.history_list.insertItem(0, "❌ Ошибка (не та фигура)")
        self.hint_label.setText("Это была не цель! Попробуйте снова.")
        self.is_active = False

    def clear_history(self):
        self.results = []
        self.history_list.clear()
        self.stats_label.setText("Последний: --- | Средний: ---")
        clear_module_history("Реакция на выбор")

    def back_to_menu_action(self):
        self.cycle_timer.stop()
        self.back_to_menu.emit()

    def load_history_from_file(self):
        """Загружает данные из файла при запуске приложения"""
        saved_data = load_results("Реакция на выбор")

        for item in saved_data:
            reaction = item["reaction_ms"]
            date_str = item["date"]

            self.results.append(reaction)
            self.history_list.insertItem(0, f"💾 {date_str} - {reaction:.1f} мс")

        if self.results:
            avg = sum(self.results) / len(self.results)
            last = self.results[-1]
            self.stats_label.setText(f"Последний: {last:.1f} мс | Средний: {avg:.1f} мс")