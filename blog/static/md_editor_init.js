'use strict';
// Инициализация EasyMDE для поля #body (редактор поста).
// Подключается в create.html и update.html (конец <body>) — единая точка
// конфигурации, инлайн-скрипты в шаблонах запрещены (канон ARC-0030).
// Сверху на базовый конфиг добавлены: загрузка изображений (imageUploadFunction
// → POST /uploads) и кнопка эмодзи с общей панелью из emoji_picker.js.

const MAX_IMAGE_SIZE = 5 * 1024 * 1024;
const ACCEPTED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];

// Загрузка изображения: файл уходит на сервер, в ответе ждём {"url": "..."}.
function uploadImage(file, onSuccess, onError) {
    if (file.size > MAX_IMAGE_SIZE) {
        onError('Файл больше 5 МБ — уменьшите картинку или сожмите её и попробуйте снова.');
        return;
    }
    if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
        onError('Такой формат нельзя загрузить — поддерживаются PNG, JPEG, GIF и WEBP.');
        return;
    }
    const data = new FormData();
    data.append('file', file);
    fetch('/uploads', { method: 'POST', body: data })
        .then((response) => {
            if (!response.ok) {
                onError('Сервер отклонил файл. Проверьте формат и попробуйте ещё раз.');
                return;
            }
            return response.json();
        })
        .then((result) => {
            if (result && result.url) {
                onSuccess(result.url);
            }
        })
        .catch(() => onError('Не удалось связаться с сервером — проверьте соединение.'));
}

// Кнопка эмодзи в тулбаре: панель открывается под кнопкой, клик вставляет
// символ в позицию курсора.
function emojiToolbarButton() {
    return {
        name: 'emoji',
        action: function (editor) {
            const container = editor.codemirror.getWrapperElement().closest('.EasyMDEContainer');
            let panel = container.querySelector('.emoji-picker');
            if (!panel) {
                panel = document.createElement('div');
                panel.className = 'emoji-picker';
                panel.hidden = true;
                fillEmojiPanel(panel, (emoji) => {
                    editor.codemirror.replaceSelection(emoji);
                    editor.codemirror.focus();
                });
                const button = container.querySelector('.editor-toolbar .emoji-btn');
                if (button) {
                    button.parentElement.insertBefore(panel, button.nextSibling);
                } else {
                    container.appendChild(panel);
                }
            }
            panel.hidden = !panel.hidden;
        },
        title: 'Вставить эмодзи',
        className: 'emoji-btn',
    };
}

new EasyMDE({
    element: document.getElementById('body'),
    spellChecker: false,
    status: false,
    minHeight: '200px',
    uploadImage: true,
    imageUploadFunction: uploadImage,
    imageMaxSize: 5 * 1024 * 1024,
    imageAccept: 'image/png, image/jpeg, image/gif, image/webp',
    toolbar: ['bold', 'italic', 'heading', '|',
              'unordered-list', 'ordered-list', 'quote', 'code', '|',
              'link', 'image', emojiToolbarButton(), '|', 'preview', 'guide'],
});
