// Slides About-section blocks in from either side as they enter the viewport,
// and lifts "approach" cards up from below — re-triggering every time the
// element scrolls into view (not just the first time).
document.addEventListener('DOMContentLoaded', function () {
    const slideTargets = document.querySelectorAll('[data-slide]');
    const riseTargets = document.querySelectorAll('[data-rise-item]');

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const supportsIO = 'IntersectionObserver' in window;

    if (reduceMotion || !supportsIO) {
        slideTargets.forEach(function (el) { el.classList.add('is-visible'); });
        riseTargets.forEach(function (el) { el.classList.add('is-visible'); });
        return;
    }

    // Slide-in blocks: one-shot animation on first appearance.
    const slideObserver = new IntersectionObserver(function (entries, obs) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                obs.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px',
    });

    slideTargets.forEach(function (el) { slideObserver.observe(el); });

    // Approach cards: rise from below each time the viewport crosses them.
    // We toggle the class instead of unobserving, so scrolling away and back
    // re-plays the animation. A small per-card delay makes them stagger.
    const riseObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            const el = entry.target;
            if (entry.isIntersecting) {
                // Force a reflow so removing then re-adding the class restarts
                // the CSS animation even when the element is already visible.
                el.classList.remove('is-visible');
                void el.offsetWidth;
                el.classList.add('is-visible');
            } else {
                el.classList.remove('is-visible');
            }
        });
    }, {
        threshold: 0.2,
        rootMargin: '0px 0px -40px 0px',
    });

    riseTargets.forEach(function (el, index) {
        el.style.transitionDelay = (index * 120) + 'ms';
        riseObserver.observe(el);
    });
});
