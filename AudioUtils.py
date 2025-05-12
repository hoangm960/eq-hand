from scipy import signal


class ThreeBandEQ:
    def __init__(self, fs, low_cut=200.0, high_cut=2000.0, order=2):
        self.fs = fs
        self.low_cut = low_cut
        self.high_cut = high_cut
        self.order = order

        # Design filters as second-order-sections for stability
        # Low band: lowpass at low_cut
        self.sos_low = signal.butter(order, low_cut, btype='low', fs=fs, output='sos')
        # Mid band: bandpass between low_cut and high_cut
        self.sos_mid = signal.butter(order, [low_cut, high_cut], btype='band', fs=fs, output='sos')
        # High band: highpass at high_cut
        self.sos_high = signal.butter(order, high_cut, btype='high', fs=fs, output='sos')

        self.gain_low = 1.0
        self.gain_mid = 1.0
        self.gain_high = 1.0

    @staticmethod
    def db_to_linear(db):
        return 10 ** (db / 20.0)

    def set_gain(self, low_db=0.0, mid_db=0.0, high_db=0.0):
        self.gain_low = self.db_to_linear(low_db)
        self.gain_mid = self.db_to_linear(mid_db)
        self.gain_high = self.db_to_linear(high_db)

    def process(self, x):
        # Filter each band
        low = signal.sosfilt(self.sos_low, x)
        mid = signal.sosfilt(self.sos_mid, x)
        high = signal.sosfilt(self.sos_high, x)

        # Apply gains
        out = self.gain_low * low + self.gain_mid * mid + self.gain_high * high
        return out