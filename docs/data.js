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

// Render the 10-day (5 past + today + 4 forecast) card strip into `container`.
window.renderWeatherCards = function(container, days) {
    const todayStr = new Date().toISOString().slice(0, 10);
    container.innerHTML = days.map(d => {
        const isToday = d.date === todayStr;
        const label = new Date(d.date + 'T00:00:00Z').toLocaleDateString(
            window.LANG === 'bg' ? 'bg-BG' : 'en-US',
            { weekday: 'short', month: 'short', day: 'numeric', timeZone: 'UTC' });
        const high = d.temp_max != null ? Math.round(d.temp_max) : '–';
        const low = d.temp_min != null ? Math.round(d.temp_min) : '–';
        const uv = d.uv_max != null ? d.uv_max.toFixed(1) : '–';
        const wind = d.wind_max != null ? Math.round(d.wind_max) : '–';
        return `<div class="weather-card${isToday ? ' today' : ''}">
            <span class="weather-date">${isToday ? t('weather_today') : label}</span>
            <span class="weather-icon">${window.weatherIcon(d.code)}</span>
            <span class="weather-temps">${high}° / ${low}°C</span>
            <span class="weather-detail">${t('weather_uv')} ${uv}</span>
            <span class="weather-detail">${t('weather_wind')} ${wind} km/h</span>
        </div>`;
    }).join('');
};

// Relative "Updated Xm ago" string from an ISO 8601 UTC timestamp, no i18n
// library needed — same {n}/{location} templating pattern used elsewhere.
window.formatUpdatedAgo = function(isoTs) {
    const minutes = Math.max(0, Math.round((Date.now() - new Date(isoTs).getTime()) / 60000));
    if (minutes < 1) return t('weather_updated_just_now');
    if (minutes < 60) return t('weather_updated_mins_ago').replace('{n}', minutes);
    return t('weather_updated_hours_ago').replace('{n}', Math.round(minutes / 60));
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
    const water = waterTemp != null ? waterTemp.toFixed(1) : '–';
    const windArrow = current.wind_dir != null
        ? `<span class="cw-wind-arrow" style="display:inline-block;transform:rotate(${Math.round(current.wind_dir) + 180}deg)">↑</span> `
        : '';
    const windDir = current.wind_dir != null ? ' ' + window.windDirectionLabel(current.wind_dir) : '';
    container.innerHTML = `
        <span class="cw-water"><span class="cw-water-icon">💧</span>${water}°C</span>
        <span class="cw-icon">${window.weatherIcon(current.code)}</span>
        <span class="cw-temp">${temp}°C</span>
        <span class="cw-detail">${t('weather_feels_like')} ${feelsLike}°C</span>
        <span class="cw-detail">${t('weather_humidity')} ${humidity}%</span>
        <span class="cw-detail">${t('weather_uv')} ${uv}</span>
        <span class="cw-detail">${windArrow}${t('weather_wind')} ${wind} km/h${windDir}</span>
        <span class="cw-updated">${window.formatUpdatedAgo(updatedIso)}</span>`;
};

// Trailing 24h hourly air-temperature line chart. Hides the whole section
// (heading + chart) if no hourly data is available.
window.renderHourlyChart = function(containerId, hourly) {
    const section = document.getElementById('hourly-section');
    if (!hourly || !hourly.length) {
        if (section) section.style.display = 'none';
        return;
    }
    const theme = window.plotlyTheme();
    const locale = window.LANG === 'bg' ? 'bg-BG' : 'en-US';
    const labels = hourly.map(h =>
        new Date(h.time + 'Z').toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' }));
    Plotly.newPlot(containerId, [{
        x: labels,
        y: hourly.map(h => h.temp),
        type: 'scatter', mode: 'lines+markers',
        line: { color: '#e0a030', width: 2 },
        marker: { size: 4 },
        text: labels,
        hovertemplate: '%{text}: <b>%{y:.1f}°C</b><extra></extra>'
    }], {
        ...theme,
        xaxis: { ...theme.xaxis, title: '', type: 'category' },
        yaxis: { ...theme.yaxis, title: '°C' }
    }, { responsive: true, displayModeBar: false });
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
