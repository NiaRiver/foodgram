# Foodgram

## Где каждый рецепт — как искусство
### Стасус CI/CD
[![Main Foodgram Workflow](https://github.com/NiaRiver/foodgram/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/NiaRiver/foodgram/actions/workflows/main.yml) - CI/CD для main branch

### Используемые технологии
#### Backend
![Static Badge](https://img.shields.io/badge/Django-grey?style=plastic&logo=django&logoColor=white&labelColor=green) - Django  
![Static Badge](https://img.shields.io/badge/PostgreSQL-grey?style=plastic&logo=Postgresql&logoColor=white&labelColor=blue) - PostgreSQL  
![Static Badge](https://img.shields.io/badge/Django%20Rest%20Framework-grey?style=plastic&logo=API&logoColor=white&label=DRF&labelColor=red) - Django Rest Framework  
#### Frontend
![Static Badge](https://img.shields.io/badge/React-gray?style=plastic&logo=react&labelColor=blue) - ReactJS  
![Static Badge](https://img.shields.io/badge/JavaScript-gray?style=plastic&logo=JavaScript&labelColor=yellow) - JavaScript  
#### Infrastructure
![Static Badge](https://img.shields.io/badge/NginX-gray?style=plastic&logo=nginx&labelColor=green) - NginX  
![Static Badge](https://img.shields.io/badge/docker-grey?style=plastic&logo=docker&logoColor=white&labelColor=blue) - Docker  

### Ссылка на сайт
<https://nia-foodgram.hopto.org/>

### Оглавления и навигация

- [Foodgram](#foodgram)
  - [Как запустить проект с помощью Docker Compose](#как-запустить-проект-с-помощью-docker-compose)
  - [Выполнить команды](#выполнить-команды)
    - [Запуск оркестра](#запуск-оркестра)
    - [Загрузка подготовленных данных](#загрузка-подготовленных-данных)
  - [Описание проекта](#описание-проекта)
  - [Фудграм](#фудграм)
  - [Возможности проекта](#возможности-проекта)
  - [Страницы проекта](#проект-состоит-из-следующих-страниц)
    - [Главная](#главная)
    - [Страница регистрации](#страница-регистрации)
    - [Страница входа](#страница-входа)
    - [Статические страницы](#статические-страницы)
    - [Страница рецепта](#страница-рецепта)
    - [Страница пользователя](#страница-пользователя)
    - [Страница подписок](#страница-подписок)
    - [Избранное](#избранное)
    - [Список покупок](#список-покупок)
    - [Создание и редактирование рецепта](#создание-и-редактирование-рецепта)
    - [Страница смены пароля](#страница-смены-пароля)
    - [Фильтрация по тегам](#фильтрация-по-тегам)
    - [Смена аватара](#смена-аватара)
    - [Разграничение прав](#разграничение-прав)
  - [API Эндпоинты](#api-эндпоинты)
  - [Основные эндпоинты](#основные-эндпоинты)
    - [Пользователи](#пользователи)
    - [Рецепты](#рецепты)
    - [Теги](#теги)
    - [Ингредиенты](#ингредиенты)
    - [Аутентификация](#аутентификация)
  - [Документация Redoc](#документация-redoc)
  - [Автор](#автор)
    - [NIA River](#nia-river)

## Как запустить проект с помощью Docker Compose

Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone https://github.com/NiaRiver/foodram.git
```

```bash
cd foodgram
```

## Выполнить команды

### Запуск оркестра

```bash
sudo docker-compose -f infra/docker-compose.yml up -d
```

### Загрузка подготовленных данных

```bash
sudo docker-compose -f infra/docker-compose.yml exec backend python /app/manage.py load_ingredients.py ../prepared_data/ingredients.json
sudo docker-compose -f infra/docker-compose.yml exec backend python /app/manage.py load_tags.py ../prepared_data/tags.json
```

## Описание проекта

## Фудграм

**Фудграм** — это онлайн-платформа для кулинарного вдохновения, где пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированные пользователи также могут пользоваться сервисом «Список покупок», который помогает собирать продукты для приготовления блюд.

## Возможности проекта

Фудграм предлагает вам:

- **Главную страницу** с самыми свежими рецептами, которые обновляются каждый день.
- **Удобный интерфейс** для регистрации и входа, чтобы вы могли сразу приступить к кулинарному вдохновению.
- **Детальные страницы рецептов**, где вы можете узнать все секреты приготовления и сохранить понравившиеся блюда в избранное.
- **Личную страницу пользователя** с возможностью редактирования своих рецептов и управления подписками.
- **Список покупок**, который автоматически формируется по вашим рецептам и позволяет легко подготовиться к готовке.
- **Функцию подписок**, чтобы вы могли быть в курсе новых рецептов от ваших любимых авторов.

Погружайтесь в мир гастрономического удовольствия с Фудграм и создавайте свои кулинарные шедевры вместе с нами!

## Проект состоит из следующих страниц

- Главная
- Страница входа
- Страница регистрации
- Страница рецепта
- Страница пользователя
- Страница подписок
- Избранное
- Список покупок
- Создание и редактирование рецепта
- Страница смены пароля
- Статические страницы «О проекте» и «Технологии»

### Главная

Содержимое главной — список первых шести рецептов, отсортированных по дате публикации «от новых к старым». На этой странице подразумевается постраничная пагинация. Остальные рецепты должны быть доступны на следующих страницах.

### Страница регистрации

Проект предоставляет систему регистрации и аутентификации пользователей. Обязательные поля для пользователя при регистрации: имя, фамилия, имя пользователя (никнейм), адрес электронной почты и пароль.

### Страница входа

После регистрации пользователь переадресовывается на страницу входа.

### Статические страницы

Проект предусматривает как минимум две статические страницы: «О проекте» и «Технологии». По умолчанию эти страницы отключены, и по их адресу отображается страница с ошибкой 404.

### Страница рецепта

Здесь — полное описание рецепта. Залогиненные пользователи могут добавить рецепт в избранное и список покупок, а также подписаться на автора рецепта. Для каждого рецепта можно получить прямую короткую ссылку.

### Страница пользователя

На странице отображается имя пользователя, все рецепты, опубликованные пользователем, и кнопка, чтобы подписаться или отписаться от него.

### Страница подписок

Только владелец аккаунта может просмотреть свою страницу подписок. Подписка доступна только залогиненным пользователям.

### Избранное

Добавлять рецепты в избранное могут только залогиненные пользователи. Если незалогиненный пользователь попытается добавить рецепт в избранное, приложение предложит зарегистрироваться или войти в аккаунт.

### Список покупок

Работать со списком покупок могут только залогиненные пользователи. Пользователь может добавлять рецепты в список покупок и скачивать файл с перечнем и количеством необходимых ингредиентов.

### Создание и редактирование рецепта

Страница создания и редактирования рецепта доступна только для залогиненных пользователей. Все поля на ней обязательны для заполнения.

### Страница смены пароля

Доступ к странице смены пароля есть только у залогиненных пользователей через кнопку «Сменить пароль».

### Фильтрация по тегам

При добавлении рецепта указываются теги. Фильтрация рецептов осуществляется по выбранным тегам.

### Смена аватара

После регистрации пользователь получает изображение профиля по умолчанию, которое можно заменить или удалить.

### Разграничение прав

В проекте предусмотрены разные уровни доступа: гость (анонимный пользователь), аутентифицированный (залогиненный) пользователь и администратор.

## API Эндпоинты

## Основные эндпоинты

### Пользователи

- **GET /api/users/**
  - Получить список пользователей с пагинацией.
- **POST /api/users/**
  - Зарегистрировать нового пользователя.

- **GET /api/users/{id}/**
  - Получить профиль пользователя по ID.

- **GET /api/users/me/**
  - Получить текущего авторизованного пользователя.

- **PUT /api/users/me/avatar/**
  - Добавить аватар текущему пользователю.

- **DELETE /api/users/me/avatar/**
  - Удалить аватар текущего пользователя.

- **GET /api/users/subscriptions/**
  - Получить подписки текущего пользователя.

- **POST /api/users/{id}/subscribe/**
  - Подписаться на пользователя по ID.

- **DELETE /api/users/{id}/subscribe/**
  - Отписаться от пользователя по ID.

- **POST /api/users/set_password/**
  - Изменить пароль текущего пользователя.

### Рецепты

- **GET /api/recipes/**
  - Получить список рецептов с фильтрацией и пагинацией.

- **POST /api/recipes/**
  - Создать новый рецепт.

- **GET /api/recipes/{id}/**
  - Получить рецепт по ID.

- **PATCH /api/recipes/{id}/**
  - Обновить рецепт по ID.

- **DELETE /api/recipes/{id}/**
  - Удалить рецепт по ID.

- **GET /api/recipes/download_shopping_cart/**
  - Скачать список покупок в формате TXT/PDF/CSV.

- **POST /api/recipes/{id}/favorite/**
  - Добавить рецепт в избранное.

- **DELETE /api/recipes/{id}/favorite/**
  - Удалить рецепт из избранного.

- **POST /api/recipes/{id}/shopping_cart/**
  - Добавить рецепт в список покупок.

- **DELETE /api/recipes/{id}/shopping_cart/**
  - Удалить рецепт из списка покупок.

- **GET /api/recipes/{id}/get-link/**
  - Получить короткую ссылку на рецепт.

### Теги

- **GET /api/tags/**
  - Получить список тегов.

- **GET /api/tags/{id}/**
  - Получить тег по ID.

### Ингредиенты

- **GET /api/ingredients/**
  - Получить список ингредиентов с поиском.

- **GET /api/ingredients/{id}/**
  - Получить ингредиент по ID.

### Аутентификация

- **POST /api/auth/token/login/**
  - Получить токен авторизации.

- **POST /api/auth/token/logout/**
  - Удалить токен авторизации.

## Документация Redoc

- С документацией можете ознакомится по ссылке:
  - **GET /api/docs/**

## Автор

### NIA River

- **Contact the creator**
  - Email: <nianate@yandex.ru>
  - GitHub: github.com/NiaRiver/
