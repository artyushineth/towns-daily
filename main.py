from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from datetime import datetime
import requests
import random
import time
import pyautogui

# Чтение списка user_id из файла 'id.txt'
with open('id.txt', 'r', encoding='utf-8') as file:
    user_ids = [line.strip() for line in file if line.strip()]

# Перемешиваем user_ids для случайного порядка
random.shuffle(user_ids)  # Изменение 1: Рандомизация порядка user_id

# Чтение списка сообщений из файла '1.txt'
with open('1.txt', 'r', encoding='utf-8') as file:
    messages = [line.strip() for line in file if line.strip()]

# Проверка, что количество сообщений соответствует 5 на каждый user_id
required_messages = len(user_ids) * 5
if len(messages) < required_messages:
    raise ValueError(
        f"Недостаточно сообщений в '1.txt'. Требуется как минимум {required_messages}, "
        f"а найдено {len(messages)}."
    )


def close_browser(user_id):
    """
    Функция для закрытия браузера по user_id.
    """
    try:
        close_url = f"http://local.adspower.net:50325/api/v1/browser/stop?user_id={user_id}"
        response = requests.get(close_url)
        response.raise_for_status()
        print(f"[{user_id}] Браузер успешно закрыт.")
    except Exception as e:
        print(f"[{user_id}] Ошибка при закрытии браузера: {str(e)}")


def chunked(lst, n):
    """
    Функция для разделения списка на части по n элементов.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_random_delay(options):
    """
    Функция для получения случайной задержки из списка опций.
    """
    return random.choice(options)


def main():
    # Разделяем все сообщения на блоки по 5 для каждого user_id
    message_chunks = list(chunked(messages, 5))

    # Проверка, что у нас есть достаточно блоков сообщений
    if len(message_chunks) < len(user_ids):
        raise ValueError("Недостаточно блоков сообщений для всех user_id.")

    # Определяем варианты задержек для различных этапов
    site_load_delays = [12 + 0.5 * i for i in range(11)]  # 12.0, 12.5, ..., 17.0 секунд (Изменение 2)

    typing_intervals = [0.05, 0.1, 0.15, 0.2, 0.07, 0.12, 0.18, 0.22, 0.09, 0.14]  # 10 разных скоростей (Изменение 3)

    message_delays = [1 + 0.133 * i for i in range(15)]  # 1.0, 1.133, ..., 3.933 секунд (Изменение 4)

    post_send_delays = [1 + 0.133 * i for i in range(15)]  # 1.0, 1.133, ..., 3.933 секунд (Изменение 5)

    new_window_delays = [3 + 0.2 * i for i in range(16)]  # 3.0, 3.2, ..., 6.0 секунд (Изменение 6)

    # Новая задержка перед отправкой сообщения (1-2 секунды, 8 вариантов)
    send_message_delays = [1 + 0.125 * i for i in range(8)]  # 1.0, 1.125, ..., 1.875 секунд (Новое изменение)

    # Основной цикл по каждому user_id и соответствующему блоку сообщений
    for idx, user_id in enumerate(user_ids):
        # Если встретили строку "stop" в списке - выходим
        if user_id.lower() == 'stop':
            print("Получена команда остановки. Завершение работы.")
            break

        driver = None
        start_time = datetime.now()
        print(f"[{user_id}] Начало работы в {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Открываем браузер для текущего user_id через AdsPower
            open_url = f"http://local.adspower.net:50325/api/v1/browser/start?user_id={user_id}"
            response = requests.get(open_url)
            response.raise_for_status()
            response_data = response.json()

            # Настройка ChromeDriver для удалённого подключения
            chrome_driver = response_data["data"]["webdriver"]
            selenium_address = response_data["data"]["ws"]["selenium"]

            chrome_options = Options()
            # Подключаемся к удалённой сессии (AdsPower)
            chrome_options.add_experimental_option("debuggerAddress", selenium_address)
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            service = Service(executable_path=chrome_driver)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_window_size(1200, 720)

            # Открываем сайт Towns
            target_url = (
                'https://app.towns.com/t/0x0d02c74b5658f5c6956a6f9c1a2244ae524dc988/'
                'channels/200d02c74b5658f5c6956a6f9c1a2244ae524dc9880000000000000000000000'
            )
            driver.get(target_url)
            print(f"[{user_id}] Открыт сайт Towns.")

            # Рандомная задержка между 12-17 секунд
            site_load_delay = get_random_delay(site_load_delays)
            print(f"[{user_id}] Ожидание загрузки сайта: {site_load_delay} секунд.")
            time.sleep(site_load_delay)  # Изменение 2

            # Находим поле для ввода текста
            try:
                message_field = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
                )
                print(f"[{user_id}] Найдено поле для ввода сообщений.")
            except Exception as e:
                raise Exception(f"Не удалось найти поле для ввода сообщений: {str(e)}")

            # Получаем блок сообщений (5 сообщений) для текущего user_id
            user_messages = message_chunks[idx]
            if len(user_messages) < 5:
                raise Exception(
                    f"Недостаточно сообщений для {user_id}. Требуется 5, а найдено {len(user_messages)}."
                )

            # Отправляем 5 сообщений
            for i, msg in enumerate(user_messages, start=1):
                try:
                    # Кликаем в поле ввода, чтобы туда встал курсор (важно для pyautogui)
                    message_field.click()
                    time.sleep(0.5)  # Краткая задержка после клика

                    # Выбираем случайный интервал для печати
                    typing_interval = get_random_delay(typing_intervals)
                    # Посимвольный ввод сообщения через PyAutoGUI с рандомной скоростью
                    pyautogui.write(msg, interval=typing_interval)
                    print(f"[{user_id}] Введено сообщение {i}/5: {msg} с интервалом {typing_interval} секунд.")

                    # Задержка перед отправкой сообщения
                    send_delay = get_random_delay(send_message_delays)
                    print(f"[{user_id}] Ожидание перед отправкой сообщения: {send_delay} секунд.")
                    time.sleep(send_delay)  # Новое изменение

                    # Отправляем сообщение нажатием на Enter
                    pyautogui.press('enter')
                    print(f"[{user_id}] Нажата клавиша Enter для отправки сообщения {i}/5.")

                    # Между отправками сообщений — рандомная задержка 1-3 секунды
                    message_delay = get_random_delay(message_delays)
                    print(f"[{user_id}] Ожидание перед следующим сообщением: {message_delay} секунд.")
                    time.sleep(message_delay)  # Изменение 4

                except Exception as e:
                    print(f"[{user_id}] Ошибка при отправке сообщения {i}/5: {str(e)}")
                    with open('error.txt', 'a', encoding='utf-8') as error_file:
                        error_file.write(f"{user_id}: Ошибка при отправке сообщения {i}/5: {str(e)}\n")
                    continue  # Переходим к следующему сообщению

            # После отправки последнего сообщения — задержка 1-3 секунды
            post_send_delay = get_random_delay(post_send_delays)
            print(f"[{user_id}] Ожидание перед закрытием браузера: {post_send_delay} секунд.")
            time.sleep(post_send_delay)  # Изменение 5

            end_time = datetime.now()
            print(f"[{user_id}] Завершена работа в {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            # Ловим любые общие ошибки, связанные с открытием браузера и т.д.
            print(f"[{user_id}] Общая ошибка: {str(e)}")
            with open('error.txt', 'a', encoding='utf-8') as error_file:
                error_file.write(f"{user_id}: Общая ошибка: {str(e)}\n")

        finally:
            # Закрытие браузера в любом случае
            close_browser(user_id)
            if driver:
                driver.quit()
                print(f"[{user_id}] Браузер закрыт.")
            # Задержка перед открытием нового окна: 3-6 секунд
            new_window_delay = get_random_delay(new_window_delays)
            print(f"[{user_id}] Ожидание перед открытием нового окна: {new_window_delay} секунд.")
            time.sleep(new_window_delay)  # Изменение 6


if __name__ == "__main__":
    main()
