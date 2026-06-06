import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget


# Импортируем все наши 5 модулей (файлов)
from menu import MenuWidget
from modules.traffic_light_module import TrafficLight
from modules.choice_module import ChoiceReaction
from modules.spatial_module import SpatialReaction
from modules.dual_module import DualReaction


class TrainingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Training Reaction")
        self.setMinimumSize(850, 750)
        self.setStyleSheet("background-color: #121212; color: white;")

        # Стек окон для переключения между меню и играми
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 1. Создаем экземпляры окон
        self.menu = MenuWidget()
        self.traffic_light_module = TrafficLight()
        self.choice_module = ChoiceReaction()
        self.spatial_module = SpatialReaction()
        self.dual_module = DualReaction()

        # 2. Добавляем в стек (важен индекс!)
        self.stacked_widget.addWidget(self.menu)  # Индекс 0
        self.stacked_widget.addWidget(self.traffic_light_module)  # Индекс 1
        self.stacked_widget.addWidget(self.choice_module)  # Индекс 2
        self.stacked_widget.addWidget(self.spatial_module)  # Индекс 3
        self.stacked_widget.addWidget(self.dual_module)  # Индекс 4

        # 3. ПОДКЛЮЧЕНИЕ СИГНАЛОВ
        # Сигнал из меню (передает имя игры)
        self.menu.selected_module.connect(self.switch_screen)

        # Сигналы "Назад" из каждой игры
        self.traffic_light_module.back_to_menu.connect(self.go_to_menu)
        self.choice_module.back_to_menu.connect(self.go_to_menu)
        self.spatial_module.back_to_menu.connect(self.go_to_menu)
        self.dual_module.back_to_menu.connect(self.go_to_menu)

    def switch_screen(self, name):
        """Переключение на экран игры по её кодовому имени"""
        if name == "traffic_light":
            self.stacked_widget.setCurrentIndex(1)
        elif name == "choice":
            self.stacked_widget.setCurrentIndex(2)
        elif name == "spatial":
            self.stacked_widget.setCurrentIndex(3)
        elif name == "dual":
            self.stacked_widget.setCurrentIndex(4)

    def go_to_menu(self):
        """Возврат на главный экран"""
        self.stacked_widget.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TrainingApp()
    window.show()
    sys.exit(app.exec())