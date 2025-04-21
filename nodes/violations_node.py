# nodes/violations_node.py
import time
import json # Для форматирования выходной строки
import torch
import traceback # Для вывода критических ошибок

# Импортируем нужные хелперы из utils.py
from .utils import (
    # post_request, # Используем post_request_json для ясности
    post_request_json,
    get_request,
    tensor_to_base64_data_uri, # Наш конвертер
    create_empty_image_tensor # Хотя не используется для вывода, может понадобиться для utils
    # upload_image_and_get_url # Больше не нужен
)

class PiperViolationsDetector:
    # Определяем проверки по умолчанию
    DEFAULT_CHECKS = "underage,nsfw"
    # Задаем константы для опроса
    DEFAULT_POLL_INTERVAL = 2  # Секунды
    DEFAULT_MAX_WAIT_TIME = 120 # Секунды

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "image": ("IMAGE",),
                "checks": ("STRING", {"multiline": False, "default": s.DEFAULT_CHECKS}),
                # Убрали poll_interval и max_wait_time
                "image_format": (["PNG", "JPEG"], {"default": "PNG"}) # Формат для Base64
            }
            # seed здесь не нужен, т.к. детектор не генеративный
        }

    RETURN_TYPES = ("STRING",) # Возвращаем JSON строку с результатами
    RETURN_NAMES = ("results_text",)
    FUNCTION = "detect_violations"
    CATEGORY = "PiperAPI/Analysis" # Можно сменить категорию на Analysis

    def parse_checks(self, checks_string):
        """Парсит строку проверок, разделенных запятыми, в список."""
        if not checks_string:
            return []
        # Убираем пустые строки после разделения
        return [check.strip() for check in checks_string.split(',') if check.strip()]

    # Убираем poll_interval, max_wait_time из аргументов, добавляем image_format
    def detect_violations(self, api_key, image, checks, image_format):
        # Используем константы
        poll_interval = self.DEFAULT_POLL_INTERVAL
        max_wait_time = self.DEFAULT_MAX_WAIT_TIME

        launch_url = "https://app.piper.my/api/violations-detector-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        # Стандартный результат ошибки в формате JSON
        default_error_result_json = json.dumps({"error": "Обработка прервана до завершения"})

        # 1. Конвертация изображения в Base64
        try:
            base64_image_uri = tensor_to_base64_data_uri(image, image_format=image_format)
            if not base64_image_uri:
                err_msg = "Критическая ошибка: Не удалось конвертировать изображение в Base64."
                print(f"[PiperViolations] {err_msg}")
                return (json.dumps({"error": err_msg}),) # Возвращаем ошибку в JSON
        except Exception as e:
            print(f"[PiperViolations] Критическая ошибка при конвертации в Base64:")
            traceback.print_exc()
            err_msg = f"Критическая ошибка подготовки Base64: {e}"
            return (json.dumps({"error": err_msg}),)

        # 2. Парсинг проверок
        checks_list = self.parse_checks(checks)
        if not checks_list:
             # Если пользователь ничего не ввел или ввел некорректно, используем дефолтные
             print(f"[PiperViolations] Предупреждение: Не указаны валидные проверки, используются стандартные: {self.DEFAULT_CHECKS}")
             checks_list = self.parse_checks(self.DEFAULT_CHECKS)

        # 3. Запуск задачи
        launch_data = {
            "inputs": {
                "image": base64_image_uri, # Используем Base64
                "checks": checks_list
            }
        }

        try:
            # print("[PiperViolations] Отправка запроса на запуск...") # Убрано
            # Используем post_request_json
            launch_response = post_request_json(launch_url, api_key, launch_data)
        except Exception as e:
             print(f"[PiperViolations] Критическая ошибка сети при запуске задачи:")
             traceback.print_exc()
             err_msg = f"Критическая ошибка сети (запуск): {e}"
             return (json.dumps({"error": err_msg}),)

        # 4. Проверка ответа на запуск
        if not launch_response or not isinstance(launch_response, dict) or "_id" not in launch_response:
            api_error_details = "Неизвестно"
            if launch_response and isinstance(launch_response, dict): api_error_details = launch_response.get('error', launch_response)
            elif launch_response: api_error_details = str(launch_response)

            err_msg = f"Критическая ошибка: Не удалось запустить задачу или получить ID. Ответ API: {api_error_details}"
            print(f"[PiperViolations] {err_msg}")
            return (json.dumps({"error": err_msg, "details": api_error_details}),)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)
        # print(f"[PiperViolations] Задача запущена. ID: {launch_id}. Опрос...") # Убрано

        # 5. Опрос состояния
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Критическая ошибка: Таймаут ({max_wait_time} сек) ожидания задачи {launch_id}"
                print(f"[PiperViolations] {err_msg}")
                return (json.dumps({"error": err_msg}),)

            try:
                state_response = get_request(state_url, api_key)
            except Exception as e:
                 print(f"[PiperViolations] Ошибка сети при опросе {launch_id} (повтор через {poll_interval} сек): {e}")
                 time.sleep(poll_interval)
                 continue

            if not state_response or not isinstance(state_response, dict):
                print(f"[PiperViolations] Предупреждение: Некорректный ответ о состоянии {launch_id} (повтор через {poll_interval} сек).")
                time.sleep(poll_interval)
                continue

            errors = state_response.get("errors")
            if errors:
                if isinstance(errors, list) and len(errors) > 0: error_details = errors # Возвращаем весь список ошибок
                elif isinstance(errors, str): error_details = [errors] # Оборачиваем строку в список
                else: error_details = [str(errors)] # На всякий случай
                err_msg = f"Критическая ошибка API: Задача {launch_id} не удалась."
                print(f"[PiperViolations] {err_msg} Детали: {error_details}")
                return (json.dumps({"error": "API processing failed", "details": error_details}),)

            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict) and len(outputs) > 0:
                 # Форматируем успешный результат в JSON
                 try:
                    result_json = json.dumps(outputs, indent=2)
                    print(f"[PiperViolations] Успех: Детекция завершена для задачи {launch_id}.") # Выводим сообщение об успехе
                    return (result_json,)
                 except Exception as e:
                    print(f"[PiperViolations] Критическая ошибка форматирования результата {launch_id}:")
                    traceback.print_exc()
                    err_msg = f"Критическая ошибка форматирования результата: {e}"
                    # Возвращаем исходный словарь outputs, если не удалось сериализовать
                    return (json.dumps({"warning": err_msg, "raw_outputs": outputs}),)

            # Если нет ни ошибок, ни outputs - ждем дальше
            time.sleep(poll_interval)

        # Сюда код не должен дойти
        # err_msg = f"Критическая ошибка: Цикл опроса неожиданно завершился для {launch_id}."
        # print(f"[PiperViolations] {err_msg}")
        # return (default_error_result_json,)