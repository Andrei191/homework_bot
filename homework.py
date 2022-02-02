import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'сообщение не отправлено. причина: {error}')


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework.status_code != 200:
        raise exceptions.RequestApiError(
            "Сбой в работе программы:"
            "Эндпоинт https://practicum.yandex.ru"
            "/api/user_api/homework_statuses/111"
            " недоступен.")
    return homework.json()


def check_response(response):
    if not isinstance(response, dict) or len(response) == 0:
        raise TypeError("ответ API некорректен,"
                        f"ожидается словарь, получено {type(response)}")
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError("ответ API некорректен,"
                        f"ожидается список, получено {type(homeworks)}")
    return homeworks


def parse_status(homework):
    try:
        homework_name = homework.get('homework_name')
    except Exception:
        raise TypeError("в словаре д/з нет ключа homework_name")
    homework_status = homework.get('status')
    if homework_status is None:
        raise TypeError("в словаре д/з нет ключа status")
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if verdict is None:
        raise KeyError("неверный статус ответа")
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if None in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        return False
    return True


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        logger.critical("одна или несколько из обязательных "
                        "переменных окружения отсутствуют")
        raise exceptions.EnvironmentVariablesError(
            "одна или несколько из обязательных "
            "переменных окружения отсутствуют")

    old_message = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)[0]
            message = parse_status(homeworks)
            if message != old_message:
                send_message(bot, message)
                logger.info('message')
                old_message = message
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != old_message:
                send_message(bot, message)
                old_message = message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
