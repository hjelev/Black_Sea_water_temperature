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
        opt.value = '/' + id + '/' + page;
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
