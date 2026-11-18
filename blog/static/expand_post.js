'use strict';
// Замер тизеров постов: .post-clip с коротким содержимым получает .fits
// (высота auto, кнопка «Раскрыть» скрыта — см. blog.css). Пересчёт при
// изменении чекбокса и ресайзе окна. Подключается только в index.html
// (конец <body>); DOM к этому моменту готов.

(function () {
    const COLLAPSED_LINES = 9;

    const adjustClips = () => {
        const collapsedPx = COLLAPSED_LINES * parseFloat(
            getComputedStyle(document.documentElement).fontSize
        );
        document.querySelectorAll('.post-clip').forEach((clip) => {
            const box = clip.previousElementSibling;
            const row = clip.parentElement.querySelector('.post-expand-row');
            if (!row) return;
            clip.classList.remove('fits');   // сброс замера перед пересчётом
            if (box && box.checked) return;  // развёрнут: высота auto, мерить нечего
            if (clip.scrollHeight <= collapsedPx) clip.classList.add('fits');
        });
    };
    document.querySelectorAll('.post-expand').forEach(
        (box) => box.addEventListener('change', adjustClips)
    );
    window.addEventListener('resize', adjustClips);
    adjustClips();
})();
