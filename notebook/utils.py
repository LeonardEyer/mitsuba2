import numpy as np
import matplotlib.pyplot as plt

SOUND_SPEED = 343
LIGHT_SPEED = 3 * 10**8


def fractionalOctaves(frac=3, f=(25, 20_000)):

    """

    Calculate fractional octave frequencies according to [1]_.

    Parameters

    ----------

    frac : int, optional

        Defines the setpwith, e.g., 3=third octaces and 1=octaves.

        The default is 3.

    f : tuple or list with two elements, optional

        Minimum and maximum center frequency in Hz to be calculated.

        The default is (25,20_000).

    fs : int, optional

        Sampling rate in Hz. The default is 44100.

    Returns

    -------

    f_c : numpy array

        Exact center frequencies in Hz ([1]_ Eq. 2-3).

    f_low : numpy array

        Exact lower cut-off frequencies in Hz ([1]_ Eq. 4).

    f_up : numpy array

        Exact upper cut-off frequencies in Hz ([1]_ Eq. 5).

    f_nominal : list with N elements

        Nominal center frequencies according to [1]_ Table E.1. Exact

        center frequencies are kept if nominal frequency is not specified.

    References

    ----------

    .. [1] IEC 61260-1, Octave-band and fractional-octave-band filters.

           Part 1: Specifications, 2014.

    """

    # frac. oct. center frequencies for a wide range (IEC 61260-1 Eq. 1-2)

    # (yields frequencies between 1 Hz and 40 kHz for frac = 24)

    if frac % 2:

        f_c = (10**(3/10)) ** (np.arange(-250, 130)/frac) * 1000

    else:

        f_c = (10**(3/10)) ** ((2*np.arange(-250, 130)+1)/(2*frac)) * 1000

    # restict the range of center frequencies according to f (add a search

    # margin to make sure that nominal frequencies can be querried)

    fMin = (10**(3/10)) ** (-1/(2*frac)) * min(f)

    fMax = (10**(3/10)) ** (1/(2*frac)) * max(f)

    f_c = f_c[np.where(np.logical_and(f_c >= fMin, f_c <= fMax))]

    # upper and lower cut-off frequencies  IEC 61260-1 Eq. 4-5)

    f_low = (10**(3/10)) ** (-1/(2*frac)) * f_c

    f_up = (10**(3/10)) ** (1/(2*frac)) * f_c

    # discard cut-off freq. is < 0

    idx = np.where(f_low > 0)[0][0]

    f_c = f_c[idx:]

    f_low = f_low[idx:]

    f_up = f_up[idx:]

    # nominal center frequencies (IEC 61260-1 Table E.1)

    tmp = [25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400,

           500, 630, 800, 1_000, 1_250, 1_600, 2_000, 2_500, 3_150, 4_000,

           5_000, 6_300, 8_000, 10_000, 12_500, 16_000, 20_000]

    # copy list of exact frequencies

    f_nominal = f_c.copy()

    for n, f in enumerate(f_nominal):

        # check if the current nominal frequency is included in f_c by

        # searching for differences smaller than quater the bandwidth

        delta = np.abs(f-tmp).min()

        bw4 = f_c[n] - f_low[n]

        if delta < bw4:

            f_nominal[n] = tmp[np.argmin(np.abs(f-tmp))]

    return f_c, f_low, f_up, f_nominal


def get_vals(hist):
    return np.array(hist.data(), copy=False).reshape([hist.time_step_count(), hist.bin_count()])


def wav_to_freq(wav, sound_speed=SOUND_SPEED):
    return sound_speed / wav


def plot_spectogram(hist, bins=None):
    vals = np.flip(get_vals(hist))
    
    wav_range = hist.wav_range()
    time_range = hist.time_range()
    
    freq_range = wav_to_freq(np.array(wav_range))
    
    if bins is None:
        yticks = np.linspace(freq_range[1], freq_range[0], min(10, hist.bin_count()))
    else:
        yticks = bins
    
    yticks = [f'{tick:,.0f}' for tick in yticks]
    xticks = np.linspace(time_range[0], time_range[1], min(6, hist.time_step_count()))
    
    
    plt.figure(figsize=(15, 5))
    plt.imshow(vals.transpose(), cmap='inferno', interpolation='nearest', aspect='auto', vmin=0)
    
    cbar = plt.colorbar()
    cbar.set_label("Energy")
    plt.xlabel("Time [s]")
    plt.ylabel("Frequency [Hz]")
    plt.yticks(np.linspace(0, hist.bin_count() - 1, min(10, hist.bin_count())), yticks)
    plt.xticks(np.linspace(0, hist.time_step_count() - 1, min(6, hist.time_step_count())), xticks)
    plt.gca().invert_yaxis()
    
    
def plot_bin_hist(values, n_bins):
    
    unique, counts = np.unique(values, return_counts=True)
    
    counts_padded = np.zeros(shape=(n_bins))
    unique_padded = np.arange(0, n_bins)
    counts_padded[unique] = counts
    
    print(dict(zip(unique_padded, counts_padded)))
    plt.bar(unique_padded, counts_padded)