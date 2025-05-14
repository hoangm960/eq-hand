import numpy as np
from scipy import signal


class EQController:
    def __init__(self, fs,
                 low_cut=300.0, mid_center=2000.0, mid_bandwidth=800.0,
                 high_cut=10000, order=2,
                 limiter_threshold_db=-1.0, limiter_attack_ms=1.0, limiter_release_ms=100.0):
        self.fs = fs
        self.low_cut = low_cut
        self.mid_center = mid_center
        self.mid_bandwidth = mid_bandwidth
        self.high_cut = high_cut if high_cut is not None else mid_center + mid_bandwidth/2
        self.order = order
        # Limiter parameters
        self.limiter_enabled = True
        self.limiter_threshold = self.db_to_linear(limiter_threshold_db)
        # Attack/release coefficients
        self.attack_coeff = np.exp(-1.0 / (limiter_attack_ms * fs * 0.001))
        self.release_coeff = np.exp(-1.0 / (limiter_release_ms * fs * 0.001))
        # State variable for gain smoothing
        self._limiter_gain = 1.0
        # Default gains
        self.gain_low = 1.0
        self.gain_mid = 1.0
        self.gain_high = 1.0
        # Design initial filters
        self._design_filters()

    @staticmethod
    def db_to_linear(db):
        return 10 ** (db / 20.0)

    def _design_filters(self):
        low_edge = max(0.0, self.mid_center - self.mid_bandwidth/2)
        high_edge = min(self.fs/2, self.mid_center + self.mid_bandwidth/2)
        lc = np.clip(self.low_cut, 0.0, self.fs/2)
        hc = np.clip(self.high_cut, 0.0, self.fs/2)
        self.sos_low = signal.butter(
            self.order, lc, btype='low', fs=self.fs, output='sos')
        self.sos_mid = signal.butter(
            self.order, [low_edge, high_edge], btype='band', fs=self.fs, output='sos')
        self.sos_high = signal.butter(
            self.order, hc, btype='high', fs=self.fs, output='sos')

    def set_gain(self, low_db=0.0, mid_db=0.0, high_db=0.0):
        self.gain_low = self.db_to_linear(low_db)
        self.gain_mid = self.db_to_linear(mid_db)
        self.gain_high = self.db_to_linear(high_db)

    def set_low_cut(self, low_cut):
        self.low_cut = low_cut
        self._design_filters()

    def set_mid_bandwidth(self, mid_center=None, mid_bandwidth=None):
        if mid_center is not None:
            self.mid_center = mid_center
        if mid_bandwidth is not None:
            self.mid_bandwidth = mid_bandwidth
        self.high_cut = self.mid_center + self.mid_bandwidth/2
        self._design_filters()

    def set_high_cut(self, high_cut):
        self.high_cut = high_cut
        self._design_filters()

    def set_limiter(self, threshold_db=None, attack_ms=None, release_ms=None, enabled=None):
        if threshold_db is not None:
            self.limiter_threshold = self.db_to_linear(threshold_db)
        if attack_ms is not None:
            self.attack_coeff = np.exp(-1.0 / (attack_ms * self.fs * 0.001))
        if release_ms is not None:
            self.release_coeff = np.exp(-1.0 / (release_ms * self.fs * 0.001))
        if enabled is not None:
            self.limiter_enabled = enabled

    def _limit_sample(self, sample):
        # instantaneous peak level
        level = abs(sample)
        if level > self.limiter_threshold:
            target_gain = self.limiter_threshold / (level + 1e-15)
        else:
            target_gain = 1.0
        # smooth gain: attack (downward) vs release (upward)
        if target_gain < self._limiter_gain:
            coeff = self.attack_coeff
        else:
            coeff = self.release_coeff
        self._limiter_gain = coeff * \
            self._limiter_gain + (1 - coeff) * target_gain
        return sample * self._limiter_gain

    def process(self, x):
        x = np.asarray(x, dtype=np.float64)
        # EQ bands
        low = signal.sosfilt(self.sos_low, x)
        mid = signal.sosfilt(self.sos_mid, x)
        high = signal.sosfilt(self.sos_high, x)
        out = self.gain_low * low + self.gain_mid * mid + self.gain_high * high
        if not self.limiter_enabled:
            return out
        # apply limiter sample-by-sample
        y = np.zeros_like(out)
        for n, s in enumerate(out):
            y[n] = self._limit_sample(s)
        return y


if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.signal import sosfreqz

    # Create EQ controller instance
    eq_control = EQController(44100)

    fs = eq_control.fs  # Sampling frequency

    # Frequency axis for plotting (log scale for audio)
    w, h_low = sosfreqz(eq_control.sos_low, worN=2048, fs=fs)
    _, h_mid = sosfreqz(eq_control.sos_mid, worN=2048, fs=fs)
    _, h_high = sosfreqz(eq_control.sos_high, worN=2048, fs=fs)

    plt.figure(figsize=(10, 6))
    plt.semilogx(w, 20 * np.log10(np.abs(h_low)), label='Low Band')
    plt.semilogx(w, 20 * np.log10(np.abs(h_mid)), label='Mid Band')
    plt.semilogx(w, 20 * np.log10(np.abs(h_high)), label='High Band')

    plt.title('EQ Band Frequency Responses')
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Magnitude [dB]')
    plt.ylim((-20, 10))
    plt.grid(which='both', axis='both')
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Generate test sine waves at different frequencies
    duration = 1.0  # seconds
    t = np.linspace(0, duration, int(44100 * duration))

    # Test frequencies for low, mid, and high bands
    f_low = 100   # Hz
    f_mid = 2000  # Hz
    f_high = 5000  # Hz

    # Generate sine waves
    sine_low = np.sin(2 * np.pi * f_low * t)
    sine_mid = np.sin(2 * np.pi * f_mid * t)
    sine_high = np.sin(2 * np.pi * f_high * t)

    # Create subplots
    fig, axs = plt.subplots(3, 2, figsize=(15, 12))
    fig.suptitle('EQ Band Processing: Cut vs Boost')

    # Low band processing
    eq_control.set_gain(low_db=-12.0, mid_db=0.0, high_db=0.0)
    processed_cut_low = eq_control.process(sine_low)
    axs[0, 0].plot(t, sine_low, label='Original')
    axs[0, 0].plot(t, processed_cut_low, label='Processed')
    axs[0, 0].set_title('Low Band Cut (-12dB)')
    axs[0, 0].legend()
    axs[0, 0].grid(True)
    axs[0, 0].set_xlim(0.11, 0.15)

    eq_control.set_gain(low_db=12.0, mid_db=0.0, high_db=0.0)
    processed_boost_low = eq_control.process(sine_low)
    axs[0, 1].plot(t, sine_low, label='Original')
    axs[0, 1].plot(t, processed_boost_low, label='Processed')
    axs[0, 1].set_title('Low Band Boost (+12dB)')
    axs[0, 1].legend()
    axs[0, 1].grid(True)
    axs[0, 1].set_xlim(0.11, 0.15)

    # Mid band processing
    eq_control.set_gain(low_db=0.0, mid_db=-12.0, high_db=0.0)
    processed_cut_mid = eq_control.process(sine_mid)
    axs[1, 0].plot(t, sine_mid, label='Original')
    axs[1, 0].plot(t, processed_cut_mid, label='Processed')
    axs[1, 0].set_title('Mid Band Cut (-12dB)')
    axs[1, 0].legend()
    axs[1, 0].grid(True)
    axs[1, 0].set_xlim(0.111, 0.115)

    eq_control.set_gain(low_db=0.0, mid_db=12.0, high_db=0.0)
    processed_boost_mid = eq_control.process(sine_mid)
    axs[1, 1].plot(t, sine_mid, label='Original')
    axs[1, 1].plot(t, processed_boost_mid, label='Processed')
    axs[1, 1].set_title('Mid Band Boost (+12dB)')
    axs[1, 1].legend()
    axs[1, 1].grid(True)
    axs[1, 1].set_xlim(0.111, 0.115)

    # High band processing
    eq_control.set_gain(low_db=0.0, mid_db=0.0, high_db=-12.0)
    processed_cut_high = eq_control.process(sine_high)
    axs[2, 0].plot(t, sine_high, label='Original')
    axs[2, 0].plot(t, processed_cut_high, label='Processed')
    axs[2, 0].set_title('High Band Cut (-12dB)')
    axs[2, 0].legend()
    axs[2, 0].grid(True)
    axs[2, 0].set_xlim(0.1111, 0.1115)

    eq_control.set_gain(low_db=0.0, mid_db=0.0, high_db=12.0)
    processed_boost_high = eq_control.process(sine_high)
    axs[2, 1].plot(t, sine_high, label='Original')
    axs[2, 1].plot(t, processed_boost_high, label='Processed')
    axs[2, 1].set_title('High Band Boost (+12dB)')
    axs[2, 1].legend()
    axs[2, 1].grid(True)
    axs[2, 1].set_xlim(0.1111, 0.1115)

    plt.tight_layout()
    plt.show()