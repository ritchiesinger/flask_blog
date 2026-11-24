'use strict';
// Инициализация EasyMDE: поле поста #body и текстарии комментариев
// [data-mde="comment"]. Подключается в create.html, update.html,
// view.html, comment_update.html (конец <body>) — единая точка
// конфигурации, инлайн-скрипты в шаблонах запрещены (канон ARC-0030).
// Порядок загрузки скриптов: emoji_list.js → emoji_picker.js → этот файл
// (эмодзи-кнопка тулбара вызывает fillEmojiPanel из emoji_picker.js).
// Конфигурации (→ ARC-0054): пост — кастомный тулбар с загрузкой
// изображений (→ ARC-0047) и эмодзи-кнопкой; комментарий — тулбар зеркалит
// базовый уровень render_markdown: заголовок и картинка кнопками НЕ даются,
// nh3 их снимает — тулбар обещает только то, что реально отрендерится.

// Лимит загрузки изображения — одна константа для собственной проверки
// uploadImage и конфига EasyMDE, чтобы цифры не расходились. Порог высок
// сознательно: цель раунда изображений — пользователь НЕ готовит картинку
// заранее, сервер сам пережимает до детальной версии и строит миниатюру.
// Файл больше 50 МБ — почти наверняка не изображение (видео, архив), его
// отрезаем на клиенте, не гоняя по сети. Серверный лимит (MAX_CONTENT_LENGTH,
// если задан) — последняя инстанция против обхода клиентского кода.
const MAX_IMAGE_SIZE = 50 * 1024 * 1024;
const MAX_IMAGE_SIZE_MB = MAX_IMAGE_SIZE / (1024 * 1024);
const ACCEPTED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];
const ERROR_HIDE_DELAY = 5000; // мс до скрытия плашки с текстом ошибки
const COMMENT_MIN_HEIGHT = '120px'; // редактор комментария компактнее поста

// Плашка индикатора (Bootstrap .progress) живёт внутри контейнера редактора
// сразу под тулбаром, создаётся один раз. Прогресс и ошибки показываются в ней
// для обоих путей загрузки: кнопка и drag&drop идут через одну uploadImage.
// На странице один редактор (как у emoji_picker.js), поэтому глобальный запрос.
function uploadIndicator() {
    const container = document.querySelector('.EasyMDEContainer');
    if (!container) return null;
    let wrapper = container.querySelector('.upload-progress');
    if (!wrapper) {
        wrapper = document.createElement('div');
        wrapper.className = 'upload-progress progress mx-2 mt-1';
        wrapper.hidden = true;
        wrapper.innerHTML =
            '<div class="progress-bar" role="progressbar" aria-label="Загрузка изображения" ' +
            'aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" style="width: 0%"></div>';
        const toolbar = container.querySelector('.editor-toolbar');
        if (toolbar) {
            toolbar.insertAdjacentElement('afterend', wrapper);
        } else {
            container.prepend(wrapper);
        }
    }
    return wrapper;
}

function showProgress(percent) {
    const wrapper = uploadIndicator();
    if (!wrapper) return;
    wrapper.hidden = false;
    const bar = wrapper.querySelector('.progress-bar');
    bar.classList.remove('bg-danger');
    bar.textContent = '';
    bar.style.width = `${percent}%`;
    bar.setAttribute('aria-valuenow', percent);
}

function hideProgress() {
    const wrapper = uploadIndicator();
    if (wrapper) wrapper.hidden = true;
}

let errorTimer = null;
function showError(message) {
    const wrapper = uploadIndicator();
    if (!wrapper) return;
    wrapper.hidden = false;
    const bar = wrapper.querySelector('.progress-bar');
    bar.classList.add('bg-danger');
    bar.textContent = message;
    bar.style.width = '100%';
    clearTimeout(errorTimer);
    errorTimer = setTimeout(() => { wrapper.hidden = true; }, ERROR_HIDE_DELAY);
}

// Имя файла попадает в alt разметки; квадратные скобки и обратный слеш
// вырезаем — они ломают Markdown (скобка в имени файла — реальный случай,
// ARC-0049: регэксп записан через шестнадцатеричные коды \x5B и \x5D,
// чтобы скобки не переживали конвейер вывода чата; прямая форма регэкспа
// дважды деградировала при передаче — живой пример лежал на диске).
function safeName(name) {
    return name.replace(/[\x5B\x5D\\]/g, '');
}

// Загрузка изображения: файл уходит на сервер, в ответе ждём {"url": "..."}.
// XHR вместо fetch — ради upload.onprogress (у fetch процентов отправки нет).
// Любой исход (успех, отказ сервера, сеть) заканчивается показом плашки:
// успех скрывает её, ошибка перекрашивает полосу.
function uploadImage(file, onSuccess, onError) {
    if (file.size > MAX_IMAGE_SIZE) {
        showError(`Файл больше ${MAX_IMAGE_SIZE_MB} МБ — это слишком много для изображения. Проверьте, что выбрали картинку, а не видео.`);
        onError('Файл слишком большой.');
        return;
    }
    if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
        showError('Такой формат нельзя загрузить — поддерживаются PNG, JPEG, GIF и WEBP.');
        onError('Неподдерживаемый формат.');
        return;
    }
    const data = new FormData();
    data.append('file', file);
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/uploads');
    clearTimeout(errorTimer);
    showProgress(0);
    xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
            showProgress(Math.round((event.loaded / event.total) * 100));
        }
    });
    xhr.addEventListener('load', () => {
        let result = null;
        try {
            result = JSON.parse(xhr.responseText);
        } catch (e) {
            result = null; // не-JSON — запасной текст ниже (→ ARC-0044)
        }
        if (xhr.status >= 200 && xhr.status < 300 && result && result.url) {
            hideProgress();
            onSuccess(result.url);
        } else {
            const message = (result && result.error)
                ? result.error
                : 'Сервер отклонил файл. Проверьте формат и попробуйте ещё раз.';
            showError(message);
            onError(message);
        }
    });
    xhr.addEventListener('error', () => {
        showError('Не удалось связаться с сервером — проверьте соединение.');
        onError('Не удалось связаться с сервером.');
    });
    xhr.send(data);
}

// Скрытый input type=file — нативный диалог выбора файла с компьютера.
// onchange вешается на каждый клик (замыкание на editor текущего вызова);
// value сбрасывается сразу, повторный выбор того же файла снова срабатывает.
let filePicker = null;
function imagePickerButton() {
    return {
        name: 'upload-image',
        action: function (editor) {
            if (!filePicker) {
                filePicker = document.createElement('input');
                filePicker.type = 'file';
                filePicker.accept = 'image/png, image/jpeg, image/gif, image/webp';
                filePicker.hidden = true;
                document.body.appendChild(filePicker);
            }
            filePicker.onchange = function () {
                const file = filePicker.files && filePicker.files[0];
                filePicker.value = '';
                if (!file) return;
                uploadImage(file, (url) => {
                    editor.codemirror.replaceSelection(`![${safeName(file.name)}](${url})`);
                    editor.codemirror.focus();
                }, () => {}); // текст ошибки уже показан плашкой
            };
            filePicker.click();
        },
        title: 'Загрузить изображение',
        className: 'fa fa-picture-o',
    };
}

// Кнопка эмодзи в тулбаре: панель открывается под кнопкой, клик вставляет
// символ в позицию курсора. Единый механизм вставки для всех форм — раньше
// комментарии вставляли в textarea, что ломалось на CodeMirror (→ ARC-0054).
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

// Тулбар комментария — зеркало базового уровня render_markdown: только то,
// что рендерится (заголовок и картинка исключены сознательно). Кнопка эмодзи —
// на той же позиции, что в постах.
function commentToolbar() {
    return ['bold', 'italic', 'strikethrough', '|',
            'code', 'quote', 'unordered-list', 'ordered-list', '|',
            'link', emojiToolbarButton(), '|', 'preview', 'guide'];
}

// Пост: #body с загрузкой изображений и полным кастомным тулбаром.
function initPostEditor() {
    const element = document.getElementById('body');
    if (!element) return;
    new EasyMDE({
        element: element,
        spellChecker: false,
        status: false,
        minHeight: '200px',
        uploadImage: true,
        imageUploadFunction: uploadImage,
        imageMaxSize: MAX_IMAGE_SIZE,
        imageAccept: 'image/png, image/jpeg, image/gif, image/webp',
        toolbar: ['bold', 'italic', 'heading', '|',
                  'unordered-list', 'ordered-list', 'quote', 'code', '|',
                  'link', imagePickerButton(), emojiToolbarButton(), '|', 'preview', 'guide'],
    });
}

// Комментарий: текстария помечается data-mde="comment" в шаблоне;
// загрузка изображений не подключается — картинки в комментариях не место.
function initCommentEditor() {
    const element = document.querySelector('textarea[data-mde="comment"]');
    if (!element) return;
    new EasyMDE({
        element: element,
        spellChecker: false,
        status: false,
        minHeight: COMMENT_MIN_HEIGHT,
        toolbar: commentToolbar(),
    });
}

initPostEditor();
initCommentEditor();
