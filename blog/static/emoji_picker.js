'use strict';
// Пикер эмодзи: наполнение панели + авто-подключение к форме
// комментария (view.html). Тулбар EasyMDE вызывает ту же функцию
// наполнения (md_editor_init.js). Панель = контейнер .emoji-picker,
// hidden атрибут управляет видимостью (CSS: .emoji-picker[hidden]).

// Наполняет панель кнопками эмодзи; клик вызывает onPick и закрывает панель.
function fillEmojiPanel(panel, onPick) {
    window.EMOJI_LIST.forEach((emoji) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'emoji-picker-item';
        item.textContent = emoji;
        item.addEventListener('click', () => {
            onPick(emoji);
            panel.hidden = true;
        });
        panel.appendChild(item);
    });
}

// Форма комментария: кнопка с data-action="emoji-toggle" открывает
// панель [data-emoji-panel], клик по эмодзи вставляет символ в textarea.
const commentForm = document.querySelector('form[action*="comment_create"]');
if (commentForm) {
    const textarea = commentForm.querySelector('textarea');
    const toggle = commentForm.querySelector('[data-action="emoji-toggle"]');
    const panel = commentForm.querySelector('[data-emoji-panel]');
    if (textarea && toggle && panel) {
        panel.hidden = true;
        fillEmojiPanel(panel, (emoji) => {
            textarea.value += emoji;
            panel.hidden = true;
            textarea.focus();
        });
        toggle.addEventListener('click', () => {
            panel.hidden = !panel.hidden;
        });
    }
}

// Форма комментария: кнопка [data-action="emoji-toggle"] открывает
// панель [data-emoji-panel] внутри той же формы, клик по эмодзи вставляет
// символ в textarea. Привязка по data-атрибутам — URL формы мог бы
// измениться, а поведение обязано пережить это без правок.
const toggle = document.querySelector('[data-action="emoji-toggle"]');
if (toggle) {
    const form = toggle.closest('form');
    const textarea = form.querySelector('textarea');
    const panel = form.querySelector('[data-emoji-panel]');
    panel.hidden = true;
    fillEmojiPanel(panel, (emoji) => {
        textarea.value += emoji;
        panel.hidden = true;
        textarea.focus();
    });
    toggle.addEventListener('click', () => {
        panel.hidden = !panel.hidden;
    });
}