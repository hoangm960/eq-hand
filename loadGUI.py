from PyQt6 import uic
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt6.QtGui import QPixmap, QImage


class UI_Window(QMainWindow):

    def __init__(self, camera=None):
        super().__init__()
        uic.loadUi("GUI.ui", self)
        self.camera = camera
        # Create a timer.
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrameSlot)

        self.start()

    def start(self):
        if not self.camera.open():
            print('failure')
            msgBox = QMessageBox()
            msgBox.setText("Failed to open camera.")
            msgBox.exec_()
            return

        self.timer.start(30)

    def nextFrameSlot(self):
        frame = self.camera.read()
        if frame is not None:
            image = QImage(
                frame, frame.shape[1], frame.shape[0], QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.cam_display.setPixmap(pixmap)


if __name__ == '__main__':
    app = QApplication([])
    window = UI_Window()
    window.show()
