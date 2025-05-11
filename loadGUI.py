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

        self.timer.start(int(1000/24))

    def nextFrameSlot(self):
        frame = self.camera.read()
        if frame is not None:
            frame, freq_band, gain, volume = self.camera.hand_detection(frame)

            image = QImage(
                frame, frame.shape[1], frame.shape[0], QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.cam_display.setPixmap(pixmap)

            if freq_band == "none":
                return

            if freq_band == "toggle":
                self.active_checkbox.toggle()
                return

            if freq_band == "all":
                self.volume_slider.setValue(int(volume*100))
                return

            UI_SLIDER_BANDS = {
                "bass": self.low_gain_slider,
                "mid": self.band_gain_slider,
                "treble": self.high_gain_slider,
            }
            UI_SLIDER_BANDS[freq_band].setValue(int(-20 + (gain / 100.0) * 30))


if __name__ == '__main__':
    app = QApplication([])
    window = UI_Window()
    window.show()
