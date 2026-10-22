// Moon phases pages (/moon-phases/ and /moon-phases/<year>/). The principal
// phase instants come from the generated /moon-data.js (build_site.py via
// moon.py, Meeus ch. 49) as window.MOON_PHASES = [[unix seconds, phase code
// 0 new / 1 first quarter / 2 full / 3 last quarter], ...]; the Moon's and
// Sun's continuous positions (illumination, distance, zodiac sign) are
// computed here (Meeus ch. 47, 25, 48). Times are shown in the viewer's own
// time zone, so the baked year table is re-rendered on load.
(function () {
    const PHASES = (window.MOON_PHASES || []).map(([unix, q]) => ({ t: unix * 1000, q }));
    const root = document.getElementById('moon-app');
    if (!PHASES.length || !root) return;
    const SYNODIC = 29.530588853;
    const DELTA_T = 69 / 86400;   // TT - UT in days, as in moon.py
    const DAY = 86400000;
    const rad = d => d * Math.PI / 180;
    const norm = d => ((d % 360) + 360) % 360;
    const locale = getLocale();
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const [firstYear, lastYear] = window.MOON_YEARS;
    const pageYear = +root.dataset.year;

    // Periodic terms of the Moon's longitude and distance (Meeus table 47.A):
    // [D, M, M', F, Σl (1e-6 deg), Σr (m)].
    const TERMS = [
        [0, 0, 1, 0, 6288774, -20905355], [2, 0, -1, 0, 1274027, -3699111],
        [2, 0, 0, 0, 658314, -2955968], [0, 0, 2, 0, 213618, -569925],
        [0, 1, 0, 0, -185116, 48888], [0, 0, 0, 2, -114332, -3149],
        [2, 0, -2, 0, 58793, 246158], [2, -1, -1, 0, 57066, -152138],
        [2, 0, 1, 0, 53322, -170733], [2, -1, 0, 0, 45758, -204586],
        [0, 1, -1, 0, -40923, -129620], [1, 0, 0, 0, -34720, 108743],
        [0, 1, 1, 0, -30383, 104755], [2, 0, 0, -2, 15327, 10321],
        [0, 0, 1, 2, -12528, 0], [0, 0, 1, -2, 10980, 79661],
        [4, 0, -1, 0, 10675, -34782], [0, 0, 3, 0, 10034, -23210],
        [4, 0, -2, 0, 8548, -21636], [2, 1, -1, 0, -7888, 24208],
        [2, 1, 0, 0, -6766, 30824], [1, 0, -1, 0, -5163, -8379],
        [1, 1, 0, 0, 4987, -16675], [2, -1, 1, 0, 4036, -12831],
        [2, 0, 2, 0, 3994, -10445], [4, 0, 0, 0, 3861, -11650],
        [2, 0, -3, 0, 3665, 14403], [0, 1, -2, 0, -2689, -7003],
        [2, 0, -1, 2, -2602, 0], [2, -1, -2, 0, 2390, 10056],
        [1, 0, 1, 0, -2348, 6322], [2, -2, 0, 0, 2236, -9884],
    ];

    // Moon and Sun at a Date: cycle position 0..1 (elongation / 360°),
    // illuminated fraction, distances and the Moon's zodiac sign.
    function moonState(date) {
        const T = (date.getTime() / DAY + 2440587.5 + DELTA_T - 2451545) / 36525;
        const Lp = 218.3164477 + 481267.88123421 * T - 0.0015786 * T * T;
        const D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T * T;
        const M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T * T;
        const Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T * T;
        const F = 93.2720950 + 483202.0175233 * T - 0.0036539 * T * T;
        const E = 1 - 0.002516 * T - 0.0000074 * T * T;
        let sl = 0, sr = 0;
        TERMS.forEach(([d, m, mp, f, l, r]) => {
            const arg = rad(d * D + m * M + mp * Mp + f * F);
            const e = Math.pow(E, Math.abs(m));
            sl += l * e * Math.sin(arg);
            sr += r * e * Math.cos(arg);
        });
        sl += 3958 * Math.sin(rad(119.75 + 131.849 * T)) + 1962 * Math.sin(rad(Lp - F))
            + 318 * Math.sin(rad(53.09 + 479264.290 * T));
        const moonLon = norm(Lp + sl / 1e6);
        const moonDist = 385000.56 + sr / 1000;

        // Sun (Meeus ch. 25, low precision).
        const L0 = 280.46646 + 36000.76983 * T;
        const C = (1.914602 - 0.004817 * T) * Math.sin(rad(M))
            + 0.019993 * Math.sin(rad(2 * M)) + 0.000289 * Math.sin(rad(3 * M));
        const ecc = 0.016708634 - 0.000042037 * T;
        const sunLon = norm(L0 + C);
        const sunDist = 149597870.7 * 1.000001018 * (1 - ecc * ecc)
            / (1 + ecc * Math.cos(rad(M + C)));

        // Phase angle (Meeus 48.4) → illuminated fraction.
        const i = 180 - norm(D) - 6.289 * Math.sin(rad(Mp)) + 2.100 * Math.sin(rad(M))
            - 1.274 * Math.sin(rad(2 * D - Mp)) - 0.658 * Math.sin(rad(2 * D))
            - 0.214 * Math.sin(rad(2 * Mp)) - 0.110 * Math.sin(rad(D));
        const pos = norm(moonLon - sunLon) / 360;
        return {
            pos, illum: (1 + Math.cos(rad(i))) / 2, age: pos * SYNODIC,
            moonDist, sunDist, zodiac: Math.floor(moonLon / 30),
            moonDiam: 2 * Math.atan(1737.4 / moonDist) * 180 / Math.PI,
            sunDiam: 2 * Math.atan(696340 / sunDist) * 180 / Math.PI,
        };
    }

    // The Moon as seen from the northern hemisphere: lit on the right while
    // waxing. The lit area is the limb half-circle plus the terminator, a
    // half-ellipse whose width follows the illuminated fraction. Twin of
    // build_site.moon_svg().
    function moonSvg(pos, size) {
        const k = (1 - Math.cos(2 * Math.PI * pos)) / 2;
        const rx = Math.abs(1 - 2 * k) * 10;
        const waxing = pos < 0.5;
        const limb = waxing ? 1 : 0;
        const term = waxing === (k < 0.5) ? 0 : 1;
        const lit = k < 0.005 ? '' : k > 0.995
            ? '<circle class="moon-lit" cx="12" cy="12" r="10"/>'
            : `<path class="moon-lit" d="M12 2A10 10 0 0 ${limb} 12 22A${rx.toFixed(2)} 10 0 0 ${term} 12 2Z"/>`;
        return `<svg class="moon-svg" width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true">`
            + `<circle class="moon-dark" cx="12" cy="12" r="10"/>${lit}</svg>`;
    }

    const phaseNames = t('moon_phases');
    const zodiac = t('zodiac');
    const ZODIAC_SIGNS = '♈♉♊♋♌♍♎♏♐♑♒♓';
    const zodiacHtml = z => `<span class="moon-zodiac-sign">${ZODIAC_SIGNS[z]}︎</span> ${zodiac[z]}`;
    // moon_phases: 0 new, 1 waxing crescent, 2 first quarter, 3 waxing gibbous,
    // 4 full, 5 waning gibbous, 6 last quarter, 7 waning crescent.
    function phaseName(date, pos) {
        const p = principalOn(date);
        if (p) return phaseNames[p.q * 2];
        return phaseNames[[1, 3, 5, 7][Math.min(3, Math.floor(pos * 4))]];
    }

    const startOfDay = date => new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const noonOf = (y, m, d) => new Date(y, m, d, 12);
    const sameDay = (a, b) => startOfDay(a).getTime() === startOfDay(b).getTime();
    // The principal phase falling on the local calendar day of date, if any.
    function principalOn(date) {
        const from = startOfDay(date).getTime();
        const to = new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1).getTime();
        return PHASES.find(p => p.t >= from && p.t < to);
    }

    const fmtDate = new Intl.DateTimeFormat(locale, { day: 'numeric', month: 'long' });
    const fmtDateYear = new Intl.DateTimeFormat(locale, { day: 'numeric', month: 'long', year: 'numeric' });
    const fmtTime = new Intl.DateTimeFormat(locale, { hour: '2-digit', minute: '2-digit', hour12: false });
    const fmtMonth = new Intl.DateTimeFormat(locale, { month: 'long' });
    const fmtWeekday = new Intl.DateTimeFormat(locale, { weekday: 'short' });
    const fmtNum = (v, digits) => v.toLocaleString(locale,
        { minimumFractionDigits: digits, maximumFractionDigits: digits });
    const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
    const $ = id => document.getElementById(id);

    const today = new Date();
    // The current year's page follows the clock; other years open on 1 January.
    let selected = pageYear === today.getFullYear() ? null : noonOf(pageYear, 0, 1);
    let calYear = selected ? pageYear : today.getFullYear();
    let calMonth = selected ? 0 : today.getMonth();
    const reference = () => selected || new Date();

    function renderNow() {
        const date = reference();
        const st = moonState(date);
        $('moon-now-h2').textContent = selected
            ? t('moon_on').replace('{date}', fmtDateYear.format(date) + ', ' + fmtTime.format(date))
            : t('moon_now');
        const facts = [
            ['moon_zodiac', zodiacHtml(st.zodiac)],
            ['moon_illum', `${Math.round(st.illum * 100)}%`],
            ['moon_age', t('moon_age_days').replace('{n}', fmtNum(st.age, 1))],
            ['moon_cycle_pos', fmtNum(st.pos, 2)],
            ['moon_dist', `${fmtNum(st.moonDist, 0)} km`],
            ['moon_diam', `${fmtNum(st.moonDiam, 2)}°`],
            ['moon_sun_dist', `${fmtNum(st.sunDist, 0)} km`],
            ['moon_sun_diam', `${fmtNum(st.sunDiam, 2)}°`],
        ];
        $('moon-now').innerHTML = `
            <div class="moon-hero">${moonSvg(st.pos, 110)}
                <div class="moon-hero-name">${phaseName(date, st.pos)}</div>
                ${selected ? `<button type="button" class="moon-btn" id="moon-reset">${t('moon_back_now')}</button>` : ''}
            </div>
            <dl class="moon-facts">${facts.map(([k, v]) =>
                `<div><dt>${t(k)}</dt><dd>${v}</dd></div>`).join('')}</dl>`;
        const reset = $('moon-reset');
        if (reset) reset.addEventListener('click', () => {
            selected = null;
            calYear = today.getFullYear();
            calMonth = today.getMonth();
            renderAll();
        });
    }

    function relDays(ms, ref) {
        const n = Math.round((startOfDay(new Date(ms)) - startOfDay(ref)) / DAY);
        if (n === 0) return t('moon_today');
        if (n === -1) return t('moon_yesterday');
        if (n === 1) return t('moon_tomorrow');
        return (n < 0 ? t('moon_days_ago') : t('moon_in_days')).replace('{n}', Math.abs(n));
    }

    function phaseCard(date, name, illum, pos, rel) {
        return `<div class="moon-card">
            <div class="moon-card-date">${fmtDate.format(date)}</div>
            <div class="moon-card-time">${fmtTime.format(date)}</div>
            ${rel ? `<div class="moon-card-rel">${rel}</div>` : ''}
            ${moonSvg(pos, 44)}
            <div class="moon-card-name">${name}</div>
            <div class="moon-card-meta">${Math.round(illum * 100)}% / ${fmtNum(pos, 2)}</div>
        </div>`;
    }

    // The principal phases of the lunation holding the reference date: from
    // the new moon before it to the next new moon.
    function renderCycle() {
        const ref = reference();
        let start = 0;
        PHASES.forEach((p, i) => { if (p.q === 0 && p.t <= ref.getTime()) start = i; });
        $('moon-cycle').innerHTML = PHASES.slice(start, start + 5).map(p =>
            phaseCard(new Date(p.t), phaseNames[p.q * 2], [0, 0.5, 1, 0.5][p.q], p.q / 4,
                      relDays(p.t, ref))).join('');
    }

    function renderDays() {
        const ref = reference();
        const cards = [];
        for (let i = 1; i <= 5; i++) {
            const date = noonOf(ref.getFullYear(), ref.getMonth(), ref.getDate() + i);
            const st = moonState(date);
            cards.push(phaseCard(date, phaseName(date, st.pos), st.illum, st.pos));
        }
        $('moon-days').innerHTML = cards.join('');
    }

    function navButton(id, label, aria, disabled, back) {
        return `<button type="button" class="moon-nav-btn" id="${id}" aria-label="${aria}"${disabled ? ' disabled' : ''}>`
            + (back ? `‹ ${label}` : `${label} ›`) + '</button>';
    }

    // Month grid, Monday first; the principal phase days carry their symbol.
    function renderCalendar() {
        const first = new Date(calYear, calMonth, 1);
        const prev = new Date(calYear, calMonth - 1, 1), next = new Date(calYear, calMonth + 1, 1);
        const html = [
            '<div class="moon-cal-row moon-cal-years">',
            navButton('moon-prev-year', calYear - 1, t('moon_prev_year'), calYear <= firstYear, true),
            `<strong>${calYear}</strong>`,
            navButton('moon-next-year', calYear + 1, t('moon_next_year'), calYear >= lastYear, false),
            '</div><div class="moon-cal-row">',
            navButton('moon-prev-month', t('months')[prev.getMonth()], t('moon_prev_month'),
                      prev.getFullYear() < firstYear, true),
            `<strong>${cap(fmtMonth.format(first))}</strong>`,
            navButton('moon-next-month', t('months')[next.getMonth()], t('moon_next_month'),
                      next.getFullYear() > lastYear, false),
            '</div><div class="moon-calendar">',
        ];
        for (let i = 0; i < 7; i++) {
            html.push(`<div class="moon-cal-head">${fmtWeekday.format(new Date(2024, 0, 1 + i))}</div>`);
        }
        const lead = (first.getDay() + 6) % 7;
        for (let i = 0; i < lead; i++) html.push('<span class="moon-cal-day empty"></span>');
        const days = new Date(calYear, calMonth + 1, 0).getDate();
        for (let d = 1; d <= days; d++) {
            const date = noonOf(calYear, calMonth, d);
            const st = moonState(date);
            const p = principalOn(date);
            const cls = ['moon-cal-day'];
            if (sameDay(date, today)) cls.push('today');
            if (selected && sameDay(date, selected)) cls.push('selected');
            const label = `${fmtDate.format(date)}: ${phaseName(date, st.pos)}, ${Math.round(st.illum * 100)}%`;
            html.push(`<button type="button" class="${cls.join(' ')}" data-day="${d}" title="${label}" aria-label="${label}">`
                + `${d}${p ? moonSvg(p.q / 4, 13) : ''}</button>`);
        }
        html.push('</div>');
        const cal = $('moon-cal');
        cal.innerHTML = html.join('');
        const shift = months => {
            const d = new Date(calYear, calMonth + months, 1);
            calYear = d.getFullYear();
            calMonth = d.getMonth();
            renderCalendar();
        };
        $('moon-prev-year').addEventListener('click', () => shift(-12));
        $('moon-next-year').addEventListener('click', () => shift(12));
        $('moon-prev-month').addEventListener('click', () => shift(-1));
        $('moon-next-month').addEventListener('click', () => shift(1));
        cal.querySelectorAll('button[data-day]').forEach(btn => btn.addEventListener('click', () => {
            selected = noonOf(calYear, calMonth, +btn.dataset.day);
            renderAll();
        }));
    }

    // Lunar calendar of the page's year: a row per lunation, from its new moon.
    function renderYear() {
        $('moon-year-note').textContent = t('moon_tz_note').replace('{tz}', tz);
        const rows = [];
        let row = null;
        PHASES.filter(p => new Date(p.t).getFullYear() === pageYear).forEach(p => {
            if (!row || p.q <= row.last) {
                row = { cells: ['', '', '', ''], last: -1 };
                rows.push(row);
            }
            const date = new Date(p.t);
            row.cells[p.q] = `<span class="moon-year-date">${moonSvg(p.q / 4, 16)} ${fmtDate.format(date)}</span>`
                + ` ${fmtTime.format(date)}<span class="moon-zodiac">${zodiacHtml(moonState(date).zodiac)}</span>`;
            row.last = p.q;
        });
        document.querySelector('#moon-year tbody').innerHTML = rows.map(r =>
            `<tr>${r.cells.map(c => `<td>${c}</td>`).join('')}</tr>`).join('');
    }

    function renderAll() {
        renderNow();
        renderCalendar();
        renderCycle();
        renderDays();
    }

    renderAll();
    renderYear();
    // Keep the "now" panel live while the page stays open.
    setInterval(() => { if (!selected) renderNow(); }, 60000);
})();
