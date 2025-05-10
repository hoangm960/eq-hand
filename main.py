from PyQt6.QtWidgets import QApplication
from loadGUI import UI_Window
from Camera import Camera

if __name__ == '__main__':

    camera = Camera(0)

    app = QApplication([])
    start_window = UI_Window(camera)
    start_window.show()
    app.exit(app.exec())
