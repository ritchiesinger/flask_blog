'use strict';
// Замер тизеров постов: .post-clip с коротким содержимым получает .fits (высота auto, кнопка «Раскрыть»
// скрыта — см. blog.css). Порог — текущая свёрнутая высота клипа из computed style, БЕЗ констант в JS
// (ARC-0045: хардкод «9 строк» разошёлся с высотой в CSS и давал пустые тизеры с кнопкой «Развернуть»).
// Пересчёт при изменении чекбокса, ресайзе окна и полной загрузке страницы — картинки меняют scrollHeight
// уже после разбора DOM.
// ARC-0048: замер после «Свернуть» — ПОСЛЕ анимации схлопывания. В момент снятия галочки высота
// промежуточная (близка к полной), scrollHeight <= высота давал ложный .fits: пост не сворачивался,
// обе кнопки прятались (fits скрывает «Развернуть», снятый чекбокс — «Свернуть»).
// Подключается только в index.html (конец <body>); DOM к этому моменту готов.

(function () {
    const animating = new WeakSet(); // клипы в окне анимации схлопывания — замер отложен

    const measureClip = (clip) => {
        animating.delete(clip);
        const box = clip.previousElementSibling;
        const row = clip.parentElement.querySelector('.post-expand-row');
        if (!row) return;
        clip.classList.remove('fits');   // сброс замера перед пересчётом
        if (box && box.checked) return;  // развёрнут: высота auto, мерить нечего
        const collapsedPx = parseFloat(getComputedStyle(clip).height);
        if (clip.scrollHeight <= collapsedPx) clip.classList.add('fits');
    };

    // Ресайз/load не трогают клипы «в анимации» — за них отвечает отложенный замер.
    const adjustClips = () => document.querySelectorAll('.post-clip').forEach((clip) => {
        if (!animating.has(clip)) measureClip(clip);
    });

    document.querySelectorAll('.post-expand').forEach((box) => {
        box.addEventListener('change', () => {
            const clip = box.nextElementSibling;
            if (!clip || !clip.classList.contains('post-clip')) return;
            clip.classList.remove('fits');
            if (box.checked) return; // разворачивание — мерить нечего
            // Схлопывание анимируется 0.4 с: замер сейчас дал бы промежуточную высоту.
            // Мерим по завершении анимации; таймер-фолбэк для браузеров без анимации
            // (prefers-reduced-motion, Firefox/Safari без interpolate-size — там collapse
            // мгновенный, а transitionend не придёт).
            let done = false;
            const measure = () => {
                if (done) return;
                done = true;
                if (!box.checked) measureClip(clip);
            };
            animating.add(clip);
            clip.addEventListener('transitionend', measure, { once: true });
            setTimeout(measure, 500);
        });
    });

    window.addEventListener('resize', adjustClips);
    window.addEventListener('load', adjustClips);
    adjustClips();
})();
