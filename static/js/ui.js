// Sitewide UI/UX motion controller.
//
// Drives a single CSS animation system across every page:
//   - [data-anim] elements reveal as they enter the viewport (and re-trigger
//     every time they leave and re-enter — the user wants motion on every
//     scroll pass, not just first load).
//   - [data-stagger] containers auto-assign a per-child CSS variable so their
//     direct children cascade in.
//   - .scroll-progress bar at the top of the page fills as the user scrolls.
//
// We use @keyframes (not transitions) so that removing then re-adding the
// `is-visible` class restarts the animation cleanly via a forced reflow.
// prefers-reduced-motion short-circuits everything to the visible state.

(function () {
    'use strict';

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const supportsIO = 'IntersectionObserver' in window;

    // Walk every [data-stagger] container and assign each of its direct
    // children a stagger index. The CSS reads --anim-delay from this.
    document.querySelectorAll('[data-stagger]').forEach(function (group) {
        const step = parseInt(group.dataset.staggerStep || '90', 10);
        Array.prototype.forEach.call(group.children, function (child, i) {
            child.style.setProperty('--anim-delay', (i * step) + 'ms');
            // If a child isn't already marked, give it a default reveal
            // variant so the stagger walker produces something visible.
            if (!child.hasAttribute('data-anim')) {
                child.setAttribute('data-anim', 'rise');
            }
        });
    });

    const targets = document.querySelectorAll('[data-anim]');

    if (reduceMotion || !supportsIO) {
        // Show everything immediately; no observer, no scroll progress.
        targets.forEach(function (el) { el.classList.add('is-visible'); });
        return;
    }

    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            const el = entry.target;
            if (entry.isIntersecting) {
                // Force a reflow so the animation restarts even when the
                // element is already visible from a previous pass.
                el.classList.remove('is-visible');
                void el.offsetWidth;
                el.classList.add('is-visible');
            } else {
                // Out of view — drop the class so the next entry re-animates.
                el.classList.remove('is-visible');
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px',
    });

    targets.forEach(function (el) { observer.observe(el); });

    // Scroll-progress bar — write --scroll on :root so the CSS can size
    // the .scroll-progress element. Passive listener for scroll perf.
    const bar = document.querySelector('.scroll-progress');
    if (bar) {
        const update = function () {
            const scrollable = document.documentElement.scrollHeight - window.innerHeight;
            const pct = scrollable > 0
                ? Math.min(100, (window.scrollY / scrollable) * 100)
                : 0;
            document.documentElement.style.setProperty('--scroll', pct + '%');
        };
        update();
        window.addEventListener('scroll', update, { passive: true });
        window.addEventListener('resize', update, { passive: true });
    }
})();
