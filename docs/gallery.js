// Lightbox for the per-location photo gallery. Progressive enhancement: the
// grid and its attribution captions work without JS; this adds click-to-enlarge.
(function () {
    function buildOverlay() {
        const ov = document.createElement('div');
        ov.className = 'gallery-lightbox';
        ov.hidden = true;
        ov.innerHTML =
            '<button class="gallery-close" type="button" aria-label="Close">×</button>' +
            '<figure class="gallery-lightbox-inner">' +
            '<img alt="">' +
            '<figcaption></figcaption>' +
            '</figure>';
        document.body.appendChild(ov);
        return ov;
    }

    document.addEventListener('DOMContentLoaded', function () {
        const links = document.querySelectorAll('.gallery-link');
        if (!links.length) return;
        const ov = buildOverlay();
        const img = ov.querySelector('img');
        const cap = ov.querySelector('figcaption');
        const close = function () {
            ov.hidden = true;
            img.removeAttribute('src');
            document.body.style.overflow = '';
        };
        ov.addEventListener('click', function (e) {
            if (e.target === ov || e.target.classList.contains('gallery-close')) close();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !ov.hidden) close();
        });
        links.forEach(function (a) {
            a.addEventListener('click', function (e) {
                e.preventDefault();
                img.src = a.getAttribute('data-full') || a.getAttribute('href');
                const artist = a.getAttribute('data-artist') || '';
                const page = a.getAttribute('data-page') || '';
                const label = (typeof t === 'function') ? t('gal_commons') : 'View on Wikimedia Commons';
                cap.innerHTML = '© ' + artist +
                    (page ? ' · <a href="' + page + '" target="_blank" rel="noopener nofollow">' + label + '</a>' : '');
                ov.hidden = false;
                document.body.style.overflow = 'hidden';
            });
        });
    });
})();
