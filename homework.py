import os
import time

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuse/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    print("hello")
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework = requests.get(ENDPOINT, headers=HEADERS, params=params)
    print(homework.status_code == 404)
    if homework.status_code == 404:
        print("A")
        raise ValueError()
    return homework.json()


def check_response(response):
    return response.get('homeworks')


def parse_status(homework):
    homework_name = homework[0].get('homework_name')
    homework_status = homework[0].get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise exceptions.HomeworkStatusError
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if None in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        return False
    return True


def main():
    """Основная логика работы бота."""
    if load_dotenv() is False:
        raise exceptions.EnvironmentVariablesExceptionError(
            "одна или несколько из обязательных"
            "переменных окружения отсутствуют")

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 1640995200
    #current_timestamp = int(time.time())

    ...

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) > 0:
                message = parse_status(homeworks)
                print(message)
                send_message(bot, message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
            time.sleep(RETRY_TIME)
        else:
            ...


if __name__ == '__main__':
    main()
