// Lightweight i18n layer for the static Black Sea Temperature site.
// Loaded in <head> before data.js / inline scripts so t() is available everywhere.

const I18N = {
    en: {
        // <title> tags
        title_dashboard: 'Black Sea Water Temperature',
        title_compare:   'Compare Years — Black Sea Water Temperature',
        title_heatmap:   'Monthly Heatmap — Black Sea Water Temperature',
        title_stats:     'Statistics — Black Sea Water Temperature',
        title_comparelocations: 'Compare Locations — Black Sea Water Temperature',

        // Nav (shared)
        nav_brand:     '🌊 Black Sea Temp',
        nav_dashboard: 'Dashboard',
        nav_compare:   'Compare Years',
        nav_heatmap:   'Heatmap',
        nav_stats:     'Statistics',
        nav_comparelocations: 'Compare Locations',
        nav_location:  'Location',

        // Footer (shared)
        footer_title: 'Black Sea Water Temperature',

        // Locations (shared)
        loc_burgas:      'Burgas, Bulgaria',
        loc_sinemorets:  'Sinemorets, Bulgaria',
        loc_varna:       'Varna, Bulgaria',
        loc_kamenbryag:  'Kamen Bryag, Bulgaria',
        loc_tyulenovo:   'Tyulenovo, Bulgaria',
        loc_nessebar:    'Nessebar, Bulgaria',
        loc_sozopol:     'Sozopol, Bulgaria',
        loc_sunnybeach:  'Sunny Beach, Bulgaria',
        loc_goldensands: 'Golden Sands, Bulgaria',
        loc_balchik:     'Balchik, Bulgaria',
        loc_capekaliakra: 'Cape Kaliakra, Bulgaria',
        loc_albena:      'Albena, Bulgaria',
        loc_svetikonstantin: 'St. Konstantin and Elena, Bulgaria',
        loc_irakli:      'Irakli Beach, Bulgaria',
        loc_pomorie:     'Pomorie, Bulgaria',
        loc_primorsko:   'Primorsko, Bulgaria',
        loc_lozenets:    'Lozenets, Bulgaria',
        loc_svetivlas:   'Sveti Vlas, Bulgaria',

        // index.html (hub)
        hub_h1:       'Black Sea Water Temperature',
        hub_subtitle: "Live and historical sea surface temperature for Bulgaria's Black Sea coast",
        hub_map:      'Current water temperature',
        hub_pick:     'Choose a location',
        map_view:     'View dashboard',

        // index.html
        dash_h1:          'Dashboard',
        dash_subtitle:    'Black Sea water temperature — {location}',
        dash_stats_loading: 'Temperature on this date (loading…)',
        dash_stats_title: 'Temperature on {date} — last 5 years',
        dash_last30:      'Last 30 Days',
        dash_full:        'Full History',
        dash_full_tip:    'Zoom or select a range below to explore historical data.',

        // compare.html
        cmp_h1:        'Compare Years',
        cmp_subtitle:  'Overlay selected years on a Jan–Dec axis to spot seasonal patterns',
        cmp_from:      'From',
        cmp_to:        'To',
        cmp_smooth:    'Smooth (7-day avg)',
        cmp_timeline:  'Timeline selector',
        cmp_tip:       'Drag to select a date range — updates the year checkboxes above.',

        // compare-locations.html
        cl_h1:           'Compare Locations',
        cl_subtitle:     'Overlay water temperature for different towns along the Black Sea coast',
        cl_smooth:       'Smooth (7-day avg)',
        cl_timeline_h2:  'Across the years',
        cl_timeline_tip: 'Each line is a location over the full record. Toggle towns above.',
        cl_seasonal_h2:  'Seasonal (single year)',
        cl_seasonal_tip: 'Selected year only, mapped onto a Jan–Dec axis to compare seasons.',
        cl_year:         'Year',

        // heatmap.html
        hm_h1:         'Monthly Heatmap',
        hm_subtitle:   'Average water temperature per month across all years ({year}–present)',
        hm_monthly:    'Monthly Averages by Year',
        hm_tip:        'Each cell shows the mean temperature for that month/year. Hover for exact values.',

        // stats.html
        st_h1:          'Statistics &amp; Records',
        st_subtitle:    'All-time records and annual statistics since {year}',
        st_records:     'All-time Records',
        st_annual:      'Annual Min / Avg / Max',
        st_trend:       'Long-term Trend',
        st_trend_tip:   'Yearly average with a 5-year moving average trend line.',
        st_hottest:     'Hottest reading',
        st_coldest:     'Coldest reading',
        st_warmest_yr:  'Warmest year (avg)',
        st_coldest_yr:  'Coldest year (avg)',
        st_max:         'Max',
        st_avg:         'Avg',
        st_min:         'Min',
        st_yearly_avg:  'Yearly avg',
        st_trend_5yr:   '5-yr trend',

        months: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    },

    bg: {
        // <title> tags
        title_dashboard: 'Температура на водата в Черно море',
        title_compare:   'Сравнение по години — Температура на Черно море',
        title_heatmap:   'Месечна карта — Температура на Черно море',
        title_stats:     'Статистика — Температура на Черно море',
        title_comparelocations: 'Сравнение на локации — Температура на Черно море',

        // Nav (shared)
        nav_brand:     '🌊 Черно море',
        nav_dashboard: 'Табло',
        nav_compare:   'Сравнение по години',
        nav_heatmap:   'Топлинна карта',
        nav_stats:     'Статистика',
        nav_comparelocations: 'Сравнение на локации',
        nav_location:  'Локация',

        // Footer (shared)
        footer_title: 'Температура на водата в Черно море',

        // Locations (shared)
        loc_burgas:      'Бургас, България',
        loc_sinemorets:  'Синеморец, България',
        loc_varna:       'Варна, България',
        loc_kamenbryag:  'Камен бряг, България',
        loc_tyulenovo:   'Тюленово, България',
        loc_nessebar:    'Несебър, България',
        loc_sozopol:     'Созопол, България',
        loc_sunnybeach:  'Слънчев бряг, България',
        loc_goldensands: 'Златни пясъци, България',
        loc_balchik:     'Балчик, България',
        loc_capekaliakra: 'Нос Калиакра, България',
        loc_albena:      'Албена, България',
        loc_svetikonstantin: 'Св. св. Константин и Елена, България',
        loc_irakli:      'Иракли, България',
        loc_pomorie:     'Поморие, България',
        loc_primorsko:   'Приморско, България',
        loc_lozenets:    'Лозенец, България',
        loc_svetivlas:   'Свети Влас, България',

        // index.html (hub)
        hub_h1:       'Температура на водата в Черно море',
        hub_subtitle: 'Температура на морската повърхност по Българското Черноморие — на живо и исторически данни',
        hub_map:      'Текуща температура на водата',
        hub_pick:     'Изберете локация',
        map_view:     'Към таблото',

        // index.html
        dash_h1:            'Табло',
        dash_subtitle:      'Температура на водата в Черно море — {location}',
        dash_stats_loading: 'Температура на тази дата (зареждане…)',
        dash_stats_title: 'Температура на {date} — последните 5 години',
        dash_last30:        'Последните 30 дни',
        dash_full:          'Пълна история',
        dash_full_tip:      'Мащабирайте или изберете диапазон по-долу, за да разгледате историческите данни.',

        // compare.html
        cmp_h1:        'Сравнение по години',
        cmp_subtitle:  'Наложете избрани години по ос ян.–дек., за да откриете сезонни модели',
        cmp_from:      'От',
        cmp_to:        'До',
        cmp_smooth:    'Изглаждане (7-дневна ср.)',
        cmp_timeline:  'Избор по времева линия',
        cmp_tip:       'Плъзнете, за да изберете период — обновява отметките за години горе.',

        // compare-locations.html
        cl_h1:           'Сравнение на локации',
        cl_subtitle:     'Наложете температурата на водата за различни градове по Черноморието',
        cl_smooth:       'Изглаждане (7-дневна ср.)',
        cl_timeline_h2:  'През годините',
        cl_timeline_tip: 'Всяка линия е локация за целия период. Превключвайте градовете горе.',
        cl_seasonal_h2:  'Сезонно (една година)',
        cl_seasonal_tip: 'Само избраната година, по ос ян.–дек. за сравнение на сезоните.',
        cl_year:         'Година',

        // heatmap.html
        hm_h1:         'Месечна топлинна карта',
        hm_subtitle:   'Средна температура на водата по месеци за всички години ({year} – днес)',
        hm_monthly:    'Месечни средни по години',
        hm_tip:        'Всяка клетка показва средната температура за този месец/година. Посочете за точни стойности.',

        // stats.html
        st_h1:          'Статистика и рекорди',
        st_subtitle:    'Рекорди за всички времена и годишна статистика от {year} г.',
        st_records:     'Рекорди за всички времена',
        st_annual:      'Годишни мин / ср / макс',
        st_trend:       'Дългосрочна тенденция',
        st_trend_tip:   'Годишна средна стойност с линия на 5-годишна плъзгаща средна.',
        st_hottest:     'Най-висока отчетена',
        st_coldest:     'Най-ниска отчетена',
        st_warmest_yr:  'Най-топла година (ср.)',
        st_coldest_yr:  'Най-студена година (ср.)',
        st_max:         'Макс',
        st_avg:         'Ср',
        st_min:         'Мин',
        st_yearly_avg:  'Годишна средна',
        st_trend_5yr:   '5-год. тенденция',

        months: ['Яну','Фев','Мар','Апр','Май','Юни','Юли','Авг','Сеп','Окт','Ное','Дек'],
    },
};

function getLang() {
    const saved = localStorage.getItem('lang');
    if (saved === 'en' || saved === 'bg') return saved;
    return (navigator.language || 'en').toLowerCase().startsWith('bg') ? 'bg' : 'en';
}

function t(key) {
    const lang = getLang();
    const val = (I18N[lang] && I18N[lang][key]);
    return val !== undefined ? val : (I18N.en[key] !== undefined ? I18N.en[key] : key);
}

function setLang(lang) {
    localStorage.setItem('lang', lang);
    location.reload();
}

function applyStaticTranslations() {
    document.documentElement.lang = getLang();
    document.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
        el.innerHTML = t(el.dataset.i18nHtml);
    });
    const titleEl = document.querySelector('title[data-i18n-title]');
    if (titleEl) document.title = t(titleEl.dataset.i18nTitle);
}

function renderSwitcher() {
    const container = document.querySelector('.lang-switch');
    if (!container) return;
    const lang = getLang();
    const flags = [
        { code: 'en', flag: '🇬🇧', label: 'English' },
        { code: 'bg', flag: '🇧🇬', label: 'Български' },
    ];
    container.innerHTML = '';
    flags.forEach(f => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'lang-btn' + (f.code === lang ? ' active' : '');
        btn.textContent = f.flag;
        btn.title = f.label;
        btn.setAttribute('aria-label', f.label);
        btn.addEventListener('click', () => setLang(f.code));
        container.appendChild(btn);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    applyStaticTranslations();
    renderSwitcher();
});
