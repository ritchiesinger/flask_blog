'use strict';
// Наполнение панели эмодзи для тулбара EasyMDE (вызывается из md_editor_init.js).
// Подключается во всех шаблонах с редактором: create.html, update.html,
// view.html, comment_update.html — перед md_editor_init.js (порядок важен:
// эмодзи-кнопка тулбара вызывает fillEmojiPanel).
// Раньше панель подключалась и к формам комментариев напрямую (вставка в
// textarea по data-action="emoji-toggle") — снято в п. 28: с EasyMDE текст
// живёт в CodeMirror, вставка в textarea ломалась. Единый механизм —
// тулбар редактора на всех формах (→ ARC-0054).

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
