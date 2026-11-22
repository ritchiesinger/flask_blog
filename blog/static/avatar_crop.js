'use strict';
// Кроп-виджет аватара (→ ARC-0051): модалка с квадратной областью кадра.
// Подключается только в profile.html (конец <body>); форма #avatar-upload-form
// есть только на своём профиле — на чужом виджет молчит, как и положено.
// Выбор файла в форме открывает модалку Bootstrap: перетаскивание мышью/пальцем
// и зум (слайдер + колесо мыши) выбирают квадрат; «Применить» режет кадр через
// canvas и отправляет на POST /user/<username>/avatar (FormData, поле file),
// затем перезагружает страницу — флеш-сообщения показывает сервер.
// GIF теряет анимацию при кропе (остаётся первый кадр) — пользователь
// предупреждён текстом модалки. Обход виджета не страшен: без JS форма
// отправляет файл как есть, сервер дорезает до квадрата по центру.
// Кнопка отправки disabled, пока файл не выбран: пустая форма не уходит
// на сервер (нативная валидация required — страховка для fallback без JS).
// CSS области кадра (.avatar-crop-stage и пр.) — в blog.css, ширина области
// обязана совпадать с CROP_VIEWPORT.

const CROP_VIEWPORT = 320; // размер квадратной области выбора на экране, px
const CROP_OUTPUT = 400;   // размер канвы результата; сервер дорежет до AVATAR_SIZE
const ZOOM_MIN = 1;
const ZOOM_MAX = 3;
const ZOOM_STEP = 0.1;     // шаг зума колесом мыши
const ERROR_HIDE_DELAY = 5000; // мс до скрытия плашки с ошибкой в модалке

(function () {
    const form = document.querySelector('#avatar-upload-form');
    const modalEl = document.getElementById('avatar-crop-modal');
    if (!form || !modalEl) return;
    const input = form.querySelector('input[type="file"]');
    const stage = modalEl.querySelector('.avatar-crop-stage');
    const image = modalEl.querySelector('#avatar-crop-image');
    const zoomSlider = modalEl.querySelector('#avatar-crop-zoom');
    const applyButton = modalEl.querySelector('#avatar-crop-apply');
    const errorBox = modalEl.querySelector('#avatar-crop-error');
    const submitButton = form.querySelector('#avatar-upload-submit');
    if (!input || !stage || !image || !zoomSlider || !applyButton || !errorBox) return;
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

    let file = null;              // исходный файл — тип и имя нужны для отправки
    let naturalWidth = 0;
    let naturalHeight = 0;
    let fitScale = 1;             // масштаб «вписать картинку в область»
    let scale = 1;                // текущий масштаб (px экрана на px исходника)
    let offset = { x: 0, y: 0 };  // смещение картинки в области (левый верх)
    let errorTimer = null;

    if (submitButton) submitButton.disabled = true;

    const showCropError = (message) => {
        errorBox.textContent = message;
        errorBox.hidden = false;
        clearTimeout(errorTimer);
        errorTimer = setTimeout(() => { errorBox.hidden = true; }, ERROR_HIDE_DELAY);
    };

    // Картинка не должна покидать область: смещение держим в пределах покрытия.
    const clampOffset = () => {
        offset.x = Math.min(0, Math.max(CROP_VIEWPORT - naturalWidth * scale, offset.x));
        offset.y = Math.min(0, Math.max(CROP_VIEWPORT - naturalHeight * scale, offset.y));
    };

    const render = () => {
        image.style.width = `${naturalWidth * scale}px`;
        image.style.height = `${naturalHeight * scale}px`;
        image.style.transform = `translate(${offset.x}px, ${offset.y}px)`;
    };

    const fit = () => {
        fitScale = Math.max(CROP_VIEWPORT / naturalWidth, CROP_VIEWPORT / naturalHeight);
        scale = fitScale;
        offset = {
            x: (CROP_VIEWPORT - naturalWidth * scale) / 2,
            y: (CROP_VIEWPORT - naturalHeight * scale) / 2,
        };
        render();
    };

    const applyZoom = (zoom) => {
        const previous = scale;
        scale = fitScale * zoom;
        // точка под центром области остаётся под центром
        offset.x = CROP_VIEWPORT / 2 - ((CROP_VIEWPORT / 2 - offset.x) * scale) / previous;
        offset.y = CROP_VIEWPORT / 2 - ((CROP_VIEWPORT / 2 - offset.y) * scale) / previous;
        clampOffset();
        zoomSlider.value = String(zoom);
        render();
    };

    zoomSlider.addEventListener('input', () => applyZoom(parseFloat(zoomSlider.value)));

    stage.addEventListener('wheel', (event) => {
        event.preventDefault();
        const zoom = parseFloat(zoomSlider.value) + (event.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP);
        applyZoom(Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, zoom)));
    }, { passive: false });

    let dragging = null;
    stage.addEventListener('pointerdown', (event) => {
        dragging = { x: event.clientX, y: event.clientY, ox: offset.x, oy: offset.y };
        stage.setPointerCapture(event.pointerId);
    });
    stage.addEventListener('pointermove', (event) => {
        if (!dragging) return;
        offset.x = dragging.ox + (event.clientX - dragging.x);
        offset.y = dragging.oy + (event.clientY - dragging.y);
        clampOffset();
        render();
    });
    stage.addEventListener('pointerup', () => { dragging = null; });
    stage.addEventListener('pointercancel', () => { dragging = null; });

    input.addEventListener('change', () => {
        const selected = input.files && input.files[0];
        if (submitButton) submitButton.disabled = !selected;
        input.value = '';
        if (!selected) return;
        file = selected;
        const reader = new FileReader();
        reader.addEventListener('load', () => {
            image.onload = () => {
                naturalWidth = image.naturalWidth;
                naturalHeight = image.naturalHeight;
                fit();
                modal.show();
            };
            image.onerror = () => showCropError('Файл не открывается как изображение.');
            image.src = reader.result;
        });
        reader.addEventListener('error', () => showCropError('Не удалось прочитать файл.'));
        reader.readAsDataURL(selected);
    });

    applyButton.addEventListener('click', () => {
        // Режем кадр: видимая область в координатах исходника — на канву.
        const sourceSide = CROP_VIEWPORT / scale;
        const sx = -offset.x / scale;
        const sy = -offset.y / scale;
        const canvas = document.createElement('canvas');
        canvas.width = CROP_OUTPUT;
        canvas.height = CROP_OUTPUT;
        canvas.getContext('2d').drawImage(image, sx, sy, sourceSide, sourceSide, 0, 0, CROP_OUTPUT, CROP_OUTPUT);
        const type = file.type === 'image/jpeg' ? 'image/jpeg' : 'image/png';
        canvas.toBlob((blob) => {
            if (!blob) {
                showCropError('Не удалось подготовить кадр.');
                return;
            }
            const data = new FormData();
            data.append('file', new File([blob], type === 'image/jpeg' ? 'avatar.jpg' : 'avatar.png', { type }));
            applyButton.disabled = true;
            fetch(form.action, { method: 'POST', body: data })
                .then((response) => {
                    applyButton.disabled = false;
                    if (response.ok) { // успех — редирект на профиль, за ним флеш
                        modal.hide();
                        window.location.reload();
                        return;
                    }
                    response.json().then((result) => {
                        showCropError((result && result.error) || 'Сервер отклонил файл. Проверьте формат и попробуйте ещё раз.');
                    }, () => showCropError('Сервер отклонил файл. Проверьте формат и попробуйте ещё раз.'));
                })
                .catch(() => {
                    applyButton.disabled = false;
                    showCropError('Не удалось связаться с сервером — проверьте соединение.');
                });
        }, type);
    });
})();
