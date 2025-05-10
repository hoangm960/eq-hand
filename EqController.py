class EQController:
    def __init__(self):
        self.gains = {'bass': 0.5, 'mid': 0.5, 'treble': 0.5}
        self.selected_band = 'mid'

    def set_band(self, band):
        self.selected_band = band

    def set_gain(self, gain):
        self.gains[self.selected_band] = gain

    def get_gains(self):
        return self.gains

    def get_selected_band(self):
        return self.selected_band
