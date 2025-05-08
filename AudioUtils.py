from scipy.signal import butter, lfilter


def butter_bandpass(lowcut, highcut, fs, order=2):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    return butter(order, [low, high], btype='band')


def apply_eq(data, fs, gains):
    low_b, low_a = butter_bandpass(20, 250, fs)
    mid_b, mid_a = butter_bandpass(250, 4000, fs)
    high_b, high_a = butter_bandpass(4000, 18000, fs)

    low = lfilter(low_b, low_a, data) * gains['low']
    mid = lfilter(mid_b, mid_a, data) * gains['mid']
    high = lfilter(high_b, high_a, data) * gains['high']

    return low + mid + high
