# Общее описание
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

# История изменений

## 27.03.2022 - Инициирующий коммит

- Сервис умеет работать с пользователями и ролями;
- Ролевая система разграничивает доступ к методам API; 
- База данных для начала выбрана SQLite 

# Документация

Подробную документацию можно найти в [wiki](https://github.com/ritchiesinger/flask_blog/wiki)