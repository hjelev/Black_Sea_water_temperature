// Moon phase icons shared by the moon pages (moon.js) and the Moon tile on the
// dashboard and weather pages (data.js). Each icon is the full lunar face
// (limb-darkened disc, maria, bright craters) under a soft-edged shadow; the
// shadow is slightly translucent so the dark side shows faint earthshine.
// The face, gradient, blur and clip are defined once in a hidden <svg> that
// every icon references. Twin of build_site.moon_svg().
(function () {
    // Maria as overlapping ellipses [cx, cy, rx, ry, rotation], drawn as one
    // translucent layer so the overlaps merge into the familiar dark seas:
    // Procellarum, Imbrium, Frigoris, Serenitatis, Tranquillitatis, Crisium,
    // Fecunditatis, Nectaris, Nubium, Humorum, Vaporum.
    const MARIA = [
        [5.6, 11.6, 2.6, 4.6, -8], [7.4, 13.8, 2.2, 2.4, 0], [6.6, 8.6, 2.0, 2.2, 0],
        [9.0, 7.2, 2.9, 2.2, -12], [11.8, 4.5, 4.2, 0.75, -4], [13.6, 7.6, 1.8, 1.7, 0],
        [15.7, 10.5, 2.2, 1.7, 22], [14.4, 11.6, 1.2, 1.0, 0], [19.2, 8.9, 1.15, 1.45, 10],
        [18.1, 13.4, 1.3, 2.0, -18], [15.8, 14.6, 1.0, 1.1, 0], [10.6, 15.2, 2.3, 1.5, 12],
        [6.9, 16.0, 1.1, 1.0, 0], [12.0, 9.8, 1.1, 0.8, 0],
    ];
    // Bright craters [cx, cy, r]: Tycho, Copernicus, Kepler, Aristarchus, Proclus.
    const CRATERS = [[11.3, 19.1, 0.5], [9.5, 10.4, 0.42], [6.9, 10.9, 0.28], [5.0, 8.7, 0.3], [17.6, 9.6, 0.22]];
    // Tycho's ray system: thin faint lines out from the crater.
    const RAYS = [[8.5, 12.5], [14.5, 12.8], [5.5, 16.5], [17.5, 17.5], [10.5, 21.6], [13.2, 21.2], [7.5, 19.8]];
    const DEFS = '<svg id="moon-icon-defs" width="0" height="0" aria-hidden="true" '
        + 'style="position:absolute;width:0;height:0;overflow:hidden"><defs>'
        + '<radialGradient id="moon-surface" cx="0.42" cy="0.38" r="0.68">'
        + '<stop offset="0" stop-color="#f8f5ec"/><stop offset="0.55" stop-color="#e4dfcf"/>'
        + '<stop offset="0.85" stop-color="#cdc6b1"/><stop offset="1" stop-color="#aaa28b"/></radialGradient>'
        + '<filter id="moon-soft" x="-10%" y="-10%" width="120%" height="120%">'
        + '<feGaussianBlur stdDeviation="0.35"/></filter>'
        + '<filter id="moon-edge" x="-10%" y="-10%" width="120%" height="120%">'
        + '<feGaussianBlur stdDeviation="0.18"/></filter>'
        // Fine surface grain: fractal noise turned into translucent grey speckle.
        + '<filter id="moon-grain" x="0" y="0" width="100%" height="100%">'
        + '<feTurbulence type="fractalNoise" baseFrequency="1.1" numOctaves="3" seed="7"/>'
        + '<feColorMatrix values="0 0 0 0 0.35  0 0 0 0 0.33  0 0 0 0 0.28  0 0 0 -2.2 1.25"/></filter>'
        + '<clipPath id="moon-clip"><circle cx="12" cy="12" r="10"/></clipPath>'
        + '<g id="moon-face"><circle cx="12" cy="12" r="10" fill="url(#moon-surface)"/>'
        + '<g fill="#857f6e" opacity="0.5" filter="url(#moon-edge)" clip-path="url(#moon-clip)">'
        + MARIA.map(([x, y, rx, ry, a]) =>
            `<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" transform="rotate(${a} ${x} ${y})"/>`).join('')
        + '</g><g stroke="#fbf9f1" stroke-width="0.14" stroke-linecap="round" opacity="0.35" clip-path="url(#moon-clip)">'
        + RAYS.map(([x, y]) => `<line x1="11.3" y1="19.1" x2="${x}" y2="${y}"/>`).join('')
        + '</g><g fill="#fcfaf3" opacity="0.85">'
        + CRATERS.map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}"/>`).join('')
        + '</g><rect x="2" y="2" width="20" height="20" filter="url(#moon-grain)" '
        + 'clip-path="url(#moon-clip)" opacity="0.4"/></g></defs></svg>';

    function injectDefs() {
        if (!document.getElementById('moon-icon-defs')) {
            document.body.insertAdjacentHTML('afterbegin', DEFS);
        }
    }
    if (document.body) injectDefs();
    else document.addEventListener('DOMContentLoaded', injectDefs);

    // Shadow over the dark part at cycle position pos (0 new, 0.5 full), as
    // seen from the northern hemisphere (lit on the right while waxing): a box
    // over the dark half closed by the terminator, a half-ellipse whose width
    // follows the illuminated fraction. The box overshoots the disc so the
    // blur only softens the terminator; the clip trims it to the disc.
    function shadowPath(pos) {
        const k = (1 - Math.cos(2 * Math.PI * pos)) / 2;
        if (k > 0.995) return '';
        if (k < 0.005) return 'M1 12a11 11 0 1 0 22 0a11 11 0 1 0-22 0Z';
        const waxing = pos < 0.5;
        const x = waxing ? -2 : 26;
        const term = waxing === (k < 0.5) ? 0 : 1;
        const rx = (Math.abs(1 - 2 * k) * 10).toFixed(2);
        return `M12 2L12 -2L${x} -2L${x} 26L12 26L12 22A${rx} 10 0 0 ${term} 12 2Z`;
    }

    window.moonSvg = function (pos, size) {
        const d = shadowPath(pos);
        return `<svg class="moon-svg" width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true">`
            + '<circle class="moon-base" cx="12" cy="12" r="10"/><use href="#moon-face"/>'
            + (d ? `<path class="moon-shadow" d="${d}" clip-path="url(#moon-clip)" filter="url(#moon-soft)"/>` : '')
            + '<circle class="moon-rim" cx="12" cy="12" r="10"/></svg>';
    };
})();
