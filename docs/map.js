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
            });
    }

    document.addEventListener('DOMContentLoaded', initMap);
})();
