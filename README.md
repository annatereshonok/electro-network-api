# Electro Network API

Онлайн-платформа торговой сети электроники.  
Django + DRF + PostgreSQL + Celery + Redis.  
Реализует иерархию звеньев сети (завод/розница/ИП) с поставщиком, продуктами и учётом задолженности.

## Содержание
- [Функционал по ТЗ](#функционал-по-тз)
- [Технический стек](#технический-стек)
- [Быстрый старт (Docker)](#быстрый-старт-docker)
- [Ручной старт (Poetry)](#ручной-старт-poetry)
- [Модели данных](#модели-данных)
- [Валидации и инварианты](#валидации-и-инварианты)
- [Админка](#админка)
- [API](#api)
- [Права доступа](#права-доступа)
- [Планировщик и фоновые задачи](#планировщик-и-фоновые-задачи)
- [Сидинг и суперюзер](#сидинг-и-суперюзер)
- [Структура проекта](#структура-проекта)

---

## Функционал по ТЗ
- Иерархия **звеньев сети** из трёх уровней: завод (уровень 0), розничная сеть, ИП.  
  **Важное правило:** уровень определяется **цепочкой поставщика** (`supplier`), а не названием.
- У каждого звена:
  - название и контакты (email, страна/город/улица/дом),
  - поставщик (`supplier` → `Unit`),
  - список продуктов (M2M `Product`),
  - **задолженность перед поставщиком** (`debt_to_supplier`, Decimal, до копеек),
  - дата создания.
- **Админка**: список/деталь, фильтр по городу, ссылка на поставщика, `admin action` «очистить задолженность».
- **API (DRF)**:
  - CRUD по `Unit` (поле `debt_to_supplier` — **read-only в API**),
  - фильтрация по стране,
  - схема Swagger/Redoc.
- **Доступ к API**: только **активные сотрудники** (is_active & is_staff).  
  Аутентификация — JWT (SimpleJWT).

---

## Технический стек
- Python 3.11+, Django 5, DRF, django-filter
- PostgreSQL 16, `psycopg2-binary`
- Celery 5, Redis 7
- SimpleJWT, drf-spectacular (+ sidecar)
- Poetry, Docker Compose

---

## Быстрый старт (Docker)

1) Скопируйте окружение:
```bash
cp .env.example .env
```
Отредактируйте `SECRET_KEY`, логины БД/почты при необходимости.

2) Поднимите стек:
```bash
docker compose up --build
```
- применятся миграции,
- (опц.) создастся суперюзер,
- (опц.) зальются демо-данные.

3) Откройте:
- API: `http://localhost:8000/`
- Документация API (Swagger): `http://localhost:8000/api/docs/`
- Схема OpenAPI: `http://localhost:8000/api/schema/`
- Админка: `http://localhost:8000/admin/`

4) Логин:
- JWT: получите токен по `POST /api/auth/token/` (staff-пользователь).
- Админка: email и пароль суперюзера из `.env`.

Остановить:
```bash
docker compose down
```
Снести БД-том:
```bash
docker compose down -v
```

---

## Ручной старт (Poetry)

```bash
poetry install
cp .env.example .env
poetry run python manage.py migrate
poetry run python manage.py ensure_superuser --email admin@example.com --password pass12345
poetry run python manage.py seed_demo
poetry run python manage.py runserver
```

---

## Модели данных

### `Product`
- `name`, `model` (уникальны в паре), `released_at` (дата выхода).

### `Unit`
- `name`, `kind` (`factory`/`retail`/`sp`), `email` (CI-unique), адресные поля,
- `supplier` → FK на `Unit` (parent), `clients` — related_name (дети),
- `products` — M2M на `Product`,
- `debt_to_supplier` — Decimal,
- `created_at`,
- `level` — вычисляемый по цепочке `supplier`.

---

## Валидации и инварианты
В **модели** (`clean()` + `save(full_clean)`):
- нормализация email → `lower()`,
- **регистронезависимая уникальность** email (`UniqueConstraint(Lower("email"))`),
- **завод не имеет поставщика** (если включено),
- запрет **самоссылки** и **длинных циклов** по `supplier` (обход вверх).

На уровне БД:
- `CheckConstraint`: запрет самоссылки (`id <> supplier_id`).

В **сериализаторах** (дружелюбные ошибки 400):
- `validate_email`: CI-unique заранее,
- `validate_supplier`: ранний запрет самоссылки/циклов.

---

## Админка
- Список/деталь `Unit` и `Product`.
- **Ссылка на поставщика** в детальной.
- **Фильтр по городу**.
- Admin Action «Очистить задолженность» — обнуляет `debt_to_supplier` выбранным объектам.

---

## API
Базовые маршруты (пример):

```
/api/units/           [GET, POST]
/api/units/{id}/      [GET, PATCH, PUT, DELETE]
/api/products/        [GET, POST]   (или ReadOnly — по необходимости)
```

Фильтрация:
- `GET /api/units/?country=DE` — по стране (через `django-filter`).

Схема и доки:
- OpenAPI: `/api/schema/`
- Swagger UI: `/api/docs/`

### Сериализаторы
`UnitSerializer`:
- **Чтение**: вложенные `products` (объекты),
- **Запись**: `product_ids` (список PK) → назначаются через `.set(...)` (PATCH не прислал — не трогаем; прислал `[]` — очищаем).

Поле `debt_to_supplier` — **read-only в API** (по ТЗ). Меняется через админку или служебные механики (платежи/таски).

### Аутентификация и выдача токена
- `POST /api/auth/token/` — получить `access/refresh` (SimpleJWT).
- `POST /api/auth/token/refresh/`.

---

## Права доступа
По умолчанию:
- `DEFAULT_PERMISSION_CLASSES = [IsAdminUser]`
- Доступ к API только у **активных сотрудников** (`is_active=True`, `is_staff=True`).

Регистрации (signup) **нет**.

---

## Планировщик и фоновые задачи
Celery + Redis.

Пример таски: уведомления должников по email с автоповторами.
- Worker: `celery -A config worker`
- Beat: `celery -A config beat` 
---

## Сидинг и суперюзер
Команды:
- `python manage.py seed_demo [--reset]` — заливает фиксированные демо-данные.
- `python manage.py ensure_superuser --email ... --password ... [--username ...]` — создаёт/обновляет суперюзера **идемпотентно**.

В Docker-старте (`entrypoint.sh`) оба шага можно включать/выключать флагами `.env`.

---

## Структура проекта
```
.
├── config/
│   ├── settings.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── urls.py
│   ├── celery.py
│   └── __init__.py
├── network/
│   ├── models.py
│   ├── admin.py
│   ├── tasks.py
│   ├── apps.py
│   ├── api/
│   │   ├── serializers.py
│   │   ├── permissions.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── management/
│   │   └── commands/
│   │       ├── ensure_superuser.py
│   └──     └── seed_demo.py
├── docker/entrypoint.sh
├── docker/Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```
