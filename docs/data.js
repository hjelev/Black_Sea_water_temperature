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
    // Preserve the current view (index/compare/heatmap/stats) when switching town.
    const file = (location.pathname.split('/').pop()) || 'index.html';
    const page = file.endsWith('.html') ? file : 'index.html';
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

// Current-conditions card. `current` may be null/absent (e.g. upstream API
// hiccup) - hide the card gracefully rather than throwing.
window.renderCurrentWeather = function(container, current, updatedIso, waterTemp) {
    if (!current) {
        container.style.display = 'none';
        return;
    }
    const temp = current.temp != null ? Math.round(current.temp) : '–';
    const feelsLike = current.feels_like != null ? Math.round(current.feels_like) : '–';
    const humidity = current.humidity != null ? Math.round(current.humidity) : '–';
    const wind = current.wind != null ? Math.round(current.wind) : '–';
    const uv = current.uv != null ? current.uv.toFixed(1) : '–';
    // The dashboard shows water in its own hero card, so it passes no waterTemp.
    const waterHtml = waterTemp != null
        ? `<span class="cw-water"><span class="cw-water-icon">💧</span>${waterTemp.toFixed(1)}°C</span>` : '';
    const windArrow = current.wind_dir != null
        ? `<span class="cw-wind-arrow" style="display:inline-block;transform:rotate(${Math.round(current.wind_dir) + 180}deg)">↑</span> `
        : '';
    const windDir = current.wind_dir != null ? ' ' + window.windDirectionLabel(current.wind_dir) : '';
    container.innerHTML = `
        ${waterHtml}
        <span class="cw-icon">${window.weatherIcon(current.code)}</span>
        <span class="cw-temp">${temp}°C</span>
        <span class="cw-detail">${t('weather_feels_like')} ${feelsLike}°C</span>
        <span class="cw-detail">${t('weather_humidity')} ${humidity}%</span>
        <span class="cw-detail">${t('weather_uv')} ${uv}</span>
        <span class="cw-detail">${windArrow}${t('weather_wind')} ${wind} km/h${windDir}</span>
        <span class="cw-updated">${window.formatUpdatedAgo(updatedIso)}</span>`;
    if (Date.now() - new Date(updatedIso).getTime() > 6 * 3600 * 1000) container.classList.add('stale');
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
    const locale = window.LANG === 'bg' ? 'bg-BG' : 'en-US';
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
    const locale = window.LANG === 'bg' ? 'bg-BG' : 'en-US';
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
