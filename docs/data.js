const CSV_BASE = 'https://raw.githubusercontent.com/hjelev/Black_Sea_water_temperature/refs/heads/main/';

// window.LOCATIONS is provided by the generated locations.js (loaded first).
// Each page sets window.LOCATION_ID in its <head> so the location comes from
// the URL, not localStorage — every town has its own indexable page.

window.getLocation = function() {
    const id = window.LOCATION_ID;
    return (window.LOCATIONS && window.LOCATIONS[id]) ? id : 'burgas';
};

window.locationName = function() {
    return t(window.LOCATIONS[window.getLocation()].nameKey);
};

// Iterate locations grouped by country in COUNTRY_ORDER, then any leftover
// countries. cb(countrySlug, [ids]) is called once per non-empty group.
window.eachCountryGroup = function(cb) {
    const order = window.COUNTRY_ORDER || [];
    const seen = {};
    const emit = (country) => {
        const ids = Object.keys(window.LOCATIONS)
            .filter(id => window.LOCATIONS[id].country === country);
        if (ids.length) { seen[country] = true; cb(country, ids); }
    };
    order.forEach(emit);
    Object.keys(window.LOCATIONS).forEach(id => {
        const c = window.LOCATIONS[id].country;
        if (c && !seen[c]) emit(c);
    });
};

// Load and parse one location's CSV by id, cached in window.__seaData[id].
window.loadLocationData = function(id) {
    window.__seaData = window.__seaData || {};
    if (window.__seaData[id]) return Promise.resolve(window.__seaData[id]);
    return fetch(CSV_BASE + window.LOCATIONS[id].csv)
        .then(r => r.text())
        .then(text => {
            const records = [];
            const lines = text.split('\n');
            for (let i = 1; i < lines.length; i++) {
                const line = lines[i].trim();
                if (!line) continue;
                const comma = line.indexOf(',');
                if (comma === -1) continue;
                const date = line.substring(0, comma);
                const temp = parseFloat(line.substring(comma + 1));
                if (date && !isNaN(temp)) {
                    records.push({
                        year:    parseInt(date.substring(0, 4)),
                        month:   parseInt(date.substring(5, 7)),
                        day:     parseInt(date.substring(8, 10)),
                        dateStr: date,
                        temp
                    });
                }
            }
            window.__seaData[id] = records;
            return records;
        });
};

// Load the location named by the current page's window.LOCATION_ID.
window.loadData = function() {
    return window.loadLocationData(window.getLocation());
};

window.renderLocationSwitcher = function() {
    const container = document.querySelector('.loc-switch');
    if (!container) return;
    const current = window.getLocation();
    // Preserve the current view (compare/heatmap/stats/...) when switching town;
    // the dashboard is linked as the folder URL, its canonical form.
    const file = location.pathname.split('/').pop();
    const page = file.endsWith('.html') && file !== 'index.html' ? file : '';
    container.innerHTML = '';
    const select = document.createElement('select');
    select.className = 'loc-select';
    select.setAttribute('aria-label', t('nav_location'));
    const addOption = (parent, id) => {
        const loc = window.LOCATIONS[id];
        const label = t(loc.nameKey);
        const shortLabel = label.split(',')[0];
        const opt = document.createElement('option');
        opt.value = (window.LANG_PREFIX || '') + '/' + id + '/' + page;
        opt.textContent = loc.flag + ' ' + shortLabel;
        opt.title = label;
        if (id === current) opt.selected = true;
        parent.appendChild(opt);
    };
    window.eachCountryGroup(function(country, ids) {
        const group = document.createElement('optgroup');
        group.label = t('country_' + country);
        ids.forEach(id => addOption(group, id));
        select.appendChild(group);
    });
    select.addEventListener('change', () => {
        if (select.value) window.location.href = select.value;
    });
    container.appendChild(select);
};

document.addEventListener('DOMContentLoaded', window.renderLocationSwitcher);

// Load one location's rolling weather window (5 days back + 5 days forecast)
// from docs/weather/<slug>.json, written hourly by get_weather_data.py.
// Same-origin, language-neutral (numbers/dates only) so bg and en pages share it.
window.loadWeatherData = function(id) {
    return fetch('/weather/' + id + '.json').then(r => r.json());
};

// WMO weather codes (Open-Meteo `weathercode`) mapped to an emoji icon.
// https://open-meteo.com/en/docs#weathervariables
window.weatherIcon = function(code) {
    const icons = {
        0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
        45: '🌫️', 48: '🌫️',
        51: '🌦️', 53: '🌦️', 55: '🌦️',
        56: '🌧️', 57: '🌧️',
        61: '🌧️', 63: '🌧️', 65: '🌧️',
        66: '🌧️', 67: '🌧️',
        71: '🌨️', 73: '🌨️', 75: '🌨️', 77: '🌨️',
        80: '🌦️', 81: '🌧️', 82: '⛈️',
        85: '🌨️', 86: '🌨️',
        95: '⛈️', 96: '⛈️', 99: '⛈️'
    };
    return icons[code] || '🌡️';
};

// WMO code → translated condition key (wx_*).
window.weatherCondKey = function(code) {
    if (code === 0) return 'wx_clear';
    if (code === 1) return 'wx_mainly_clear';
    if (code === 2) return 'wx_partly_cloudy';
    if (code === 3) return 'wx_overcast';
    if (code === 45 || code === 48) return 'wx_fog';
    if (code >= 51 && code <= 55) return 'wx_drizzle';
    if (code === 56 || code === 57 || code === 66 || code === 67) return 'wx_freezing_rain';
    if (code >= 61 && code <= 65) return 'wx_rain';
    if ((code >= 71 && code <= 77) || code === 85 || code === 86) return 'wx_snow';
    if (code >= 80 && code <= 82) return 'wx_showers';
    if (code >= 95) return 'wx_thunder';
    return 'wx_partly_cloudy';
};

// WHO UV index categories → { key, color }.
window.uvLevel = function(uv) {
    if (uv < 3) return { key: 'uv_low', color: '#3ea72d' };
    if (uv < 6) return { key: 'uv_moderate', color: '#e0b000' };
    if (uv < 8) return { key: 'uv_high', color: '#f18b00' };
    if (uv < 11) return { key: 'uv_very_high', color: '#e53210' };
    return { key: 'uv_extreme', color: '#b567a4' };
};

// Rough Beaufort grouping of a km/h wind speed.
window.windKey = function(kmh) {
    if (kmh < 6) return 'wind_calm';
    if (kmh < 20) return 'wind_light';
    if (kmh < 39) return 'wind_moderate';
    if (kmh < 62) return 'wind_strong';
    return 'wind_gale';
};

// Relative "Updated Xm ago" string from an ISO 8601 UTC timestamp, no i18n
// library needed — same {n}/{location} templating pattern used elsewhere.
window.formatUpdatedAgo = function(isoTs) {
    const minutes = Math.max(0, Math.round((Date.now() - new Date(isoTs).getTime()) / 60000));
    if (minutes < 1) return t('weather_updated_just_now');
    if (minutes < 60) return t('weather_updated_mins_ago').replace('{n}', minutes);
    if (minutes < 48 * 60) return t('weather_updated_hours_ago').replace('{n}', Math.round(minutes / 60));
    return t('weather_updated_days_ago').replace('{n}', Math.round(minutes / 1440));
};

// Compass abbreviation (translated) for a wind_direction_10m degree value
// (0-360, meteorological convention: direction the wind is blowing FROM).
window.windDirectionLabel = function(deg) {
    const keys = [
        'wind_dir_n', 'wind_dir_ne', 'wind_dir_e', 'wind_dir_se',
        'wind_dir_s', 'wind_dir_sw', 'wind_dir_w', 'wind_dir_nw'
    ];
    const index = Math.round(((deg % 360) + 360) % 360 / 45) % 8;
    return t(keys[index]);
};

// Wind compass: arrow points where the wind blows TO (from + 180°).
function compassSvg(deg) {
    const labels = ['wind_dir_n', 'wind_dir_e', 'wind_dir_s', 'wind_dir_w'].map(t);
    const arrow = deg == null ? '' :
        `<g transform="rotate(${Math.round(deg) + 180} 50 50)">
            <path d="M50 16 L58 38 L50 33 L42 38 Z" fill="var(--accent)"/>
            <line x1="50" y1="33" x2="50" y2="80" stroke="var(--accent)" stroke-width="4" stroke-linecap="round"/>
         </g>`;
    return `<svg class="wx-compass" viewBox="0 0 100 100" aria-hidden="true">
        <circle cx="50" cy="50" r="44" fill="none" stroke="var(--nav-border)" stroke-width="2"/>
        ${[0, 45, 90, 135, 180, 225, 270, 315].map(a =>
            `<line x1="50" y1="8" x2="50" y2="${a % 90 ? 12 : 15}" stroke="var(--text-muted)" stroke-width="2" transform="rotate(${a} 50 50)"/>`).join('')}
        <text x="50" y="27" text-anchor="middle">${labels[0]}</text>
        <text x="77" y="54" text-anchor="middle">${labels[1]}</text>
        <text x="50" y="81" text-anchor="middle">${labels[2]}</text>
        <text x="23" y="54" text-anchor="middle">${labels[3]}</text>
        ${arrow}
    </svg>`;
}

// "Right now" tiles: main conditions, optional sea water, wind compass, UV
// gauge and humidity ring. `current` may be null/absent (e.g. upstream API
// hiccup) - hide the block gracefully rather than throwing. The dashboard
// shows water in its own hero card, so it passes no waterTemp.
window.renderWeatherNow = function(el, current, updatedIso, waterTemp) {
    const c = current;
    if (!c) { el.style.display = 'none'; return; }
    const round = v => v != null ? Math.round(v) : '–';
    const uv = c.uv != null ? c.uv : 0;
    const uvl = window.uvLevel(uv);
    const hum = c.humidity != null ? Math.round(c.humidity) : null;
    const stale = Date.now() - new Date(updatedIso).getTime() > 6 * 3600 * 1000;
    // Wide screens fit the main tile plus all gauges on one row.
    el.style.setProperty('--wx-gauges', 2 + (waterTemp != null) + (hum != null));
    el.innerHTML = `
        <div class="wx-tile wx-main">
            <span class="wx-big-icon">${window.weatherIcon(c.code)}</span>
            <div>
                <span class="wx-big-temp">${round(c.temp)}°</span>
                <span class="wx-cond">${t(window.weatherCondKey(c.code))}</span>
                <span class="wx-sub">${t('weather_feels_like')} ${round(c.feels_like)}°C</span>
                <span class="wx-sub wx-upd${stale ? ' stale' : ''}">${window.formatUpdatedAgo(updatedIso)}</span>
            </div>
        </div>
        ${waterTemp != null ? `<div class="wx-tile wx-sea" style="--wh-color:${window.tempColor(waterTemp)}">
            <span class="wx-tile-label">💧 ${t('weather_sea')}</span>
            <span class="wx-tile-value">${waterTemp.toFixed(1)}°C</span>
            <span class="wx-sub">${t(window.comfortKey(waterTemp))}</span>
        </div>` : ''}
        <div class="wx-tile">
            <span class="wx-tile-label">🌬️ ${t('weather_wind')}</span>
            <div class="wx-wind">
                ${compassSvg(c.wind_dir)}
                <div>
                    <span class="wx-tile-value">${round(c.wind)} <small>km/h</small></span>
                    <span class="wx-sub">${t(window.windKey(c.wind || 0))}${c.wind_dir != null
                        ? ', ' + t('weather_from').replace('{dir}', window.windDirectionLabel(c.wind_dir)) : ''}</span>
                </div>
            </div>
        </div>
        <div class="wx-tile">
            <span class="wx-tile-label">☀️ ${t('weather_uv_index')}</span>
            <span class="wx-tile-value" style="color:${uvl.color}">${uv.toFixed(1)}</span>
            <div class="wx-uv-bar"><span style="left:${Math.min(100, uv / 12 * 100)}%"></span></div>
            <span class="wx-sub">${t(uvl.key)}</span>
        </div>
        ${hum != null ? `<div class="wx-tile">
            <span class="wx-tile-label">💦 ${t('weather_humidity')}</span>
            <div class="wx-ring" style="--p:${hum}"><span>${hum}%</span></div>
        </div>` : ''}`;
};

// Moon position, illumination and rise/set times - the moon part of
// SunCalc (c) Vladimir Agafonkin, BSD-2-Clause, github.com/mourner/suncalc.
// Phase is the same everywhere; rise/set depend on lat/lon.
const moonCalc = (function() {
    const rad = Math.PI / 180, dayMs = 864e5, e = rad * 23.4397;
    const toDays = date => date.valueOf() / dayMs - 0.5 + 2440588 - 2451545;
    const rightAscension = (l, b) => Math.atan2(Math.sin(l) * Math.cos(e) - Math.tan(b) * Math.sin(e), Math.cos(l));
    const declination = (l, b) => Math.asin(Math.sin(b) * Math.cos(e) + Math.cos(b) * Math.sin(e) * Math.sin(l));
    function sunCoords(d) {
        const M = rad * (357.5291 + 0.98560028 * d);
        const L = M + rad * (1.9148 * Math.sin(M) + 0.02 * Math.sin(2 * M) + 0.0003 * Math.sin(3 * M))
            + rad * 102.9372 + Math.PI;
        return { dec: declination(L, 0), ra: rightAscension(L, 0) };
    }
    function moonCoords(d) {
        const L = rad * (218.316 + 13.176396 * d), M = rad * (134.963 + 13.064993 * d),
              F = rad * (93.272 + 13.229350 * d);
        const l = L + rad * 6.289 * Math.sin(M), b = rad * 5.128 * Math.sin(F);
        return { ra: rightAscension(l, b), dec: declination(l, b), dist: 385001 - 20905 * Math.cos(M) };
    }
    function altitude(date, lat, lon) {
        const d = toDays(date), c = moonCoords(d), phi = rad * lat;
        const H = rad * (280.16 + 360.9856235 * d) + rad * lon - c.ra;
        let h = Math.asin(Math.sin(phi) * Math.sin(c.dec) + Math.cos(phi) * Math.cos(c.dec) * Math.cos(H));
        const hr = Math.max(h, 0);  // atmospheric refraction
        return h + 0.0002967 / Math.tan(hr + 0.00312536 / (hr + 0.08901179));
    }
    // fraction: lit part 0-1; phase: 0 new, 0.25 first quarter, 0.5 full, 0.75 last quarter.
    function illumination(date) {
        const d = toDays(date), s = sunCoords(d), m = moonCoords(d), sdist = 149598000;
        const phi = Math.acos(Math.sin(s.dec) * Math.sin(m.dec) + Math.cos(s.dec) * Math.cos(m.dec) * Math.cos(s.ra - m.ra));
        const inc = Math.atan2(sdist * Math.sin(phi), m.dist - sdist * Math.cos(phi));
        const angle = Math.atan2(Math.cos(s.dec) * Math.sin(s.ra - m.ra),
            Math.sin(s.dec) * Math.cos(m.dec) - Math.cos(s.dec) * Math.sin(m.dec) * Math.cos(s.ra - m.ra));
        return { fraction: (1 + Math.cos(inc)) / 2, phase: 0.5 + 0.5 * inc * (angle < 0 ? -1 : 1) / Math.PI };
    }
    // Rise/set within the 24h after `start`; either may be null (the moon
    // skips one roughly every month).
    function times(start, lat, lon) {
        const hc = 0.133 * rad, at = h => new Date(start.valueOf() + h * 36e5);
        let h0 = altitude(start, lat, lon) - hc, rise = null, set = null;
        for (let i = 1; i <= 24; i += 2) {
            const h1 = altitude(at(i), lat, lon) - hc, h2 = altitude(at(i + 1), lat, lon) - hc;
            const a = (h0 + h2) / 2 - h1, b = (h2 - h0) / 2, xe = -b / (2 * a), ye = (a * xe + b) * xe + h1;
            const disc = b * b - 4 * a * h1;
            let roots = 0, x1 = 0, x2 = 0;
            if (disc >= 0) {
                const dx = Math.sqrt(disc) / (Math.abs(a) * 2);
                x1 = xe - dx; x2 = xe + dx;
                if (Math.abs(x1) <= 1) roots++;
                if (Math.abs(x2) <= 1) roots++;
                if (x1 < -1) x1 = x2;
            }
            if (roots === 1) {
                if (h0 < 0) rise = i + x1; else set = i + x1;
            } else if (roots === 2) {
                rise = i + (ye < 0 ? x2 : x1);
                set = i + (ye < 0 ? x1 : x2);
            }
            if (rise != null && set != null) break;
            h0 = h2;
        }
        return { rise: rise != null ? at(rise) : null, set: set != null ? at(set) : null };
    }
    // Next moment the phase reaches `target` (0 new, 0.5 full), refined by
    // a few Newton-style steps along the 29.53-day synodic month.
    function nextPhase(date, target) {
        const month = 29.530588 * dayMs;
        let t = date.valueOf() + ((target - illumination(date).phase + 1) % 1) * month;
        for (let k = 0; k < 4; k++) {
            t += (((target - illumination(new Date(t)).phase + 1.5) % 1) - 0.5) * month;
        }
        return new Date(t);
    }
    return { illumination, times, nextPhase };
})();

const MOON_PHASES = [
    ['moon_new', '🌑'], ['moon_waxing_crescent', '🌒'], ['moon_first_quarter', '🌓'], ['moon_waxing_gibbous', '🌔'],
    ['moon_full', '🌕'], ['moon_waning_gibbous', '🌖'], ['moon_last_quarter', '🌗'], ['moon_waning_crescent', '🌘']
];

// Minutes east of UTC for an IANA zone at a given instant.
function tzOffsetMinutes(date, tz) {
    const p = {};
    new Intl.DateTimeFormat('en-US', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: 'numeric',
        day: 'numeric', hour: 'numeric', minute: 'numeric' })
        .formatToParts(date).forEach(x => { p[x.type] = +x.value; });
    return Math.round((Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute) - date.valueOf()) / 60000);
}

// Sunrise/sunset (today's row of the Open-Meteo daily window, UTC times)
// and moon phase + moonrise/moonset for one location, as two tiles shown in
// the location's own time zone. Each tile hides itself if it has no data.
window.renderAstro = function(el, days, id) {
    const loc = window.LOCATIONS[id], tz = loc.tz, locale = getLocale();
    const now = new Date();
    const hm = d => d ? d.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit', timeZone: tz }) : '—';
    const dayLabel = d => d.toLocaleDateString(locale, { weekday: 'short', day: 'numeric', month: 'short', timeZone: tz });

    // Local calendar day at the location -> its midnight as a UTC instant.
    const ymd = now.toLocaleDateString('en-CA', { timeZone: tz });
    const utcMidnight = new Date(ymd + 'T00:00:00Z');
    const midnight = new Date(utcMidnight.valueOf() - tzOffsetMinutes(utcMidnight, tz) * 60000);

    let sunTile = '';
    const today = (days || []).find(d => d.sunrise && d.sunset &&
        new Date(d.sunrise + 'Z').toLocaleDateString('en-CA', { timeZone: tz }) === ymd);
    if (today) {
        const rise = new Date(today.sunrise + 'Z'), set = new Date(today.sunset + 'Z');
        const mins = Math.round((set - rise) / 60000);
        // Sun's progress along the daylight arc (clamped before rise / after set).
        const f = Math.max(0, Math.min(1, (now - rise) / (set - rise)));
        const up = now >= rise && now <= set;
        const sx = 50 - 40 * Math.cos(Math.PI * f), sy = 46 - 36 * Math.sin(Math.PI * f);
        sunTile = `<div class="wx-tile wx-astro-tile">
            <span class="wx-tile-label">🌅 ${t('weather_sun')}</span>
            <div class="wx-astro-body">
                <svg class="wx-sun-arc" viewBox="0 0 100 52" aria-hidden="true">
                    <path d="M10 46 A40 36 0 0 1 90 46" fill="none" stroke="var(--nav-border)" stroke-width="2" stroke-dasharray="3 3"/>
                    <line x1="4" y1="46" x2="96" y2="46" stroke="var(--text-muted)" stroke-width="1.5"/>
                    <circle cx="${sx.toFixed(1)}" cy="${sy.toFixed(1)}" r="6" fill="${up ? '#f5b400' : 'var(--text-muted)'}"/>
                </svg>
                <div class="wx-astro-times">
                    <span><small>${t('weather_sunrise')}</small><b>${hm(rise)}</b></span>
                    <span><small>${t('weather_sunset')}</small><b>${hm(set)}</b></span>
                </div>
            </div>
            <span class="wx-sub">${t('weather_day_length').replace('{h}', Math.floor(mins / 60)).replace('{m}', mins % 60)}</span>
        </div>`;
    }

    const ill = moonCalc.illumination(now);
    const [phaseKey, emoji] = MOON_PHASES[Math.round(ill.phase * 8) % 8];
    const mt = moonCalc.times(midnight, loc.lat, loc.lon);
    const full = moonCalc.nextPhase(now, 0.5), newMoon = moonCalc.nextPhase(now, 0);
    const moonTile = `<div class="wx-tile wx-astro-tile">
        <span class="wx-tile-label">🌙 ${t('weather_moon')}</span>
        <div class="wx-astro-body">
            <span class="wx-moon-icon" title="${t(phaseKey)}">${emoji}</span>
            <div>
                <span class="wx-cond">${t(phaseKey)}</span>
                <span class="wx-sub">${t('weather_illuminated').replace('{n}', Math.round(ill.fraction * 100))}</span>
            </div>
        </div>
        <div class="wx-astro-times">
            <span><small>${t('weather_moonrise')}</small><b>${hm(mt.rise)}</b></span>
            <span><small>${t('weather_moonset')}</small><b>${hm(mt.set)}</b></span>
        </div>
        <span class="wx-sub">${[[full, 'moon_full', '🌕'], [newMoon, 'moon_new', '🌑']]
            .sort((a, b) => a[0] - b[0])
            .map(([d, key, icon]) => `${icon} ${t(key)}: ${dayLabel(d)}`).join(' · ')}</span>
    </div>`;

    el.innerHTML = sunTile + moonTile;
};

// Trailing 48h hourly air-temperature line chart. Hides the whole section
// (heading + chart) if no hourly data is available. opts.icons adds a weather
// icon above the line every 3 hours (6 on narrow screens).
window.renderHourlyChart = function(containerId, hourly, opts) {
    const section = document.getElementById('hourly-section');
    if (!hourly || !hourly.length) {
        if (section) section.style.display = 'none';
        return;
    }
    const theme = window.plotlyTheme();
    const locale = getLocale();
    // Real date axis (not categories) so Plotly thins the ticks to fit any width.
    const times = hourly.map(h => new Date(h.time + 'Z'));
    const labels = times.map(d =>
        d.toLocaleString(locale, { weekday: 'short', hour: '2-digit', minute: '2-digit' }));
    const temps = hourly.map(h => h.temp);
    const range = window.paddedRange(temps);
    const el = document.getElementById(containerId);
    const iconStep = el && el.clientWidth < 600 ? 6 : 3;
    const annotations = (opts && opts.icons) ? hourly
        .map((h, i) => ({ h, i }))
        .filter(({ h, i }) => i % iconStep === 0 && h.code != null && h.temp != null)
        .map(({ h, i }) => ({ x: times[i], y: h.temp, yshift: 16, showarrow: false,
                              text: window.weatherIcon(h.code), font: { size: 15 } })) : [];
    if (annotations.length && range) range[1] += (range[1] - range[0]) * 0.12;
    Plotly.newPlot(containerId, [{
        x: times,
        y: temps,
        type: 'scatter', mode: 'lines',
        line: { color: '#e0a030', width: 2.5, shape: 'spline' },
        fill: 'tozeroy', fillcolor: 'rgba(224,160,48,0.12)',
        text: labels,
        hovertemplate: '%{text}: <b>%{y:.1f}°C</b><extra></extra>'
    }], {
        ...theme,
        xaxis: { ...theme.xaxis, title: '', tickformat: '%H:%M\n%d.%m' },
        yaxis: { ...theme.yaxis, title: '°C', rangemode: 'normal', range },
        annotations
    }, window.plotlyConfig());
};

// [min, max] of the values with a little headroom, so filled areas don't
// stretch the axis down to zero.
window.paddedRange = function(values) {
    const v = values.filter(x => x != null && !isNaN(x));
    if (!v.length) return undefined;
    const lo = Math.min(...v), hi = Math.max(...v);
    const pad = Math.max(0.5, (hi - lo) * 0.1);
    return [lo - pad, hi + pad];
};

window.plotlyConfig = function() {
    return { responsive: true, displayModeBar: false };
};

// Cold→warm colour across the Black Sea's ~4–28 °C range (same scale as the hub map).
window.tempColor = function(temp) {
    if (temp == null || isNaN(temp)) return '#888';
    const f = Math.max(0, Math.min(1, (temp - 4) / 24));
    return 'hsl(' + Math.round(220 - f * 220) + ', 75%, 47%)';
};

window.comfortKey = function(temp) {
    if (temp < 17) return 'comfort_cold';
    if (temp < 21) return 'comfort_cool';
    if (temp < 24) return 'comfort_pleasant';
    return 'comfort_warm';
};

// Mean temperature per "MM-DD" over every year before `beforeYear`.
// Returns { byDay: {'MM-DD': avg}, years: n }.
window.dayAverages = function(records, beforeYear) {
    const sums = {}, years = new Set();
    records.forEach(r => {
        if (r.year >= beforeYear) return;
        years.add(r.year);
        const k = r.dateStr.substring(5, 10);
        (sums[k] = sums[k] || [0, 0]);
        sums[k][0] += r.temp; sums[k][1]++;
    });
    const byDay = {};
    Object.keys(sums).forEach(k => { byDay[k] = sums[k][0] / sums[k][1]; });
    return { byDay, years: years.size };
};

// Big "sea water now" card: latest reading, 24h change, anomaly vs the
// historical average for the date, and a swimming-comfort label.
window.renderWaterHero = function(container, records) {
    if (!container || !records.length) return;
    const last = records[records.length - 1];
    const lastTime = new Date(last.dateStr.replace(' ', 'T') + 'Z').getTime();
    // Reading closest to 24h before the latest one.
    let prev = null;
    for (let i = records.length - 2; i >= 0; i--) {
        const dt = lastTime - new Date(records[i].dateStr.replace(' ', 'T') + 'Z').getTime();
        if (dt >= 20 * 3600 * 1000) { prev = records[i]; break; }
    }
    let deltaHtml = '';
    if (prev) {
        const d = Math.round((last.temp - prev.temp) * 10) / 10;
        const cls = d > 0 ? 'up' : d < 0 ? 'down' : 'flat';
        const arrow = d > 0 ? '▲' : d < 0 ? '▼' : '●';
        const txt = d === 0 ? t('water_delta_flat')
            : t('water_delta_day').replace('{sign}', d > 0 ? '+' : '−').replace('{n}', Math.abs(d).toFixed(1));
        deltaHtml = `<span class="wh-chip ${cls}">${arrow} ${txt}</span>`;
    }
    const avg = window.dayAverages(records, last.year);
    const norm = avg.byDay[last.dateStr.substring(5, 10)];
    let anomalyHtml = '';
    if (norm != null && avg.years >= 2) {
        const a = Math.round((last.temp - norm) * 10) / 10;
        const key = a > 0 ? 'water_vs_avg_above' : a < 0 ? 'water_vs_avg_below' : 'water_vs_avg_same';
        anomalyHtml = `<span class="wh-chip ${a > 0 ? 'up' : a < 0 ? 'down' : 'flat'}">${
            t(key).replace('{n}', Math.abs(a).toFixed(1)).replace('{years}', avg.years)}</span>`;
    }
    const locale = getLocale();
    const measured = new Date(lastTime).toLocaleString(locale,
        { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
    container.style.setProperty('--wh-color', window.tempColor(last.temp));
    container.innerHTML = `
        <div class="wh-main">
            <span class="wh-label">💧 ${t('water_now')}</span>
            <span class="wh-temp">${last.temp.toFixed(1)}<small>°C</small></span>
            <span class="wh-comfort">${t(window.comfortKey(last.temp))}</span>
        </div>
        <div class="wh-side">
            ${deltaHtml}
            ${anomalyHtml}
            <span class="wh-measured">${t('water_measured').replace('{date}', measured)}</span>
        </div>`;
};

window.plotlyTheme = function() {
    const text = getComputedStyle(document.documentElement).getPropertyValue('--text').trim() || '#333';
    const muted = getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#666';
    return {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor:  'rgba(0,0,0,0)',
        font: { color: text, size: 12 },
        xaxis: { gridcolor: 'rgba(128,128,128,0.15)', zerolinecolor: 'rgba(128,128,128,0.2)', color: muted },
        yaxis: { gridcolor: 'rgba(128,128,128,0.15)', zerolinecolor: 'rgba(128,128,128,0.2)', color: muted },
        legend: { font: { color: text } },
        margin: { l: 50, r: 20, t: 40, b: 50 }
    };
};

// Plotly's `responsive` only reacts to window resizes; a chart drawn before the
// scrollbar or fonts settle keeps a stale width. Re-fit charts whenever their
// container actually changes size.
if (window.ResizeObserver) {
    document.addEventListener('DOMContentLoaded', function() {
        const ro = new ResizeObserver(entries => entries.forEach(e => {
            if (e.target.classList.contains('js-plotly-plot')) Plotly.Plots.resize(e.target);
        }));
        document.querySelectorAll('.chart, .chart-tall').forEach(el => ro.observe(el));
    });
}
