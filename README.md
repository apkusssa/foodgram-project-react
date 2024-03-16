<h1 style="text-align:center;">Foodgram</h1> 

Foodgram - это онлайн-платформа для всех, кто увлечен готовкой и кулинарией. Здесь вы можете легко искать, сохранять и делиться рецептами, а также находить новые и интересные идеи для блюд.

На Foodgram вы создаете свой собственный профиль, где храните свои любимые рецепты и следите за активностью других пользователей. Можно добавлять фотографии приготовленных блюд, описания и список ингредиентов, а также отмечать любимые рецепты.

Это отличное место для тех, кто ищет вдохновение в кулинарии и готов к делению своими кулинарными экспериментами. Присоединяйтесь к Foodgram и откройте для себя бесконечный мир вкусов и вдохновения!

Проект доступен по ссылке: [Foodgram](https://apkfoodgram.zapto.org)

<h2 style="text-align:center;">Инструкция по запуску:</h2>

- Клонировать репозиторий с github на сервер `git clone git@github.com:apkusssa/foodgram-project-react.git`
- Установить Curl `sudo apt update && sudo apt install curl`
- Скачать установщик Docker'а `curl -fSL https://get.docker.com -o get-docker.sh`
- Установить Docker `sudo sh ./get-docker.sh`
- Установить Docker compose `sudo apt install docker-compose-plugin`
- Создать файл .env с переменными
- Запустить сценарий установки проекта `sudo docker compose -f docker-compose.production.yml up -d`
- Выполнить миграции `sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate`
- Собрать статику контейнера backend `sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic`
- Скопировать статику из контейнера в вольюм `sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/`


<h2 style="text-align:center;">Используемые технологии:</h2>
<ul>
    <li> Ubuntu 22.04 <a href="https://help.ubuntu.com/"> Documentation</a> </li>
    <li>Python 3.10.12 <a href="https://docs.python.org/3/index.html"> Documentation</a> </li>
    <li>Django 3.2.3 <a href="https://docs.djangoproject.com/en/4.2/"> Documentation</a></li>
    <li>Django Rest Framework 3.12.4 <a href="https://www.django-rest-framework.org/topics/documenting-your-api/"> Documentation</a></li>
    <li>Gunicorn 20.1.0 <a href="https://docs.gunicorn.org/en/stable/"> Documentation</a></li>
    <li>React JS 18.2.0 <a href="https://legacy.reactjs.org/docs/getting-started.html?url=https%3A%2F%2Freactjs.org%2Fdocs%2Fgetting-started.html"> Documentation</a></li>
    <li>Nginx 1.18.0 (Ubuntu) <a href="https://nginx.org/ru/docs/"> Documentation</a></li>
    <li>Docker 24.0.7 <a href="https://docs.docker.com/"> Documentation</a></li>
    <li>Docker compose 2.21.0 <a href="https://docs.docker.com/compose/"> Documentation</a></li>
    
</ul>

<h2 style="text-align:center;">Пример запроса:</h2>

### Request
``` bash
$ curl http://158.160.26.0/api/recipes/
```
### Response
``` json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results":  [
        {
            "id": 1,
            "tags": [
                {
                    "id": 2,
                    "name": "Обед",
                    "color": "#49B64E",
                    "slug": "lunch"
                }
            ],
            "author": {
                "email": "vpupkin@yandex.ru",
                "id": 1,
                "username": "vasya.pupkin",
                "first_name": "Вася",
                "last_name": "Пупкин",
                "is_subscribed": false
            },
            "ingredients": [
                {
                    "id": 1916,
                    "name": "фарш (свинина и курица)",
                    "measurement_unit": "г",
                    "amount": 500
                },
                {
                    "id": 886,
                    "name": "лук репчатый",
                    "measurement_unit": "г",
                    "amount": 100
                }
            ],
            "is_favorited": false,
            "is_in_shopping_cart": false,
            "name": "Котлета по киевски",
            "image": "http://localhost:8000/media/recipes/images/temp.png",
            "text": "Рецепт приготовления котлеты по киевски.",
            "cooking_time": 40
        }
    ]
}
```

<h2 style="text-align:center;">Данные для входа в админ панель:</h2>
логин админа: admin
почта админа: admin@mail.ru
пароль админа: admin

<h2 style="text-align:center;">Данные для входа гостя: </h2>
почта: qwe@mail.ru
пароль: qweqweqweqwe

<h3>Автор: Афанасий Павлов</h3>