# Moon phase astronomy for the /moon-phases/ page (build_site.py).
#
# Instants of the principal phases (new moon, first quarter, full moon, last
# quarter) from Jean Meeus, "Astronomical Algorithms" ch. 49 (accurate to well
# under a minute), and the Sun's apparent longitude (ch. 25, low precision) for
# the zodiac sign the Moon is in at each phase. docs/moon.js computes the
# Moon's continuous position in the browser and reads the phase instants
# baked from here.
#
# Python 3.7+ , standard library only.
import datetime
import math

# Phase codes, also used by docs/moon.js: 0 new, 1 first quarter, 2 full,
# 3 last quarter.
NEW, FIRST, FULL, LAST = range(4)

UNIX_EPOCH_JD = 2440587.5
# TT - UT in days (~69 s in the 2020s; the error is a few seconds per decade).
DELTA_T = 69.0 / 86400


def _sin(deg):
    return math.sin(math.radians(deg))


def _cos(deg):
    return math.cos(math.radians(deg))


# (coefficient, E power, M, M', F, Ω) multipliers of each periodic term.
_NEW_TERMS = (
    (-0.40720, 0, 0, 1, 0, 0), (0.17241, 1, 1, 0, 0, 0), (0.01608, 0, 0, 2, 0, 0),
    (0.01039, 0, 0, 0, 2, 0), (0.00739, 1, -1, 1, 0, 0), (-0.00514, 1, 1, 1, 0, 0),
    (0.00208, 2, 2, 0, 0, 0), (-0.00111, 0, 0, 1, -2, 0), (-0.00057, 0, 0, 1, 2, 0),
    (0.00056, 1, 1, 2, 0, 0), (-0.00042, 0, 0, 3, 0, 0), (0.00042, 1, 1, 0, 2, 0),
    (0.00038, 1, 1, 0, -2, 0), (-0.00024, 1, -1, 2, 0, 0), (-0.00017, 0, 0, 0, 0, 1),
    (-0.00007, 0, 2, 1, 0, 0), (0.00004, 0, 0, 2, -2, 0), (0.00004, 0, 3, 0, 0, 0),
    (0.00003, 0, 1, 1, -2, 0), (0.00003, 0, 0, 2, 2, 0), (-0.00003, 0, 1, 1, 2, 0),
    (0.00003, 0, -1, 1, 2, 0), (-0.00002, 0, -1, 1, -2, 0), (-0.00002, 0, 1, 3, 0, 0),
    (0.00002, 0, 0, 4, 0, 0),
)
_FULL_TERMS = (
    (-0.40614, 0, 0, 1, 0, 0), (0.17302, 1, 1, 0, 0, 0), (0.01614, 0, 0, 2, 0, 0),
    (0.01043, 0, 0, 0, 2, 0), (0.00734, 1, -1, 1, 0, 0), (-0.00515, 1, 1, 1, 0, 0),
    (0.00209, 2, 2, 0, 0, 0), (-0.00111, 0, 0, 1, -2, 0), (-0.00057, 0, 0, 1, 2, 0),
    (0.00056, 1, 1, 2, 0, 0), (-0.00042, 0, 0, 3, 0, 0), (0.00042, 1, 1, 0, 2, 0),
    (0.00038, 1, 1, 0, -2, 0), (-0.00024, 1, -1, 2, 0, 0), (-0.00017, 0, 0, 0, 0, 1),
    (-0.00007, 0, 2, 1, 0, 0), (0.00004, 0, 0, 2, -2, 0), (0.00004, 0, 3, 0, 0, 0),
    (0.00003, 0, 1, 1, -2, 0), (0.00003, 0, 0, 2, 2, 0), (-0.00003, 0, 1, 1, 2, 0),
    (0.00003, 0, -1, 1, 2, 0), (-0.00002, 0, -1, 1, -2, 0), (-0.00002, 0, 1, 3, 0, 0),
    (0.00002, 0, 0, 4, 0, 0),
)
_QUARTER_TERMS = (
    (-0.62801, 0, 0, 1, 0, 0), (0.17172, 1, 1, 0, 0, 0), (-0.01183, 1, 1, 1, 0, 0),
    (0.00862, 0, 0, 2, 0, 0), (0.00804, 0, 0, 0, 2, 0), (0.00454, 1, -1, 1, 0, 0),
    (0.00204, 2, 2, 0, 0, 0), (-0.00180, 0, 0, 1, -2, 0), (-0.00070, 0, 0, 1, 2, 0),
    (-0.00040, 0, 0, 3, 0, 0), (-0.00034, 1, -1, 2, 0, 0), (0.00032, 1, 1, 0, 2, 0),
    (0.00032, 1, 1, 0, -2, 0), (-0.00028, 2, 2, 1, 0, 0), (0.00027, 1, 1, 2, 0, 0),
    (-0.00017, 0, 0, 0, 0, 1), (-0.00005, 0, -1, 1, -2, 0), (0.00004, 0, 0, 2, 2, 0),
    (-0.00004, 0, 1, 1, 2, 0), (0.00004, 0, -2, 1, 0, 0), (0.00003, 0, 1, 1, -2, 0),
    (0.00003, 0, 3, 0, 0, 0), (0.00002, 0, 0, 2, -2, 0), (0.00002, 0, -1, 1, 2, 0),
    (-0.00002, 0, 1, 3, 0, 0),
)
# Planetary arguments A1..A14: (constant, rate per lunation, coefficient).
_PLANETARY = (
    (299.77, 0.107408, 0.000325), (251.88, 0.016321, 0.000165),
    (251.83, 26.651886, 0.000164), (349.42, 36.412478, 0.000126),
    (84.66, 18.206239, 0.000110), (141.74, 53.303771, 0.000062),
    (207.14, 2.453732, 0.000060), (154.84, 7.306860, 0.000056),
    (34.52, 27.261239, 0.000047), (207.19, 0.121824, 0.000042),
    (291.34, 1.844379, 0.000040), (161.72, 24.198154, 0.000037),
    (239.56, 25.513099, 0.000035), (331.55, 3.592518, 0.000023),
)


def phase_jd(k):
    """Julian Day (UT) of the phase with lunation number k (integer = new
    moon, +0.25 first quarter, +0.5 full, +0.75 last quarter; k = 0 is the
    new moon of 2000-01-06)."""
    t = k / 1236.85
    jde = (2451550.09766 + 29.530588861 * k + 0.00015437 * t ** 2
           - 0.000000150 * t ** 3 + 0.00000000073 * t ** 4)
    e = 1 - 0.002516 * t - 0.0000074 * t ** 2
    m = 2.5534 + 29.10535670 * k - 0.0000014 * t ** 2 - 0.00000011 * t ** 3
    mp = (201.5643 + 385.81693528 * k + 0.0107582 * t ** 2 + 0.00001238 * t ** 3
          - 0.000000058 * t ** 4)
    f = (160.7108 + 390.67050284 * k - 0.0016118 * t ** 2 - 0.00000227 * t ** 3
         + 0.000000011 * t ** 4)
    om = 124.7746 - 1.56375588 * k + 0.0020672 * t ** 2 + 0.00000215 * t ** 3
    frac = round((k % 1) * 4) % 4
    terms = (_NEW_TERMS, _QUARTER_TERMS, _FULL_TERMS, _QUARTER_TERMS)[frac]
    for coef, epow, cm, cmp, cf, com in terms:
        jde += coef * e ** epow * _sin(cm * m + cmp * mp + cf * f + com * om)
    if frac in (FIRST, LAST):
        w = (0.00306 - 0.00038 * e * _cos(m) + 0.00026 * _cos(mp)
             - 0.00002 * _cos(mp - m) + 0.00002 * _cos(mp + m) + 0.00002 * _cos(2 * f))
        jde += w if frac == FIRST else -w
    a1 = 299.77 + 0.107408 * k - 0.009173 * t ** 2
    jde += 0.000325 * _sin(a1)
    for const, rate, coef in _PLANETARY[1:]:
        jde += coef * _sin(const + rate * k)
    return jde - DELTA_T


def phases(first_year, last_year):
    """[(unix seconds, phase code)] of every principal phase whose instant
    falls in first_year..last_year (UTC), in time order."""
    start = datetime.datetime(first_year, 1, 1, tzinfo=datetime.timezone.utc).timestamp()
    end = datetime.datetime(last_year + 1, 1, 1, tzinfo=datetime.timezone.utc).timestamp()
    k = math.floor((first_year - 2000) * 12.3685) - 1
    out = []
    while True:
        for q in range(4):
            unix = (phase_jd(k + q / 4) - UNIX_EPOCH_JD) * 86400
            if unix >= end:
                return out
            if unix >= start:
                out.append((int(round(unix)), q))
        k += 1


def sun_longitude(unix):
    """Apparent ecliptic longitude of the Sun in degrees (Meeus ch. 25)."""
    t = ((unix / 86400 + UNIX_EPOCH_JD + DELTA_T) - 2451545.0) / 36525
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t ** 2
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t ** 2
    c = ((1.914602 - 0.004817 * t - 0.000014 * t ** 2) * _sin(m)
         + (0.019993 - 0.000101 * t) * _sin(2 * m) + 0.000289 * _sin(3 * m))
    om = 125.04 - 1934.136 * t
    return (l0 + c - 0.00569 - 0.00478 * _sin(om)) % 360


def zodiac_index(unix, phase):
    """Tropical zodiac sign (0 = Aries) of the Moon at a principal phase: the
    Moon is then 0/90/180/270 degrees east of the Sun."""
    return int(((sun_longitude(unix) + 90 * phase) % 360) // 30)


def _last_sunday(year, month):
    day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1) if month < 12 \
        else datetime.date(year, 12, 31)
    return day - datetime.timedelta(days=(day.weekday() + 1) % 7)


def eu_offset_hours(unix, standard):
    """UTC offset of a European zone with EU summer time (last Sunday of March
    to the last Sunday of October, switching at 01:00 UTC)."""
    utc = datetime.datetime.fromtimestamp(unix, datetime.timezone.utc)
    begin = datetime.datetime.combine(_last_sunday(utc.year, 3), datetime.time(1),
                                      datetime.timezone.utc)
    finish = datetime.datetime.combine(_last_sunday(utc.year, 10), datetime.time(1),
                                       datetime.timezone.utc)
    return standard + (1 if begin <= utc < finish else 0)
