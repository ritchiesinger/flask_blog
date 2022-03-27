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

## Формат ответа

Ответ любого метода имеет вид:

```json
{
    "data": null,
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJKV1QiL..."
}
```

где в поле `data` может быть произвольная структура, в зависимости от вызываемого метода и возвращаемых данных. В 
ряде случаев `data` может быть пустой.

`error_code` - код ошибки. `0` считается успешным, остальные коды являются ошибками и сопровождаются `error_text` - 
словесным описанием ошибки. В случае успешного ответа `error_text` возвращается `null`.

При каждом запросе при успешном прохождении аутентификации генерируется новый токен, который возвращается в поле 
`token`.

## Аутентификация

В сервисе предусморено 2 вида аутентификации: 

- Basic Auth
- Bearer Token 

Все методы сервиса поддерживают оба вида (кроме метода /api/token - он вызывается только с Basic Auth).

### GET /api/token

Метод для получения Bearer Token. Метод авторизованный.

#### Пример запроса

```shell
GET /api/token
```
#### Пример ответа
```json
{
    "data": {
        "user_roles": [
            "user",
            "admin"
        ]
    },
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1Ni..."
}
```

## Управление пользователями (Администратор)

Методы сервиса предназначенные для пользователей с ролью Администратор для управления пользователями.

### GET /api/admin/users/<user_id>

Метод для получения данных о профиле любого пользователя.

#### Пример запроса

```shell
GET /api/admin/users/3
```

#### Пример ответа

```json
{
    "data": {
        "email": "ritchie12@mail.ru",
        "id": 2,
        "login": "ritchie_singer",
        "roles": [
            "user",
            "admin"
        ]
    },
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJKV1QiLCJhb..."
}
```

### GET /api/admin/users

Метод для поиска пользователей с фильтрацией. Параметры-фильтры передаются в URL, являются подстроками по которым будет 
производиться поиск. Доступны:

- `email`. Адрес электронной почты.
- `login`. Имя учётной записи пользователя.

Также есть возможность управлять размером выдачи (пагинация):

- `per_page`. Сколько результатов будет на странице.
- `page`. Запрашиваемая страница. Если запрашиваемая страница не существует (нет столько страниц в выдаче), то 
вернётся последняя возможная.

#### Пример запроса

```shell
GET /api/admin/users?email=ritchie&login=singer&page=3&per_page=10
```

#### Пример ответа

```json
{
    "data": {
        "page": 1,
        "per_page": 10,
        "total_pages": 1,
        "total_users_found": 2,
        "users": [
            {
                "email": "ritchie12@mail.ru",
                "id": 2,
                "login": "ritchie_singer",
                "roles": [
                    "user",
                    "admin"
                ]
            },
            {
                "email": "ritchie1@mail.ru",
                "id": 3,
                "login": "ritchie",
                "roles": [
                    "user"
                ]
            }
        ]
    },
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJKV1QiLCJhb..."
}
```

### PUT /api/admin/users/<user_id>

Изменение профиля пользователя с перезаписью всех доступных для изменения полей профиля.

#### Пример запроса

```shell
PUT /api/admin/users/3
```
с телом:
```json
{
    "login": "ritchie1",
    "email": "ritchie1@mail.ru"
}
```

#### Пример ответа

```json
{
    "data": null,
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJKV1QiL..."
}
```

### PATCH /api/admin/users/<user_id>

Частичное изменение профиля пользователя.

#### Пример запроса

```shell
PATCH /api/admin/users/3
```
с телом:
```json
{
    "email": "ritchie1@mail.ru"
}
```

#### Пример ответа

```json
{
    "data": {
        "email": "ritchie1@mail.ru",
        "id": 3,
        "login": "ritchie22311",
        "roles": [
            "user"
        ]
    },
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiO..."
}
```

### DELETE /api/admin/users/<user_id>

Удаление профиля пользователя.

#### Пример запроса

```shell
DELETE /api/admin/users/3
```

#### Пример ответа

```json
{
    "data": null,
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJKV1QiL..."
}
```

## Управление ролями (Администратор)

### POST /api/admin/role

Создание роли.

#### Пример запроса

```shell
POST /api/admin/role
```
с телом:

```json
{
    "name": "test_role",
    "description": "qwerty"
}
```
#### Пример ответа

```json
{
    "data": {
        "id": 4,
        "name": "test_role"
    },
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiO..."
}
```

### GET /api/admin/role/<role_id>

Получение информации о роли.

#### Пример запроса

```shell
GET /api/admin/role/3
```

#### Пример ответа

```json
{
    "data": {
        "description": "asdfasdfasdfasdf",
        "id": 3,
        "name": "some_nam"
    },
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJKV1..."
}
```

### PUT /api/admin/role/<role_id>

Изменение роли с перезаписью всех доступных для редактирования полей.

#### Пример запроса

```shell
PUT /api/admin/role/3
```
с телом:

```json
{
    "name": "test_role",
    "description": "qwerty"
}
```
#### Пример ответа

```json
{
    "data": null,
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJ..."
}
```

### PATCH /api/admin/role/<role_id>

Редактирование роли (частичное изменение).

#### Пример запроса

```shell
PUT /api/admin/role/3
```
с телом:

```json
{
    "name": "test_role"
}
```
#### Пример ответа

```json
{
    "data": {
        "description": "asdfasdfasdfasd11f",
        "id": 3,
        "name": "some_nam"
    },
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJK..."
}
```

### DELETE /api/admin/role/<role_id>

Удаление роли.

#### Пример запроса

```shell
DELETE /api/admin/role/3
```

#### Пример ответа

```json
{
    "data": null,
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJKV1QiL..."
}
```

### POST /api/admin/role_assignment

Назначение роли.

#### Пример запроса

```shell
POST /api/admin/role_assignment
```

с телом:

```json
{
    "user_id": 3,
    "role_id": 4
}
```

#### Пример ответа

```json
{
    "data": null,
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJKV1QiL..."
}
```

### DELETE /api/admin/role_assignment

Снятие роли.

#### Пример запроса

```shell
DELETE /api/admin/role_assignment
```

с телом:

```json
{
    "user_id": 3,
    "role_id": 4
}
```

#### Пример ответа

```json
{
    "data": null,
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJKV1QiL..."
}
```

## Работа с пользователем (Пользователь)

### POST /api/registration

Регистрация новой учётной записи пользователя. Не требует авторизации.

#### Пример запроса

```shell
POST /api/registration
```
с телом:

```json
{
    "login": "Horacio_Block",
    "password": "qwerty",
    "email": "Teagan.Abbott42@hotmail.com"
}
```
#### Пример ответа

```json
{
    "data": {
        "email": "Teagan.Abbott42@hotmail.com",
        "id": 8,
        "login": "Horacio_Block"
    },
    "error_code": 0,
    "error_text": null
}
```

### GET /api/user

Получение текущей (своей) учётной записи.

#### Пример запроса

```shell
GET /api/user
```

#### Пример ответа

```json
{
    "data": {
        "email": "ritchie12@mail.ru",
        "id": 2,
        "login": "ritchie_singer",
        "roles": [
            "user",
            "admin"
        ]
    },
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJK..."
}
```
### PUT /api/user

Изменение всего профиля текущего пользователя (всех доступных для редактирования полей)

#### Пример запроса

```shell
PUT /api/user
```
с телом:

```json
{
    "login": "ritchie_singer",
    "email": "ritchie11111@mail.ru"
}
```
#### Пример ответа

```json
{
    "data": null,
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJ..."
}
```

### PATCH /api/user

Редактирование текущей учётной записи (частичное изменение).

#### Пример запроса

```shell
PUT /api/user
```
с телом:

```json
{
    "email": "ritchie12@mail.ru"
}
```
#### Пример ответа

```json
{
    "data": {
        "email": "ritchie1222@mail.ru",
        "id": 2,
        "login": "ritchie_singer",
        "roles": [
            "user",
            "admin"
        ]
    },
    "error_code": 0,
    "error_text": null,
    "token": "eyJ0eXAiOiJK..."
}
```
