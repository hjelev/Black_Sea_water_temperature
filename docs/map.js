// Hub map: plots every location from window.LOCATIONS on a Leaflet/OpenStreetMap
// map and labels each marker with the current water temperature read from
// /latest_temps.json (generated every 2h by get_daily_temp.py).
//
// Leaflet (window.L), locations.js (window.LOCATIONS) and i18n.js (t) are all
// loaded before this script. Keyless — no API key, no billing.

(function () {
    // Map a temperature to a cold→warm colour across the Black Sea's ~4–28 °C range.
    function tempColor(temp) {
        if (temp == null || isNaN(temp)) return '#888';
        const f = Math.max(0, Math.min(1, (temp - 4) / 24));
        const hue = 220 - f * 220; // 220 = blue (cold) → 0 = red (warm)
        return 'hsl(' + Math.round(hue) + ', 75%, 47%)';
    }

    function initMap() {
        const el = document.getElementById('map');
        if (!el || !window.L || !window.LOCATIONS) return;

        // Centre on the Black Sea basin; fitBounds below tightens to the markers.
        const map = L.map('map', { scrollWheelZoom: false }).setView([43.4, 34.0], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        const bounds = [];

        fetch('/latest_temps.json')
            .then(r => (r.ok ? r.json() : {}))
            .catch(() => ({}))
            .then(latest => {
                Object.keys(window.LOCATIONS).forEach(id => {
                    const loc = window.LOCATIONS[id];
                    if (typeof loc.lat !== 'number' || typeof loc.lon !== 'number') return;

                    const rec = latest[id];
                    const temp = rec ? rec.temp : null;
                    const name = t(loc.nameKey).split(',')[0];
                    const hasTemp = temp != null && !isNaN(temp);
                    const pinText = hasTemp ? temp.toFixed(1) + '°' : '–';
                    const popupTemp = hasTemp ? temp.toFixed(1) + ' °C' : '–';

                    const icon = L.divIcon({
                        className: 'map-temp-pin',
                        html: '<span class="map-temp-pin-inner" style="background:'
                            + tempColor(temp) + '">' + pinText + '</span>',
                        iconSize: null
                    });

                    const dateLine = rec
                        ? '<div class="map-popup-date">' + rec.date + '</div>' : '';
                    L.marker([loc.lat, loc.lon], { icon, title: name })
                        .addTo(map)
                        .bindPopup(
                            '<div class="map-popup">'
                            + '<div class="map-popup-name">' + loc.flag + ' ' + name + '</div>'
                            + '<div class="map-popup-temp">' + popupTemp + '</div>'
                            + dateLine
                            + '<a class="map-popup-link" href="' + (window.LANG_PREFIX || '') + '/' + id + '/">'
                            + t('map_view') + ' →</a>'
                            + '</div>'
                        );

                    bounds.push([loc.lat, loc.lon]);
                });

                // Label each home-screen location card with the same current
                // temperature, colour-matched to the map pins.
                document.querySelectorAll('.hub-card[data-loc]').forEach(card => {
                    const span = card.querySelector('.hub-temp');
                    const rec = latest[card.dataset.loc];
                    if (!span) return;
                    const temp = rec ? rec.temp : null;
                    if (temp != null && !isNaN(temp)) {
                        span.textContent = temp.toFixed(1) + '°';
                        span.style.background = tempColor(temp);
                        span.style.color = '#fff';
                    }
                });

                if (bounds.length) map.fitBounds(bounds, { padding: [30, 30] });
                renderSummary(latest);
                initHubTools(latest);
            });
    }

    // "Warmest now / Coldest now" chips above the map.
    function renderSummary(latest) {
        const el = document.getElementById('hub-summary');
        if (!el) return;
        const rows = Object.keys(window.LOCATIONS)
            .filter(id => latest[id] && latest[id].temp != null && !isNaN(latest[id].temp))
            .map(id => ({ id, temp: latest[id].temp }))
            .sort((a, b) => b.temp - a.temp);
        if (rows.length < 2) return;
        const chip = (row, key) => {
            const loc = window.LOCATIONS[row.id];
            return '<a class="hub-chip" href="' + (window.LANG_PREFIX || '') + '/' + row.id + '/">'
                + '<span class="hub-chip-label">' + t(key) + '</span> '
                + loc.flag + ' ' + t(loc.nameKey).split(',')[0]
                + ' <b style="background:' + tempColor(row.temp) + '">' + row.temp.toFixed(1) + '°</b></a>';
        };
        el.innerHTML = chip(rows[0], 'hub_warmest') + chip(rows[rows.length - 1], 'hub_coldest');
    }

    // Search box + "sort by temperature" toggle for the location cards.
    function initHubTools(latest) {
        const search = document.getElementById('hub-search');
        const sort = document.getElementById('hub-sort');
        const wrap = document.getElementById('hub-locations');
        const empty = document.getElementById('hub-no-match');
        if (!search || !sort || !wrap) return;
        const cards = Array.from(wrap.querySelectorAll('.hub-card[data-loc]'));
        // Remember each card's home so un-sorting restores the country groups.
        const homes = cards.map(c => ({ card: c, parent: c.parentNode }));
        const flat = document.createElement('div');
        flat.className = 'hub-grid hub-flat';
        flat.hidden = true;
        wrap.appendChild(flat);
        const tempOf = c => {
            const rec = latest[c.dataset.loc];
            return rec && rec.temp != null && !isNaN(rec.temp) ? rec.temp : -Infinity;
        };

        function apply() {
            const q = search.value.trim().toLowerCase();
            if (sort.checked) {
                cards.slice().sort((a, b) => tempOf(b) - tempOf(a)).forEach(c => flat.appendChild(c));
            } else {
                homes.forEach(h => h.parent.appendChild(h.card));
            }
            flat.hidden = !sort.checked;
            let shown = 0;
            cards.forEach(c => {
                const match = !q || c.dataset.search.indexOf(q) !== -1;
                c.hidden = !match;
                if (match) shown++;
            });
            wrap.querySelectorAll('.hub-section').forEach(sec => {
                sec.hidden = sort.checked || !sec.querySelector('.hub-card:not([hidden])');
            });
            if (empty) empty.hidden = shown > 0;
        }
        search.addEventListener('input', apply);
        sort.addEventListener('change', apply);
    }

    document.addEventListener('DOMContentLoaded', initMap);
})();
