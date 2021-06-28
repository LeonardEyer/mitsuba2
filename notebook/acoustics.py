import numpy as np
import matplotlib.pyplot as plt
import scipy.integrate as igt

def EDC(rir, energy=False):
    """
    Die Abklingkurve jedes Oktavbands ist durch Rückwärts-Integration der quadrierten Impulsantwort zu erzeugen.
    Im Idealfall ohne Störpegel sollte die Integration am Ende der Impulsantwort beginnen und bis zum
    Anfang der quadrierten Impulsantwort laufen.
    """
    n = 2
    if energy:
         n = 1
    
    # Schroeder integration
    sch = np.cumsum(rir[::-1]**n)[::-1]
    sch_db = 10 * np.log10(sch / np.sum(rir**n))
    
    return sch_db

def T(n, edc, start=-5, poly=False, plot=False):
    """
    Zeit, die erforderlich ist, damit die räumlich gemittelte Schallenergiedichte in
    einem geschlossenen Raum um 60 dB sinkt, nachdem die Schallquelle abgeschaltet wurde.
    
    T kann basierend auf einem kürzeren Dynamikbereich als 60 dB ermittelt und auf eine Abklingzeit von
    60 dB extrapoliert werden. Sie wird dann entsprechend gekennzeichnet. So wird sie, wenn T aus der Zeit ermittelt wird, zu
    der die Abklingkurve erstmalig die Werte 5 dB und 25 dB unter dem Anfangspegel erreicht, mit T 20 , gekennzeichnet.
    Werden Abklingwerte von 5 dB bis 35 dB unter dem Anfangspegel verwendet, werden sie mit T 30 gekennzeichnet.
    
    n: in T_n
    x: Signal
    """
    rt60_from = np.argmax(edc < start)
    rt60_to = np.argmax(edc < -n+start)
    xp = np.linspace(rt60_from, rt60_to, rt60_to - rt60_from + 1)
    
    # Abklingrate bestimmen
    z = np.polyfit(xp, edc[rt60_from:rt60_to + 1], 1)
    
    if plot:
        plt.plot(xp, np.poly1d(z)(xp))
    
    if poly:
        return -60 / z[0], np.poly1d(z)
    else:
        return -60 / z[0]

def EDT(edc, **kwargs):
    """
    Die frühe Abklingzeit (en: early decay time (EDT)) muss (wie die herkömmliche Abklingzeit) aus der Neigung der
    integrierten Impulsantwort-Kurven ermittelt werden. Die Neigung der Abklingkurve sollte aus linearen
    Regressions-Geraden bester Anpassung aus den anfänglichen 10 dB (zwischen 0 dB und –10 dB) des
    Abklingvorgangs ermittelt werden. Die Abklingzeiten sollten aus der Steigung innerhalb der Zeit, die für einen
    60 dB–Abklingvorgang erforderlich ist, ermittelt werden
    """
    return T(10, edc, start=0, **kwargs)


def C(te, ir, fs=44100, energy=False):
    """
    C_te: eine Früh-zu-Spät-Index genannte Kennzahl;
    
    te = die frühe Zeitgrenze von entweder 50 ms oder 80 ms (C 80 wird üblicherweise „Klarheitsmaß“ genannt);
    rir = die Impulsantwort
    
    Es gibt zwar verschiedene Parameter, die in dieser Gruppe verwendet werden können, jedoch ist einer der ein-
    fachsten das Verhältnis des früh eintreffenden zum spät eintreffenden Energie-Anteil. Dieses kann entweder für
    eine Zeitgrenze der frühen Energie von 50 ms oder von 80 ms nach Gleichung (A.10) in dB berechnet werden,
    je nachdem, ob beabsichtigt ist, die Ergebnisse auf Bedingungen von Sprache bzw. von Musik zu beziehen.
    """
    
    n = 2
    if energy:
         n = 1
            
    # (A.10)
    t = int((te / 1000) * fs + 1)
    return 10 * np.log10(
        np.sum(ir[:t]**n) / np.sum(ir[t:]**n)
    )

def D50(rir, fs=44100, energy=False):
    """
    Es kann auch ein Verhältnis der früh eintreffenden zur Gesamt-Schallenergie gemessen werden. Bei-
    spielsweise wird D 50 („Tonschärfe“ oder „Deutlichkeit“) manchmal für Sprach-Bedingungen benutzt
    """
    n = 2
    if energy:
         n = 1
    # (A.11)
    t = int(0.050 * fs + 1)
    return np.sum(rir[:t]**n) / np.sum(rir**n)
