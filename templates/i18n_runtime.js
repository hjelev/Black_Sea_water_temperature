// Runtime i18n helpers appended to the generated docs/i18n.js by build_site.py.
// Static text is baked into the HTML per language at build time; this code only
// serves dynamic content (charts, dropdowns, map popups) and the nav widgets.

// The page's language is fixed at build time: window.LANG is injected in <head>,
// with the URL prefix as a fallback (English lives under /en/).
function getLang() {
    if (window.LANG === 'en' || window.LANG === 'bg') return window.LANG;
    const p = location.pathname;
    return (p === '/en' || p.startsWith('/en/')) ? 'en' : 'bg';
}

function t(key) {
    const lang = getLang();
    const val = (I18N[lang] && I18N[lang][key]);
    return val !== undefined ? val : (I18N.en[key] !== undefined ? I18N.en[key] : key);
}

// Path of the current page in the given language (Bulgarian at the root,
// English under /en/).
function siblingPath(lang) {
    let path = location.pathname;
    if (path === '/en') path = '/en/';
    const bgPath = path.startsWith('/en/') ? path.slice(3) : path;
    return lang === 'en' ? '/en' + bgPath : bgPath;
}

function renderSwitcher() {
    const container = document.querySelector('.lang-switch');
    if (!container) return;
    const lang = getLang();
    const flags = [
        { code: 'bg', flag: '🇧🇬', label: 'Български' },
        { code: 'en', flag: '🇬🇧', label: 'English' },
    ];
    container.innerHTML = '';
    flags.forEach(f => {
        const a = document.createElement('a');
        a.className = 'lang-btn' + (f.code === lang ? ' active' : '');
        a.href = siblingPath(f.code);
        a.hreflang = f.code;
        a.textContent = f.flag;
        a.title = f.label;
        a.setAttribute('aria-label', f.label);
        if (f.code === lang) a.setAttribute('aria-current', 'true');
        container.appendChild(a);
    });
}

function renderNavToggle() {
    const inner = document.querySelector('.nav-inner');
    if (!inner || inner.querySelector('.nav-toggle')) return;
    const nav = inner.closest('.nav');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'nav-toggle';
    btn.textContent = '☰';
    btn.setAttribute('aria-label', t('nav_menu'));
    btn.setAttribute('aria-expanded', 'false');
    const close = () => {
        nav.classList.remove('nav-open');
        btn.setAttribute('aria-expanded', 'false');
    };
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const open = nav.classList.toggle('nav-open');
        btn.setAttribute('aria-expanded', String(open));
    });
    // Close when a menu link is tapped or when clicking outside the nav.
    inner.querySelectorAll('.nav-links a').forEach(a => a.addEventListener('click', close));
    document.addEventListener('click', (e) => {
        if (!nav.contains(e.target)) close();
    });
    inner.appendChild(btn);
}

// Collapse the nav to a hamburger whenever the brand + menu + flags no longer
// fit on a single row. Width-agnostic: it measures the real layout, so it
// works for any language label lengths and any viewport size.
function updateNavCollapse() {
    const inner = document.querySelector('.nav-inner');
    if (!inner) return;
    const nav = inner.closest('.nav');
    const brand = inner.querySelector('.nav-brand');
    const links = inner.querySelector('.nav-links');
    const lang = inner.querySelector('.lang-switch');
    if (!nav || !brand || !links || !lang) return;
    // Measure in the expanded state.
    const wasOpen = nav.classList.contains('nav-open');
    nav.classList.remove('nav-collapsed', 'nav-open');
    // If the menu or the flags dropped below the brand's row, it doesn't fit.
    const top = brand.offsetTop;
    const overflow = links.offsetTop > top + 1 || lang.offsetTop > top + 1;
    if (overflow) {
        nav.classList.add('nav-collapsed');
        if (wasOpen) nav.classList.add('nav-open');
    }
}

let navCollapseRaf;
function scheduleNavCollapse() {
    cancelAnimationFrame(navCollapseRaf);
    navCollapseRaf = requestAnimationFrame(updateNavCollapse);
}

document.addEventListener('DOMContentLoaded', () => {
    renderSwitcher();
    renderNavToggle();
    updateNavCollapse();
    window.addEventListener('resize', scheduleNavCollapse);
});
