'use strict';
// Модалка подтверждения (#confirm-modal в base.html): data-action (delete_post/user/comment, change_role, reset_avatar)
// на кнопке внутри формы → текст и подпись кнопки из CONFIRM_ACTIONS (fallback по умолчанию) → показ модалки →
// подтверждение сабмитит ближайшую форму. Заголовок модалки тоже меняется: для смены роли «Подтверждение удаления»
// врал бы. Подключается в base.html (конец <body>); DOM к этому моменту готов.

const CONFIRM_ACTIONS = {
    delete_post: {
        title: 'Подтвердите удаление',
        text: 'Удалить пост? Действие необратимо.',
        button: 'Удалить',
    },
    delete_user: {
        title: 'Подтвердите удаление',
        text: 'Удалить пользователя? Все его посты будут удалены вместе с аккаунтом. Действие необратимо.',
        button: 'Удалить',
    },
    delete_comment: {
        title: 'Подтвердите удаление',
        text: 'Удалить комментарий? Действие необратимо.',
        button: 'Удалить',
    },
    change_role: {
        title: 'Подтвердите изменение роли',
        text: 'Изменить роль пользователя? Новая роль вступит в силу сразу.',
        button: 'Изменить',
    },
    reset_avatar: {
        title: 'Подтверждение сброса аватара',
        text: 'Сбросить аватар? Вернётся автогенерация по имени или логину. Картинку можно загрузить заново.',
        button: 'Сбросить',
    },
};
const FALLBACK_TITLE = 'Подтвердите действие';
const FALLBACK_TEXT = 'Вы уверены? Действие необратимо.';
const FALLBACK_BUTTON = 'Подтвердить';

const modalEl = document.getElementById('confirm-modal');
const confirmBtn = document.getElementById('confirm-delete');
const modalText = document.getElementById('confirm-modal-text');
const modalTitle = modalEl ? modalEl.querySelector('.modal-title') : null;

if (modalEl && confirmBtn) {
    let formToSubmit = null;

    document.querySelectorAll('[data-action="delete_post"], [data-action="delete_user"], [data-action="delete_comment"], [data-action="change_role"], [data-action="reset_avatar"]').forEach((btn) => {
        btn.addEventListener('click', (event) => {
            event.preventDefault();
            formToSubmit = btn.closest('form');
            const action = CONFIRM_ACTIONS[btn.dataset.action];
            if (modalTitle) {
                modalTitle.textContent = action ? action.title : FALLBACK_TITLE;
            }
            if (modalText) {
                modalText.textContent = action ? action.text : FALLBACK_TEXT;
            }
            confirmBtn.textContent = action ? action.button : FALLBACK_BUTTON;
            bootstrap.Modal.getOrCreateInstance(modalEl).show(btn);
        });
    });

    confirmBtn.addEventListener('click', () => {
        if (formToSubmit) formToSubmit.submit();
    });
}
