import logging
import os
import sys
import time
from http import HTTPStatus

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


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """функция отправки сообщений в телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'сообщение не отправлено. причина: {error}')


def get_api_answer(current_timestamp):
    """теперь ответ от API в формате list, а не json."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logger.error('Сбой в работе программы:'
                     f'Эндпоинт {ENDPOINT}'
                     f' недоступен." причина: {error}')
    if homework.status_code != HTTPStatus.OK:
        raise exceptions.RequestApiError(
            'Сбой в работе программы:'
            f'Эндпоинт {ENDPOINT}'
            ' недоступен.')
    try:
        return homework.json()
    except Exception:
        logger.error('ошибка функции get_api_answer, ответ API пуст')


def check_response(response):
    """функция возвращает список домашних заданий."""
    if not isinstance(response, dict) or len(response) == 0:
        raise TypeError("ответ API некорректен,"
                        f"ожидается словарь, получено {type(response)}")
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError("ответ API не соответствует ожидаемому")
    return homeworks


def parse_status(homework):
    """возвращает строку для отправки сообщения с нужным комментарием."""
    if isinstance(homework, list):
        homework = homework[0]
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        logger.error("в словаре д/з нет ключа homework_name")
        raise KeyError("в словаре д/з нет ключа homework_name")
    if homework_status is None:
        raise TypeError("в словаре д/з нет ключа status")
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError("неверный статус ответа")
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if verdict is None:
        raise KeyError("неверный статус ответа")
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """проверка доступности необходимых переменных окружения."""
    env_variables = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(env_variables)


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        logger.critical("одна или несколько из обязательных "
                        "переменных окружения отсутствуют")
        raise exceptions.EnvironmentVariablesError(
            "одна или несколько из обязательных "
            "переменных окружения отсутствуют")

    old_message = ''
    old_error = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 1638316800

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)[0]
            print(homeworks)
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
            if error != old_error:
                send_message(bot, message)
                old_error = error
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
