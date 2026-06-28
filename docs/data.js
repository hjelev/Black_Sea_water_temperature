const CSV_BASE = 'https://raw.githubusercontent.com/hjelev/Black_Sea_water_temperature/refs/heads/main/';

const LOCATIONS = {
    burgas:     { csv: 'sea_water_temp.csv',        nameKey: 'loc_burgas',     flag: '🏖️' },
    sinemorets: { csv: 'sinemorets_water_temp.csv', nameKey: 'loc_sinemorets', flag: '⛵' },
};

window.getLocation = function() {
    const saved = localStorage.getItem('location');
    return LOCATIONS[saved] ? saved : 'burgas';
};

window.setLocation = function(id) {
    if (!LOCATIONS[id]) return;
    localStorage.setItem('location', id);
    location.reload();
};

window.locationName = function() {
    return t(LOCATIONS[window.getLocation()].nameKey);
};

window.loadData = function() {
    const id = window.getLocation();
    window.__seaData = window.__seaData || {};
    if (window.__seaData[id]) return Promise.resolve(window.__seaData[id]);
    return fetch(CSV_BASE + LOCATIONS[id].csv)
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

window.renderLocationSwitcher = function() {
    const container = document.querySelector('.loc-switch');
    if (!container) return;
    const current = window.getLocation();
    container.innerHTML = '';
    Object.keys(LOCATIONS).forEach(id => {
        const loc = LOCATIONS[id];
        const label = t(loc.nameKey);
        const shortLabel = label.split(',')[0];
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'loc-btn' + (id === current ? ' active' : '');
        btn.textContent = loc.flag + ' ' + shortLabel;
        btn.title = label;
        btn.setAttribute('aria-label', label);
        btn.addEventListener('click', () => window.setLocation(id));
        container.appendChild(btn);
    });
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
