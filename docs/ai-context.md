# AI-контекст проекта: blog (Flask)

Ядро — только действующие решения, каноны и карта. История — в архиве (ai-context-archive.md, записи ARC-NNNN,
оглавление в шапке; запросы: «Покажи ARC-0007», «Покажи ARC-0001–0009», «Покажи оглавление архива»).
Ссылки из ядра — в формате → ARC-NNNN. Критерий строки ядра: «если забыть — сломает следующую работу?».
Правило закрытия раунда: ядро меняется максимум на ±3 строки (секция раунда + бэклог + счёт),
остальное — одной записью в архив; в конце раунда ядро выдаётся целиком.

## 1. Стек и окружение
- Python 3.15, Flask, SQLite, Windows, PyCharm.
- Shell: `flask --app "blog:create_app()" shell`.
- Верификация раунда: `pytest -v`, `ruff check blog tests`, `coverage run -m pytest && coverage report -m`.

## 2. Архитектура приложения
- Слои: роуты (blueprints: api, web, admin) → сервисы → модели. Роуты тонкие: валидация/flash/redirect,
  логика — в сервисах.
- blog/services/base_errors.py: ServiceError (500) → NotFoundError (404), ForbiddenError (403),
  BadRequestError (400), ConflictError (409). Ошибки бизнес-логики — только этими классами.
- WEB: @web_errors; API: @api_errors → JSON {'error': ...} со статусом из исключения.
  Порядок декораторов: @api_errors сверху.
- Исключение: /api/token отвечает 401 напрямую dict (нет доменных исключений).
- Константы — blog/constants.py: POSTS_PER_PAGE = 5, COMMENTS_PER_PAGE = 10, USERS_PER_PAGE = 20,
  MAX_PER_PAGE = 50, Roles (USER, ADMIN, SUPERADMIN), ROLE_SCOPES и role_includes (иерархия ролей —
  единственная точка истины; → ARC-0041), ROLE_DISPLAY_NAMES/ROLE_BADGE_CLASSES/ROLE_TARGET_OPTIONS
  (ролевые карты: человекочитаемые названия — язык UI; сырые значения — в value dropdown, API и БД;
  → ARC-0043), PROFILE_TAB_POSTS/PROFILE_TAB_COMMENTS/PROFILE_TABS.
  Строки ролей в коде не используются — только константы.
- pyproject: requires-python >=3.15; ruff — line-length 120, py315, E/F/I/UP/B/Q/D, pydocstyle google,
  ignore-decorators ["wraps"]; coverage — branch=true, source=["blog"].
- Чистое состояние (тесты зелёные, Ruff ноль, покрытие 100%) — умолчание закрытия раунда, не фиксируется;
  записывается только отклонение.

## 3. Аутентификация и роли
- JWT (flask-jwt-extended): /api/token, /api/register; WEB — сессии (Flask-Login).
- Роль — по БД через get_current_user(), не через JWT claims (смена роли действует сразу).
  Декоратор role_required(*roles); User.is_admin существует, но проверка идёт через role in roles.
- loaders.py: @login_manager.user_loader + @jwt.user_lookup_loader; регистрация при импорте — фабрика делает
  `import blog.loaders  # noqa: F401` ради декораторов. Файл живой, НЕ удалять (→ ARC-0009).
- CLI — все в blog/cli.py: `flask make-admin`, `flask create-admin`, `flask clean-uploads` (чистка сирот
  uploads, → ARC-0033), `flask make-superadmin` (отказ, если супер-админ уже существует; смена хозяина —
  delete-user, затем make-superadmin), `flask delete-user` (→ ARC-0041).
- Новые CLI-команды регистрируются add_command в фабрике приложения: invoke_cli в тестах зовёт click
  напрямую, живой Flask без регистрации команду не видит; регистрация накрыта юнит-гвардом
  test_cli_registration.py (→ ARC-0041, ARC-0043).
- create-admin: дубль имени — «уже существует», пароль не перезаписывается.
- auth_service: authenticate / register_user; ошибки — исключениями (пустое имя или пароль короче 4 символов →
  BadRequestError; дубль → ConflictError). POST /api/register → 201 {"user": {...}}; username strip — пустая → 400.
- WEB-аутентификация: гость — 302 на логин; под сессией GET /login|/register — 302 на главную; next: внутренние
  пути работают, внешний/`//evil.site`/без ведущего слеша → на главную (open redirect закрыт).

## 4. Пользователи: админ-API и WEB-админка
- API: GET /api/users, DELETE /api/users/<id>; admin_service.list_users / delete_user(user_id, actor).
  Не-админ → 403 (проверка роли ДО поиска); самоудаление → 403; нет пользователя → 404. Сервисный гвард —
  defense-in-depth (юнит-тест), декоратор — ранний барьер.
- WEB (blog/web/admin.py): GET /admin/users, POST /admin/users/<id>/delete; @login_required + @web_errors.
  Гость → 302; не-админ → 404 (не подсказывать скрытые роуты); админ → 200; самоудаление → 403; нет id → 404.
  Расхождение WEB/API — осознанное (API честно 403, WEB прячет 404).
- Роли (→ ARC-0041): SUPERADMIN уникален, выдаётся/снимается только через CLI; смена USER↔ADMIN — только
  супер-админом, себе нельзя (403). API PATCH /api/users/<id> (карта 401→403→400→404→200, повтор
  идемпотентен; супер-админ проходит существующие админ-эндпоинты по иерархии); WEB POST
  /user/<username>/role (302 + флеш «Роль изменена на Administrator.», контролы — dropdown сырых ролей +
  «Изменить» + confirm-модалка — видит только супер-админ на чужом профиле; не-супер прямой POST → 404,
  гость → 302). Бейджи ролей в профиле и админке — человекочитаемые названия (→ ARC-0043).
  В тестах супер-админ — create_user(role=Roles.SUPERADMIN).
- Фирменные ошибки: errorhandler(404)/(500) в фабрике + errors/404.html, errors/500.html;
  один 404-хэндлер ловит и роутинг, и NotFoundError админки.
- Хедер: пункт «Административная панель» только при is_authenticated and is_admin; меню для остальных пустое
  сознательно (вернёмся с профилем).
- Каскадное удаление Post ↔ User: Post.author_id — FK ondelete='CASCADE'; naming convention в extensions.py;
  conftest — PRAGMA foreign_keys=ON; User.posts — cascade='all, delete-orphan' + passive_deletes=True.

## 5. Посты и комментарии: контракты и пагинация
- post_service.list_posts(page=1, per_page=POSTS_PER_PAGE) -> Pagination: db.paginate, error_out=False
  (за пределами total → пустой список, не 404); сортировка Post.created.desc(), Post.id.desc().
- WEB-лента: ?page — санитизация через общие хелперы pagination.py (→ ARC-0032);
  index.html — Bootstrap-навигация (has_prev/has_next/pages).
- API GET /api/posts — конверт: posts, page, pages, total, per_page (в конверте применённый
  per_page = pagination.per_page). Санитизация: page — мусор/<1 → 1; per_page — мусор/<1 → POSTS_PER_PAGE, > 50 → 50.
- Модель Post: body — сырой Markdown; comment_count — column_property со scalar subquery + correlate_except(Comment)
  (→ ARC-0037; N+1 счётчика убран).
- Markdown: blog/services/markdown.py — render_markdown: "" → ""; иначе nh3.clean(mistune-рендер); порядок
  обязателен (рендер, потом санитизация). _BootstrapRenderer: block_quote → class="blockquote".
  В шаблонах — только фильтр markdown и всегда |safe (вызов функции из шаблона — UndefinedError);
  update.html — сырой Markdown в textarea. teaser-фильтр удалён (лента обрезает CSS).
- Права на контент (посты и комментарии) — единая модель blog/services/permissions.py: ensure_allowed
  (author_id, actor, action, subject); Action.UPDATE/DELETE; автор — всё со своим; админ — только удаление
  чужого, одинаково в WEB и API; чужое редактирование — 403 (→ ARC-0038). Гварды в сервисах сняты
  (check_author удалён); порядок 404 → 403 — get_* до ensure_allowed. Гость: WEB 302 / API 401.
- Профиль /user/<username> — публичный; вкладки лент как ссылки: ?tab=posts|comments (мусор → posts), одна
  пагинация page внутри активной вкладки; get_profile(username, tab, page) отдаёт одну ленту через карту
  _FEEDS; новые разделы — строкой в карту (→ ARC-0039).
- Комментарии: Comment(id, post_id FK CASCADE, author_id FK CASCADE, body, created_at). Новые сверху —
  сортировка created.desc() с обязательным тайбрейком id.desc() (сортировка по created без id
  недетерминированна при массовом создании; → ARC-0040). Без Markdown — экранированный текст.
  Список комментариев поста: comment_service.list_for_post(post_id, page, per_page) → Pagination;
  COMMENTS_PER_PAGE = 10; API — конверт как у постов; ?page на странице поста листает комментарии
  (одна лента — один query-параметр; → ARC-0040).
- WEB-роуты постов: пустой/whitespace title — флеш с ошибкой; валидация body отсутствует осознанно.

## 6. Статика и JS
- static/css/blog.css: CSS-тизер (.post-clip 9rem, градиент, раскрытие через visually-hidden чекбокс) +
  анимация раскрытия (interpolate-size в @supports, prefers-reduced-motion; Firefox/Safari — мгновенное раскрытие);
  .post-clip img — max-width: 100% / height: auto (картинки в постах не выламывают вёрстку, → ARC-0033).
- Семь JS-файлов в static/:
  - autoclose_alerts.js — тосты .auto-close: появление через .show (re-flow хак offsetWidth), через 5 с снятие .show
    и удаление из DOM через 400 мс; уход по CSS-transition;
  - tooltip.js — bootstrap.Tooltip по `[data-bs-toggle="tooltip"]`;
  - confirm_action.js (→ ARC-0041, бывший confirm_delete.js) — #confirm-modal: разметка в base.html
    (data-bs-backdrop="static"; Escape закрывает модалку — осознанно, решение по итогам ручного тестирования);
    data-action (delete_post/user/comment, change_role) → CONFIRM_ACTIONS: заголовок, текст и подпись кнопки
    перезаписываются при каждом открытии (статичный текст base.html — заглушка); FALLBACK_* для действий без
    записи; форма через closest('form'), submit по кнопке модалки,
    открытие через Modal.getOrCreateInstance(modalEl).show(btn);
  - expand_post.js — пересчёт «fits» для .post-clip: замер scrollHeight от 9rem (rem из computed style), развёрнутый
    пост не мерится; слушатели change/resize + стартовый вызов;
  - md_editor_init.js — инициализация EasyMDE: #body, spellChecker/status off, minHeight 200px, кастомный toolbar
    (с эмодзи-кнопкой → ARC-0033); uploadImage: true + imageUploadFunction — загрузка через POST /uploads;
    константы MAX_IMAGE_SIZE/ACCEPTED_IMAGE_TYPES наверху файла — клиентские проверки размера и формата с русскими
    сообщениями (встроенные проверки EasyMDE обходятся кастомной функцией; imageMaxSize/imageAccept — декор);
    подключается в create.html/update.html.
  - emoji_list.js — набор эмодзи для пикера;
  - emoji_picker.js — fillEmojiPanel + авто-подключение по data-атрибутам
    (closest('form'); по одной форме на страницу — п. 14 бэклога).
- Шпаргалка Markdown у редактора (→ ARC-0042): partial blog/templates/blog/_cheatsheet.html — collapse-кнопка
  «Шпаргалка Markdown» после textarea #body в create.html/update.html (строкой {% include %}); 8 примеров
  в карточках «исходник → результат» (сетка row-cols-md-2), 7 рендерятся живым фильтром markdown | safe
  (справка самопроверяющаяся), пример картинки — raw-заглушка (битой иконки не быть); CSS-блок
  .md-cheatsheet-* в blog.css (плитки-карточки, НЕ flex в строку — разъезжалось); тесты test_web_cheatsheet.py:
  структурный якорь id="md-cheatsheet" + data-bs-target, отсутствие проверяется вне форм (→ ARC-0039).
- Тост-стек флеш-сообщений (.toast-stack в blog.css): fixed снизу по центру (left 50% + translateX), z-index 1045
  (ниже модалки 1055), ширина min(480px, 100vw - 2rem), transition-анимация появления/ухода, prefers-reduced-motion.
- Канон кастомного JS (→ ARC-0030): один файл = один самодостаточный виджет, подключается только там, где нужен; ось
  организации — точка загрузки, НЕ домен (слияние по домену тянуло бы код на все страницы). Граница пересмотра:
  общий код у файлов или 10+ файлов → modules/сборка. Шапка-комментарий с якорями и страницами подключения
  обязательна; 'use strict' первой строкой; именованные константы наверху файла; vanilla JS + публичный API
  Bootstrap; скрипты в конце <body> без defer — DOMContentLoaded не нужен; инлайн-скрипты в шаблонах запрещены;
  JS вне тестового покрытия осознанно (верификация — ручная проверка); ESLint не вводим.
- EasyMDE 2.21.0 (CDN, без SRI осознанно) — только в create.html/update.html.
- CDN Bootstrap 5.3.8 — с integrity (SRI).
- Кастомные CSS/JS — осознанное исключение из «чистого Bootstrap».
- Канон шаблонов: иконочная кнопка = тултип + aria-label; якоря data-action (видимый текст кнопок вне покрытия
  — trade-off); формы удаления без id.
- Аватар по умолчанию (→ ARC-0031): macros.html — макрос avatar(username) (первые 2 буквы логина, upper); CSS-класс
  .avatar в blog.css (кружок, --bs-secondary-bg/secondary, 2rem, margin-right 0.5rem, flex-shrink 0); показ: хедер
  (base.html), лента (index.html), пост+комментарии (view.html), админка (admin_users.html), профиль (profile.html).
  Импорт макроса один — в base.html, дочерние шаблоны наследуют контекст. Картинок нет; раскраска по хешу сделана
  (→ ARC-0037): blog/avatar.py — avatar_color(username), класс палитры avatar-palette-<md5>.
- Пагинация WEB-админки и админ-API (→ ARC-0032): USERS_PER_PAGE = 20 (константы — на сущность, не shared);
  blog/pagination.py — общие хелперы page_from_args/per_page_from_args(default)/tab_from_args(allowed, default)
  для WEB и API (первый общий WEB/API-код, рядом с constants.py); admin_service.list_users(page, per_page)
  → db.paginate по id возрастанию; /api/users теперь конверт {users, page, pages, total, per_page} (контракт
  изменён осознанно, тест переписан); admin/users.html — навигация под таблицей; санитизация ленты и постов
  переведена на общие хелперы.
- Изображения в постах и эмодзи (→ ARC-0033): UPLOAD_FOLDER (папка uploads/ рядом с instance, в .gitignore),
  MAX_CONTENT_LENGTH = 5 МБ; ALLOWED_IMAGE_EXTENSIONS и IMAGE_EXTENSION_ALIASES — в constants;
  uploads_service.save_image — белый список расширений + magic bytes (сигнатуры в сервисе: imghdr выпилен
  из Python), имя uuid4, путь только из сгенерированного имени (../ исключён по построению), расхождение
  расширения и сигнатуры — ошибка, не автозамена; + папка создаётся фабрикой create_app
  (mkdir parents=True, exist_ok=True) (→ ARC-0034); web/uploads.py: POST /uploads (login_required, JSON {url})
  и GET /uploads/<path> (публично, send_from_directory); EasyMDE унифицирован в md_editor_init.js
  (imageUploadFunction → POST /uploads, кнопка image) — инлайн-конфиг update.html удалён по канону ARC-0030;
  эмодзи — Unicode в тексте, нулевая серверная обработка; emoji_list.js (набор) + emoji_picker.js
  (fillEmojiPanel + авто-подключение по data-атрибутам); пикер на трёх формах: тулбар постов (create/update)
  и обе формы комментария (view, update); CLI clean-uploads — чистка сирот по UPLOAD_RE
  (комментарии не сканируются — plain text по дизайну).

## 7. Тестовая архитектура
- Структура tests/: constants/ (endpoints.py, web_endpoints.py), objects/ (user.py), preconditions/
  (app, users, posts, comments), tests/, tools/clients/ (api.py, api_user_facade.py, web_client.py,
  custom_flask_client.py), tools/asserters/ (base_asserters.py, soft_asserters.py), unit_tests/, conftest.py.
- Allure через glamor (`import glamor as allure`, не смешивать с import allure). Слои @epic → @feature → @story →
  @title; happy path — BLOCKER, валидация/отказы — CRITICAL; @title на фикстурах обязателен. Шаги «Актёр. Слой.
  действие»; актёр — от чьего лица (гость — без актёра; «БД.»/«ORM.» — без).
- AllureClient: аттачит запрос/ответ; тело запроса — из аргументов open ДО отправки (response.request нельзя —
  ClientDisconnected); маскируются authorization/cookie/password; внутренние редиректы (EnvironBuilder) не
  аттачатся; attach_traffic — флаг-атрибут класса (False отключает аттачи).
- setup_app: чистое приложение на тест, sqlite:///:memory:; контекст закрывается ДО yield, teardown — в собственном
  контексте (→ ARC-0009); ORM в теле теста — только внутри with setup_app.app_context().
- setup_app_client: app.test_client_class = AllureClient; возврат на return.
- create_user(app, app_client, username, password, role=Roles.USER): commit → refresh → attach/to_dict → expunge,
  возврат объекта без перезапроса (→ ARC-0034);
- UserObject: db_model, password, api_token (ленивое свойство — единственное место с ассертами вне теста),
  refresh_api_token(). user.api = ApiUserFacade, user.web = WebClient. Гостевые действия — чистые Api/WebClient;
  клиенты возвращают сырой ответ, без ассертов.
- Api — фасад с разделами (api.users.list/delete/change_role(token=...)); ApiUserFacade — методы от имени
  пользователя (change_user_role, ...), раздела .users у него НЕТ (→ ARC-0041). WebClient —
  .auth/.posts/.comments/.admin/.uploads/.users (.users.profile, .users.change_role).
- Фасад пользователя открывает все действия своей роли, включая пассивные чтения без токена (get_posts_list,
  get_comments_list); тонкая ретрансляция — контракт, не дублирование (→ ARC-0035).
- Канон фикстур: ORM-объекты — commit → refresh → attach/to_dict → expunge; после expunge — только скаляры
  колонок, связи нельзя; сериализация до expunge (→ ARC-0034).
- WEB-логин-предусловие — фикстура setup_logged_in_user(setup_test_user): титул «Пользователь. WEB. Авторизован»,
  шаг входа с самопроверкой assert_redirect, возврат UserObject; логин-как-предмет теста — явным шагом (→ ARC-0035).
- Временная папка — setup_tmp_dir (TemporaryDirectory), не tmp_path/tmp_path_factory (в отчёте нет внутренних
  фикстур pytest). Актёр и слой однослойной фикстуры — в @title, вложенные шаги без префиксов; многослойная
  фикстура описывает результат в титуле, шаги — по общему канону (→ ARC-0034).
- api.py: BaseClient (_post/_patch/_get/_delete; _get принимает query); фильтр «if value» — None и пустая строка
  не уходят в тело (осознанный контракт).
- Эндпоинты — dataclass-константы, шаблонные пути через .format(...). WebEndpoints.USER.CHANGE_ROLE.
  Ассертеры: assert_status_code, assert_condition, assert_redirect, SoftAssert (чеки внутрь SoftAssert —
  только с soft_assert=True, иначе исполняются сразу и вернут None; → ARC-0041).
- CLI: invoke_cli(app, command, args, hidden=()) — клик зовётся только через него. CLI — интерфейс, НЕ юнит.
  Юниты: tests/unit_tests/ — без Allure-обвязки; ветки, недостижимые через интерфейсы, безинтерфейсные места
  и гварды (регистрация CLI — test_cli_registration.py, → ARC-0043).
- WEB-канон: точные редиректы — assert_redirect (302 + Location одним шагом; отдельный GET с флешем сохраняется;
  → ARC-0035); исключения — негативная проверка «Location не ведёт наружу» и startswith(LOGIN) при гостевом next —
  на assert_status_code + assert_condition, асертер под особые случаи не подгоняется (вернуться к опциональному
  параметру при 5–6 таких местах); положительный контроль ДО проверки исчезновения; порядок списков — по точным
  спискам значений. Признак отсутствия сущности на странице — структурный (якорь карточки), не текстовый:
  текст сущности может легитимно присутствовать в ссылках чужих карточек (→ ARC-0039). Проверка набора
  сущностей — сравнением множеств, не генератором с двумя for (двойной for в all(...) — декартово
  произведение; → ARC-0040). Докстринги Google; фикстуры setup_*.

## 8. Процесс работы с AI
- Сессия: пользователь присылает ядро (оглавление архива — при необходимости); AI выдаёт обновлённую версию к
  концу сессии. Файлы не хранятся в контейнере — при потере просить у пользователя, не восстанавливать по памяти.
- Режим: план — названия шагов; один шаг за раз: правка → присылка модуля → проверка и актуализация → следующий шаг.
- Канон передачи — полные файлы: изменённый модуль выдаётся в чате целиком, пользователь заменяет файл на диске
  целиком; куски для патча не ищутся. Ядро — целиком в конце каждого раунда. Перед выдачей целого файла AI
  опирается на актуальную версию с диска: если есть ручные правки, не дошедшие до AI, файл запрашивается заново —
  ручные правки не теряются. Подтверждение сохранения — вложением файлов. Приложенный файл затирает одноимённый
  на диске. Сохранение подтверждается явно (→ ARC-0012, ARC-0015).
- Ruff — зона ответственности пользователя: AI не отслеживает замечания форматирования и линта (импорты, кавычки,
  стиль docstring и прочее, что проверяет Ruff) ни в патчах, ни в промежуточных прогонах; исключение — замечания
  с функциональными последствиями. В конце раунда пользователь приводит код в порядок и прогоняет Ruff;
  AI комментирует результат только если что-то сломалось.
- Длина строки .py/.md — 120 символов; html/js/css — по best-practices.
- Прогон исполняет код с диска, а не в голове; канон тестов сверять с эталонным модулем сессии.
- Уроки: факты — в сообщение ассерта, не в print; имена API сверять с документацией до кода. Диагностика:
  временные принты — рабочая практика, снимаются после фикса.
- Восстановимые данные (coverage, git, код) в контексте не хранятся.
- При напоминании о бэклоге сверять пункты с ядром — закрытые раунды из бэклога убирать в момент закрытия, не позже.
- Точечные прогоны: убедиться, что окружение не подхватило вторую копию проекта (чужой conftest на пути импорта);
  диагностика — трейсбек загрузки плагинов до коллекции (→ ARC-0039).

## 9. Бэклог
Правило напоминаний: при закрытии раунда AI напоминает об открытых пунктах; «сделано самим» — только с явного
подтверждения в чате.
2. Хвост пагинации: «Назад» за пределами total — украшение, «когда-нибудь» (слои закрыты: лента, посты-API,
   пользователи, комментарии → ARC-0032, ARC-0040).
3. Доработки комментариев: лайки + нюансы (формулировка позже).
5. Видео в постах: вставка с YouTube/VK, возможная кастомная MD-разметка.
6. Модульность приложения (python-модули): каркас «Обо мне» + устанавливаемые модули (WEB-auth, WEB-лента,
   API-auth, API-лента). Постановки нет.
8. Преобразование в персональный блог: посты — SuperAdministrator (хозяин) и Administrator; User — читает
   и комментирует; гость — читает.
10. Аватарки: картинки-аватары (раскраска по хешу сделана → ARC-0037).
11. Тесты WEB-пагинации админки: зеркальное трио TestIndexPagination (шаблон и роут готовы → ARC-0032,
    отдельных тестов нет — расхождение с каноном «каждая пагинация накрыта трио»).
12. Markdown в комментариях: сейчас plain text (закреплено тестом). Развилка: включить рендер через render_markdown +
    nh3 — честно подсадить EasyMDE на обе формы комментариев; НО меняется семантика существующих комментариев
    (старые **звёздочки** начнут рендериться). Решать отдельным раундом.
13. Загрузки: Image-модель (автор, привязка к постам) — чистка сирот перейдёт с регулярки на БД; автозамена
    расширения по magic bytes (PNG под именем .jpg сейчас даёт 400 — осознанный MVP). После модели — расширение
    прав на чужие загрузки в permissions.py (хвост ARC-0038).
14. Если две формы с пикером окажутся на одной странице — перевести emoji_picker.js на querySelectorAll с
    циклом (сейчас по одной форме).
15. Обработка изображений на сервере: сжатие/масштабирование при загрузке (Pillow) — чтобы «огромная по размеру
    картинка» перестала быть проблемой пользователя; возможно, миниатюры. Связано с п. 13 (Image-модель) —
    проектировать одним куском.
18. Профиль: базовая версия готова (→ ARC-0037), ленты на вкладках (→ ARC-0039). Осталось: журнал изменений
    сущностей; дифференциация данных (владелец — максимум, гость — ограниченно, админ — всё), реквизиты
    (кроме пароля). Новые разделы — строкой в карту _FEEDS.
20. WEB-тесты: кандидат setup_logged_in_admin; нюанс — test_menu_item_visibility меняет двух пользователей на
    одном клиенте, две «авторизованные» фикстуры на один клиент не расходятся без аккуратности (→ ARC-0035).
21. Вынести макрос pagination_nav в macros.html: три локальные копии (index, profile, view), рефакторинг
    шаблонов отдельным раундом (идея ARC-0040).

## 10. Текущее состояние
- Счёт (прогон 2026-11-20, вечер): 236 тестов; Ruff — ноль; покрытие 100% (903 stmts, 120 branch, BrPart 0).
- Последние раунды: → ARC-0038 → ARC-0039 → ARC-0040 → ARC-0041 → ARC-0042 → ARC-0043.
- Активных раундов нет. Allure-отчёты устраивают; за поведением glamor — наблюдение (скрытые teardown-шаги,
  «?» у несработавших постусловий).
