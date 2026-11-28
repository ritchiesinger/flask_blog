# Карта структуры проекта: blog (Flask)

Назначение: единственная точка истины «где что лежит и что делает». Разделение труда с ядром (docs/ai-context.md):
карта отвечает на «где и что», ядро — на «почему так, каноны и что нельзя». Аннотация — одна строка на модуль;
→ ARC-NNNN — детали решения в архиве (docs/ai-context-archive.md).
Протокол: прикладывается к сессии вместе с активным контекстом (ai-context.md или ai-context-testing.md, → ARC-0060); обновляется в конце раунда вместе с ядром (целиком).
Сознательно не показаны: .venv/, instance/, uploads/ (рядом с instance), кэши и артефакты прогонов
(__pycache__, .pytest_cache, allure-результаты, htmlcov). Каталог migrations/versions фиксированный — список
версий не аннотируется, он растёт с моделями.

├── 📁 blog
│   ├── 📁 api                            — тонкие JSON-роуты; декоратор @api_errors сверху (→ ARC-0006)
│   │   ├── 📄 __init__.py                — blueprint api
│   │   ├── 📄 admin.py                   — GET /api/users, DELETE /api/users/<id> (→ ARC-0021, ARC-0032)
│   │   ├── 📄 auth.py                    — POST /api/token (401 напрямую dict), POST /api/register → 201
│   │   ├── 📄 comments.py                — API комментариев: list/create/update/delete, конверт как у постов (→ ARC-0040)
│   │   ├── 📄 decorators.py              — @api_errors, @role_required(*roles) (→ ARC-0041)
│   │   ├── 📄 errors.py                  — маппинг ServiceError → JSON {'error': ...} со статусом
│   │   └── 📄 posts.py                   — API постов: конверт {posts, page, pages, total, per_page} (→ ARC-0026, ARC-0027)
│   ├── 📁 models
│   │   ├── 📄 __init__.py                — сборка моделей
│   │   ├── 📄 comment.py                 — Comment: FK CASCADE на post/author (→ ARC-0022, ARC-0040)
│   │   ├── 📄 image.py                   — Image + привязка к постам (sync_all_post_links) (→ ARC-0044)
│   │   ├── 📄 post.py                    — Post: body — сырой Markdown; comment_count column_property (→ ARC-0037)
│   │   └── 📄 user.py                    — User: Roles, avatar_filename, display_name (→ ARC-0051)
│   ├── 📁 services                       — вся бизнес-логика; ошибки — только классами base_errors
│   │   ├── 📄 admin_service.py           — list_users/delete_user(user_id, actor), сервисный гвард defense-in-depth (→ ARC-0021)
│   │   ├── 📄 auth_service.py            — authenticate/register_user; пустое имя/короткий пароль → BadRequest, дубль → Conflict
│   │   ├── 📄 avatar_service.py          — сохранение аватара: квадрат, пережатие AVATAR_SIZE/SMALL, папка при записи (→ ARC-0051)
│   │   ├── 📄 base_errors.py             — ServiceError (500) → NotFound/Forbidden/BadRequest/Conflict (404/403/400/409)
│   │   ├── 📄 comment_service.py         — list_for_post/get/create/update/delete → Pagination (→ ARC-0040)
│   │   ├── 📁 markdown                   — пакет Markdown-рендера; mistune → nh3 — порядок обязателен
│   │   │                                   (→ ARC-0015, ARC-0050); распил монолита → ARC-0058
│   │   │   ├── 📄 __init__.py            — контракты render_markdown / render_markdown_basic, реестр _PLUGINS
│   │   │   │                               (собирается из модулей пакета), nh3-карты двух уровней (→ ARC-0058)
│   │   │   ├── 📄 blocks.py              — плагины раунда С: :::img (whitelist классов), :::gallery, :::carousel
│   │   │   │                               (→ ARC-0057, тесты → ARC-0059); токен broken — общий для обоих контейнеров
│   │   │   ├── 📄 core.py                — _BootstrapRenderer/_BasicRenderer, build_extended_renderer (→ ARC-0050)
│   │   │   └── 📄 video.py               — плагин :::video: YouTube/VK/RuTube (→ ARC-0052, ARC-0056)
│   │   ├── 📄 permissions.py             — ensure_allowed: единая модель прав контента (→ ARC-0038)
│   │   ├── 📄 post_service.py            — CRUD постов + sync_all_post_links (→ ARC-0044, ARC-0054)
│   │   ├── 📄 uploads_service.py         — save_image: whitelist расширений + magic bytes, имя uuid4 (→ ARC-0044)
│   │   └── 📄 user_service.py            — change_role/change_display_name с гвардами (→ ARC-0041, ARC-0053)
│   ├── 📁 static
│   │   ├── 📄 autoclose_alerts.js        — тосты .auto-close: показ 5 с, уход по transition (→ ARC-0029)
│   │   ├── 📄 avatar_crop.js             — кроп-виджет аватара, только profile.html (→ ARC-0051)
│   │   ├── 📄 blog.css                   — тизер ленты, тост-стек, шпаргалка, аватары, .video-embed 16:9 для
│   │   │                                   :::video, .gallery-grid — grid-сетка :::gallery (→ ARC-0016, ARC-0045,
│   │   │                                   ARC-0052, ARC-0057)
│   │   ├── 📄 confirm_action.js          — #confirm-modal, CONFIRM_ACTIONS, form через closest (→ ARC-0020, ARC-0041)
│   │   ├── 📄 emoji_list.js              — набор эмодзи пикера (→ ARC-0033)
│   │   ├── 📄 emoji_picker.js            — fillEmojiPanel: наполнение панели; вызывается тулбаром EasyMDE
│   │   │                                   (→ ARC-0033, ARC-0050: textarea-механизм снят)
│   │   ├── 📄 expand_post.js             — fits тизера, замер scrollHeight (→ ARC-0045, ARC-0048)
│   │   ├── 📄 favicon.ico                — иконка сайта
│   │   ├── 📄 md_editor_init.js          — EasyMDE для постов (#body) и комментариев ([data-mde="comment"]);
│   │   │                                   загрузка изображений — только посты (→ ARC-0044, ARC-0047, ARC-0050)
│   │   └── 📄 tooltip.js                 — bootstrap.Tooltip по data-bs-toggle (→ ARC-0018)
│   ├── 📁 templates
│   │   ├── 📁 admin
│   │   │   └── 📄 users.html             — WEB-админка: таблица + пагинация (→ ARC-0021, ARC-0032)
│   │   ├── 📁 auth
│   │   │   ├── 📄 login.html             — вход (next-защита → ARC-0035)
│   │   │   └── 📄 register.html          — регистрация
│   │   ├── 📁 blog
│   │   │   ├── 📄 _cheatsheet.html       — шпаргалка Markdown, живой рендер; 8 примеров, восьмая — видео;
│   │   │   │                               примеры — источники из РФ (RUPixel, VK → ARC-0057) (→ ARC-0042, ARC-0052)
│   │   │   ├── 📄 comment_update.html    — форма правки комментария: EasyMDE (→ ARC-0022, ARC-0050)
│   │   │   ├── 📄 create.html            — форма поста: EasyMDE + шпаргалка (→ ARC-0015)
│   │   │   ├── 📄 index.html             — лента: тизер, карточки, навигация (→ ARC-0016)
│   │   │   ├── 📄 profile.html           — профиль: вкладки, кроп, role-контролы (→ ARC-0039, ARC-0051)
│   │   │   ├── 📄 update.html            — форма правки: сырой Markdown в textarea (→ ARC-0015)
│   │   │   └── 📄 view.html              — страница поста: комментарии (markdown_basic), EasyMDE-форма
│   │   │                                   комментария (→ ARC-0050)
│   │   ├── 📁 errors
│   │   │   ├── 📄 404.html               — фирменная 404 (ловит и роутинг, и NotFoundError)
│   │   │   └── 📄 500.html               — фирменная 500
│   │   ├── 📄 base.html                  — каркас: хедер, тосты, модалка, импорт макросов
│   │   └── 📄 macros.html                — avatar(user, size), pagination_nav(pagination, endpoint):
│   │                                       disabled-стрелки с tabindex/aria-disabled (→ ARC-0046, ARC-0051, ARC-0061)
│   ├── 📁 web                            — тонкие HTML-роуты; @web_errors; гость → 302, не-админ → 404
│   │   ├── 📄 __init__.py                — blueprint web
│   │   ├── 📄 admin.py                   — GET /admin/users, POST /admin/users/<id>/delete (→ ARC-0021)
│   │   ├── 📄 auth.py                    — логин/регистрация/выход, open redirect закрыт (→ ARC-0035)
│   │   ├── 📄 blog.py                    — лента, view, create/update/delete (→ ARC-0003)
│   │   ├── 📄 errors.py                  — @web_errors: ServiceError → flash/redirect
│   │   ├── 📄 uploads.py                 — POST /uploads (login_required), GET /uploads/<path> публично (→ ARC-0033)
│   │   └── 📄 user.py                    — профиль, role, display_name, avatar (→ ARC-0039, ARC-0051)
│   ├── 📄 __init__.py                    — фабрика create_app: blueprints, extensions, loaders, errorhandler 404/500,
│   │                                       413-хендлер, add_command всех CLI, фильтры markdown/markdown_basic (→ ARC-0008, ARC-0041, ARC-0050)
│   ├── 📄 avatar.py                      — avatar_color(username): детерминированный оттенок по MD5 (не hash() —
│   │                                       тот нестабилен между запусками), класс палитры blog.css (→ ARC-0037)
│   ├── 📄 cli.py                         — все CLI: make-admin, create-admin, clean-uploads, make-superadmin,
│   │                                       delete-user (→ ARC-0033, ARC-0041)
│   ├── 📄 config.py                      — конфигурация: SQLALCHEMY, MAX_CONTENT_LENGTH = 64 МБ
│   ├── 📄 constants.py                   — общие константы: пагинации, Roles, ролевые карты, PROFILE_TABS (→ ARC-0043)
│   ├── 📄 extensions.py                  — db, login_manager, jwt, naming convention FK CASCADE (→ ARC-0041)
│   ├── 📄 loaders.py                     — user_loader + user_lookup_loader; живой, НЕ удалять (→ ARC-0009)
│   └── 📄 pagination.py                  — page_from_args/per_page_from_args/tab_from_args, WEB и API (→ ARC-0032)
├── 📁 docs
│   ├── 📄 ai-context-archive.md          — архив раундов ARC-NNNN, оглавление в шапке
│   ├── 📄 ai-context-testing.md          — контекст тестирования: каноны тестов, инфраструктура (→ ARC-0060)
│   ├── 📄 ai-context.md                  — ядро контекста: решения, каноны, бэклог
│   └── 📄 project_structure.md           — карта структуры (этот файл); обновляется в конце раунда вместе с ядром
├── 📁 migrations
│   ├── 📁 versions                       — 4 миграции; каталог фиксированный, список растёт с моделями
│   ├── 📄 alembic.ini
│   ├── 📄 env.py
│   ├── 📄 README
│   └── 📄 script.py.mako
├── 📁 tests
│   ├── 📁 constants
│   │   ├── 📄 endpoints.py               — API-эндпоинты: dataclass-константы, .format(...) (→ ARC-0005)
│   │   └── 📄 web_endpoints.py           — WEB-эндпоинты: WebEndpoints.USER.* (→ ARC-0053)
│   ├── 📁 objects
│   │   └── 📄 user.py                    — UserObject: db_model, password, client (публичный → ARC-0061),
│   │                                       api_token, .api/.web фасады (→ ARC-0005)
│   ├── 📁 preconditions                  — фикстуры-предусловия, плагины conftest (→ ARC-0034)
│   │   ├── 📄 __init__.py
│   │   ├── 📄 app_preconditions.py       — setup_app, setup_app_client, setup_tmp_dir
│   │   ├── 📄 comments_preconditions.py  — создание комментариев
│   │   ├── 📄 posts_preconditions.py     — создание постов
│   │   └── 📄 users_preconditions.py     — create_user, setup_logged_in_user (→ ARC-0035),
│   │                                       setup_logged_in_admin (→ ARC-0061)
│   ├── 📁 tests                          — интерфейсные тесты (API/WEB/CLI), Allure-обвязка; 362 прогона
│   │   └── 📄 test_*.py                  — по доменам: api_*, web_*, cli_*, *_service/model
│   ├── 📁 tools
│   │   ├── 📁 asserters
│   │   │   ├── 📄 base_asserters.py      — assert_status_code/condition/redirect (→ ARC-0041)
│   │   │   └── 📄 soft_asserters.py      — SoftAssert (→ ARC-0041)
│   │   ├── 📁 clients
│   │   │   ├── 📄 api.py                 — Api фасад + BaseClient (→ ARC-0035)
│   │   │   ├── 📄 api_user_facade.py     — ApiUserFacade: действия от имени пользователя (→ ARC-0041)
│   │   │   ├── 📄 custom_flask_client.py — AllureClient: аттач запрос/ответ, маскировка (→ ARC-0035)
│   │   │   └── 📄 web_client.py          — WebClient: .auth/.posts/.comments/.admin/.uploads/.users (→ ARC-0053)
│   │   ├── 📄 cli_tools.py               — invoke_cli: запуск click-команды в app_context + аттач команды
│   │   │                                   и вывода в Allure, маскировка паролей hidden
│   │   └── 📄 image_factory.py           — генерация тестовых изображений (→ ARC-0044)
│   ├── 📁 unit_tests                     — юниты с Allure-обвязкой (минимум epic/feature/story → ARC-0059):
│   │   │                                   гварды, ветки вне интерфейсов (→ ARC-0006); 66 прогонов
│   │   └── 📄 test_*.py                  — test_cli_registration, test_markdown_video (26 юнитов :::video),
│   │                                       test_markdown_blocks (40 юнитов блоков раунда С; → ARC-0043, ARC-0052,
│   │                                       ARC-0056, ARC-0057, ARC-0059)
│   ├── 📄 __init__.py                    — пакет tests (→ ARC-0054: без него bare pytest ломает импорты)
│   └── 📄 conftest.py                    — PRAGMA foreign_keys=ON, pytest_plugins = tests.preconditions.* (→ ARC-0054)
├── 📄 .gitignore                         — uploads/, кэши, instance
└── 📄 pyproject.toml                     — ruff (line-length 120, py315, E/F/I/UP/B/Q/D), coverage (branch, source=blog)
