'use strict';
// Тултипы Bootstrap: инициализация всех [data-bs-toggle="tooltip"].
// Подключается в base.html (конец <body>); DOM к этому моменту готов.

document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(
    (el) => new bootstrap.Tooltip(el)
);
