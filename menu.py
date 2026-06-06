from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal

class ModuleCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, title, internal_name, icon_emoji):
        super().__init__()
        self.internal_name = internal_name
        self.setFixedSize(200, 270)

        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 2px solid #2491b3;
                border-radius: 15px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(10)

        self.img_label = QLabel(icon_emoji)
        self.img_label.setStyleSheet("font-size: 80px; border: none; background: transparent;")
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)

        self.select_btn = QPushButton("ВЫБРАТЬ")
        self.select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_btn.setStyleSheet(""" QPushButton { background-color: #333; color: white; font-weight: bold; border-radius: 8px; padding: 10px; font-size: 12px; border: 1px solid #444; }
            QPushButton:hover { background-color: #2491b3; color: black; border: 1px solid #2491b3; }
        """)
        self.select_btn.clicked.connect(lambda: self.clicked.emit(self.internal_name))

        layout.addWidget(self.img_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.select_btn)
        self.setLayout(layout)

class MenuWidget(QWidget):
    selected_module = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)

        header = QLabel("TRAINING REACTION")
        header.setStyleSheet("font-size: 36px; color: #2491b3; font-weight: bold; margin-bottom: 30px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        grid = QGridLayout()
        grid.setSpacing(70)

        # КАРТОЧКИ: Проверь internal_name у четвертой — теперь "sound"
        self.card1 = ModuleCard("Простая реакция (Светофор)", "traffic_light", "🚦")
        self.card2 = ModuleCard("Реакция на выбор (Фигуры)", "choice", "🎯")
        self.card3 = ModuleCard("Координация и слежение", "spatial", "🖱️")
        self.card4 = ModuleCard("Реакция на сложный выбор (Клавиатура)", "dual", "⌨️")

        self.card1.clicked.connect(self.selected_module.emit)
        self.card2.clicked.connect(self.selected_module.emit)
        self.card3.clicked.connect(self.selected_module.emit)
        self.card4.clicked.connect(self.selected_module.emit)

        grid.addWidget(self.card1, 0, 0)
        grid.addWidget(self.card2, 0, 1)
        grid.addWidget(self.card3, 1, 0)
        grid.addWidget(self.card4, 1, 1)

        layout.addLayout(grid)
        self.setLayout(layout)