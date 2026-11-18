'use strict';
// Модалка подтверждения удаления (#confirm-modal в base.html):
// data-action (delete_post/user/comment) на кнопке внутри формы → текст
// из CONFIRM_TEXTS (FALLBACK_TEXT по умолчанию) → показ модалки →
// подтверждение сабмитит ближайшую форму. Подключается в base.html
// (конец <body>); DOM к этому моменту готов.

const CONFIRM_TEXTS = {
    delete_post: 'Удалить пост? Действие необратимо.',
    delete_user: 'Удалить пользователя? Все его посты будут удалены вместе с аккаунтом. Действие необратимо.',
    delete_comment: 'Удалить комментарий? Действие необратимо.',
};
const FALLBACK_TEXT = 'Вы уверены? Действие необратимо.';

const modalEl = document.getElementById('confirm-modal');
const confirmBtn = document.getElementById('confirm-delete');
const modalText = document.getElementById('confirm-modal-text');

if (modalEl && confirmBtn) {
    let formToSubmit = null;

    document.querySelectorAll('[data-action="delete_post"], [data-action="delete_user"], [data-action="delete_comment"]').forEach((btn) => {
        btn.addEventListener('click', (event) => {
            event.preventDefault();
            formToSubmit = btn.closest('form');
            if (modalText) {
                modalText.textContent = CONFIRM_TEXTS[btn.dataset.action] || FALLBACK_TEXT;
            }
            bootstrap.Modal.getOrCreateInstance(modalEl).show(btn);
        });
    });

    confirmBtn.addEventListener('click', () => {
        if (formToSubmit) formToSubmit.submit();
    });
}
