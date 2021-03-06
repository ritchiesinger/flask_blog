# Общее описание

[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/PyCQA/pylint)

Учебный проект для освоения фреймворка Flask.

Проект представляет собой сервис с REST API. Т.к цель исключительно образовательная, то составить перечень 
заявленных функциональностей не представляется возможным. 

На момент инициирующего коммита в сервисе реализована работа 
с пользователями и ролевая система. Дальнейшее развитие можно будет отслеживать в разделе `История изменений`, где 
будут перечисляться существенные вехи разработки.

# Установка и запуск

После клонирования репозитория устанавливаем зависимости:

```shell
pip install -e ./app
```

Далее запускаем приложение:
```shell
flask run
```

Если планируется не только запускать, но и разрабатывать, то рекомендуется запустить скрипт:

```shell
sh ./dep_install.sh
```

Он установит все необходимые зависимости как для запуска приложения, так и вспомогательные зависимости для разработки.
В частности имеется скрипт для проверки кода линтерами:

```shell
sh ./run_linters.sh
```

# История изменений

## 06.04.2022 - Начало работы над визуальной частью

- Добавлена папка web-app - проект на ReactJS;
- Реализована авторизация и выход, а также страница профиля (пока только на чтение);
- При авторизации учитывается ролевая модель.

## 03.04.2022 - Добавление автотестов

- В проект добавлена система отчётов автотестов **Allure Reports**;
- Организована структура хранения кода автотестов (шаги, предусловия, тестовые функции);
- Добавлено некоторео кол-во тестов.

## 29.03.2022 - Улучшение структуры проекта

[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/PyCQA/pylint)

- Реализован паттерн **Flask Blueprints**. Методы разложены структурно по модулям;
- Реализован паттерн **Flask Application Factory**;
- В проект добавлен `PyLint`. Проведён рефакторинг согласно замечаниям. Проставлены исключения, связанные со спецификой 
Flask. 

## 27.03.2022 - Инициирующий коммит

- Сервис умеет работать с пользователями и ролями;
- Ролевая система разграничивает доступ к методам API; 
- База данных для начала выбрана SQLite 

# Документация

Подробную документацию можно найти в [wiki](https://github.com/ritchiesinger/flask_blog/wiki)
