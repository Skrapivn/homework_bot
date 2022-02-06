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
    Formatter(fmt='[%(asctime)s: %(levelname)s] %(funcName)s(%(lineno)d) - '
              '%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',)
)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправка сообщения ботом."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.info(f'Сообщение {message} успешно отправлено')
    except Exception as error:
        logger.error(f'Сбой отправки сообщения {message} в телеграмм: {error}')


def get_api_answer(current_timestamp):
    """Получение ответа от API."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as err:
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
        logger.error(f'Отсутствует ожидаемый ответ ошибка: {err}')
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
    if homework_name and homework_status is None:
        raise KeyError('Ошибка в получении статуса ответа API')
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
    error_log = ''

    if check_tokens() is False:
        sys.exit(logger.critical('Отсутствие обязательных переменных. '
                                 'Ошибка в Токенах или файле .env'))
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            current_timestamp = response.get('current_date', current_timestamp)
            
            if homework != []:
                if send_message(bot, parse_status(homework[0])):
                    logger.debug('Отправка сообщения')
                    error_log = ''
            else:
                logger.debug('Нет нового статуса ДЗ')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if message != error_log and send_message(bot, message):
                error_log = message

            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
