# Telegram Bot
Телеграм бот-помошник, отправляющий статус проверки ДЗ после ревью. С помощью бота больше нет нужды заходить и каждый раз проверять почту. 

## Как запустить проект:
1. Клонировать репозиторий:
```
git clone https://github.com/Skrapivn/homework_bot.git
```

2. Создать виртуальное окружение:
```
python -m venv venv
```

3. Активировать виртуальное окружение, обновить версию ```pip``` и установить зависимости из ```requirements.txt```:
```
source venv/bin/activate
```
```
python -m pip install -–upgrade pip.
```
```
pip install -r requirements.txt
```
4. Необходимо изменить ключи в файле .evn.example и переименовать файл в .evn:
```
PRACTICUM_TOKEN = <Ваш персональный токен Yandex.Practicum>
TELEGRAM_TOKEN = <токен Вашего телеграмм-бота>
TELEGRAM_CHAT_ID = <токен Вашего личного телеграмм-чата>
```
Теперь можно запустить программу из среды разработки или зарегестрировать бота, к примеру на сервисе **Heroku**

Автор: [Sergey K.](https://github.com/Skrapivn "Sergey K.")
