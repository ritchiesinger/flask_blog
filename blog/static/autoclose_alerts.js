'use strict';
// Автозакрытие тостов флеш-сообщений (.auto-close).
// Появление: .show добавляется сразу после загрузки — transition из blog.css
// плавно проявляет тост. Через 5 с .show снимается — transition обратным
// ходом гасит тост, затем он удаляется из DOM.


const AUTO_CLOSE_MS = 5000;
const REMOVE_MS = 400;

document.querySelectorAll('.toast.auto-close').forEach((toast) => {
    // Форсируем расчёт стартовых стилей (opacity 0), иначе переход с анимацией
    // может не сработать: тост просто появится сразу в конечном состоянии
    void toast.offsetWidth;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
        // Уход по той же transition (300 мс), затем удаление из DOM
        setTimeout(() => toast.remove(), REMOVE_MS);
    }, AUTO_CLOSE_MS);
});
