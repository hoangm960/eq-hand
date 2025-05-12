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

        self.initialized = False
        self.initialize_button.clicked.connect(self.start)
        # self.start()
    def start(self):
        if self.initialized:
            self.initialized = False
            return

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
            if not self.initialized:
                self.initialized = self.camera.initializeHandDetection(frame)
                if self.initialized:
                    self.initialize_button.setText("ReInitialize?")
            else:
                frame, freq_band, gain, volume, adjust_mode = self.camera.handDetection(
                    frame)

                if adjust_mode and self.activated_label.text() == "OFF":
                    self.activated_label.setText("ON")
                elif not adjust_mode and self.activated_label.text() == "ON":
                    self.activated_label.setText("OFF")

                if not freq_band in ["none", "toggle"]:
                    if freq_band == "all":
                        self.volume_slider.setValue(int(volume*100))
                    else:
                        UI_SLIDER_BANDS = {
                            "bass": self.low_gain_slider,
                            "mid": self.band_gain_slider,
                            "treble": self.high_gain_slider,
                        }
                        UI_SLIDER_BANDS[freq_band].setValue(int(-20 + (gain / 100.0) * 30))

            image = QImage(
                frame, frame.shape[1], frame.shape[0], QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.cam_display.setPixmap(pixmap)



if __name__ == '__main__':
    app = QApplication([])
    window = UI_Window()
    window.show()
