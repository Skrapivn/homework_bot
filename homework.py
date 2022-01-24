from http import HTTPStatus
import logging
import os
import sys
import time
from logging import Formatter, StreamHandler

import requests
import telegram
from dotenv import load_dotenv

from exceptions import ApiResponseError, ServerApiError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
handler.setFormatter(
    Formatter(fmt='[%(asctime)s: %(levelname)s] %(funcName)s - %(message)s',
              datefmt='%m/%d/%Y %I:%M:%S %p')
)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправка сообщения ботом."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.info('Сообщение успешно отправлено')
    except telegram.error:
        logger.error('Сбой отправки сообщения в телеграмм')


def get_api_answer(current_timestamp):
    """Получение ответа от API."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as err:
        logger.error(f'Ошибка отправки запроса {err}')
        raise err(
            'Ошибка отправки запроса на сервер API: ', err
        )
    if response.status_code != HTTPStatus.OK:
        logger.error(f'ENDPOINT недоступен код: {response.status_code}')
        raise ServerApiError(
            f'Сервер недоступен код: {response.status_code}'
        )
    try:
        return response.json()
    except ValueError as err:
        logger.error(f'Отсутствует ожидаемые ответ ошибка: {err}')
        raise err('Некорректный ответ API')


def check_response(response):
    """Проверяет ответ API."""
    if (isinstance(response, dict)
       and 'homeworks' in response
       and isinstance(response['homeworks'], list)):
        return response['homeworks']
    raise ApiResponseError('Неверный формат ответа API')


def parse_status(homework):
    """Выгрузка статуса из ответа API."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        logger.error('Найден новый статус, отсутствующий в списке!')
        raise Exception('Некорректные данные по статусу ДЗ')
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    logger.info(f'Вердикт проекта {verdict}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    tokens_os = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for token_name, tokens in tokens_os.items():
        if tokens is None:
            logger.critical(f'Необходимо проверить Токены {token_name}')
            return False
    logger.info('Токены прошли проверку')
    return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    error_log = None
    message_log = None

    if check_tokens() is False:
        sys.exit(logger.critical('Отсутствие обязательных переменных. '
                                 'Ошибка в Токенах или файле .env'))
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework != []:
                message = parse_status(homework[0])
                if message_log != message:
                    message_log = message
                    logger.debug('Отправка сообщения')
                    send_message(bot, message)
            else:
                logger.debug('Нет нового статуса ДЗ')

            current_date = response.get('current_date', current_timestamp)
            current_timestamp = current_date
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if error_log != message:
                error_log = message
                send_message(bot, message)
            else:
                logger.debug(f'Ошибка {message} уже существует')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
