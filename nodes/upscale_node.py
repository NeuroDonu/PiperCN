import time
import traceback # Оставляем для вывода критических ошибок

# Импортируем необходимые функции из utils
from .utils import (
    get_request,
    post_request_json,
    url_to_image_tensor,
    create_empty_image_tensor,
    tensor_to_base64_data_uri
)

class PiperUpscaleImage:
    UPSCALE_FACTORS = [2, 3, 4]
    # Задаем константы для опроса здесь, а не в интерфейсе
    DEFAULT_POLL_INTERVAL = 2  # Секунды
    DEFAULT_MAX_WAIT_TIME = 300 # Секунды

    @classmethod
    def INPUT_TYPES(cls):
        factor_strings = [str(f) for f in cls.UPSCALE_FACTORS]
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "image": ("IMAGE",),
                "upscaling_factor": (factor_strings, {"default": "2"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "image_format": (["PNG", "JPEG"], {"default": "PNG"})
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("status_text", "output_image")
    FUNCTION = "upscale_image"
    CATEGORY = "PiperAPI/Image"

    # Убираем poll_interval и max_wait_time из параметров функции
    def upscale_image(self, api_key, image, upscaling_factor, seed, image_format):
        # Используем константы
        poll_interval = self.DEFAULT_POLL_INTERVAL
        max_wait_time = self.DEFAULT_MAX_WAIT_TIME

        launch_url = "https://app.piper.my/api/upscale-image-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        empty_image = create_empty_image_tensor()
        status_text = "Ошибка: Неизвестный сбой." # Стандартное сообщение об ошибке

        # 1. Проверка входных данных
        try:
            upscale_value = float(upscaling_factor)
        except ValueError:
             err_msg = f"Критическая ошибка: Неверный фактор масштабирования '{upscaling_factor}'."
             print(f"[PiperUpscale] {err_msg}")
             return (err_msg, empty_image)

        # 2. Конвертация в Base64
        try:
            base64_data_uri = tensor_to_base64_data_uri(image, image_format=image_format)
            if not base64_data_uri:
                err_msg = "Критическая ошибка: Не удалось конвертировать изображение в Base64."
                # Предполагаем, что tensor_to_base64_data_uri уже вывел детали ошибки
                print(f"[PiperUpscale] {err_msg}")
                return (err_msg, empty_image)
        except Exception as e:
            print(f"[PiperUpscale] Критическая ошибка при конвертации в Base64:")
            traceback.print_exc()
            err_msg = f"Критическая ошибка подготовки Base64: {e}"
            return (err_msg, empty_image)

        # 3. Запуск задачи
        json_input_data = {
            "inputs": {
                "image": base64_data_uri,
                "upscalingResize": upscale_value
            }
        }

        try:
            # print("[PiperUpscale] Отправка запроса на запуск...") # Убрано
            launch_response = post_request_json(launch_url, api_key, json_input_data)
        except Exception as e:
             print(f"[PiperUpscale] Критическая ошибка сети при запуске задачи:")
             traceback.print_exc()
             err_msg = f"Критическая ошибка сети (запуск): {e}"
             return (err_msg, empty_image)

        # 4. Проверка ответа на запуск
        if not launch_response or not isinstance(launch_response, dict) or "_id" not in launch_response:
            api_error_details = "Неизвестно"
            if launch_response and isinstance(launch_response, dict):
                 api_error_details = launch_response.get('error', launch_response) # Пытаемся получить детали
            elif launch_response:
                 api_error_details = str(launch_response) # Если ответ не словарь

            err_msg = f"Критическая ошибка: Не удалось запустить задачу или получить ID. Ответ API: {api_error_details}"
            print(f"[PiperUpscale] {err_msg}")
            return (err_msg, empty_image)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)
        # print(f"[PiperUpscale] Задача запущена. ID: {launch_id}. Опрос...") # Убрано

        # 5. Опрос состояния
        start_time = time.time()
        while True:
            current_time = time.time()
            # Проверка таймаута
            if current_time - start_time > max_wait_time:
                err_msg = f"Критическая ошибка: Таймаут ({max_wait_time} сек) ожидания задачи {launch_id}"
                print(f"[PiperUpscale] {err_msg}")
                return (err_msg, empty_image)

            # Запрос состояния
            try:
                state_response = get_request(state_url, api_key)
            except Exception as e:
                 # Ошибка сети при опросе - не обязательно критическая, можем повторить
                 print(f"[PiperUpscale] Ошибка сети при опросе {launch_id} (повтор через {poll_interval} сек): {e}")
                 # traceback.print_exc() # Можно раскомментировать для детальной отладки сети
                 time.sleep(poll_interval)
                 continue # Повторяем попытку

            # Анализ ответа
            if not state_response or not isinstance(state_response, dict):
                # Некорректный ответ - повторяем
                print(f"[PiperUpscale] Предупреждение: Некорректный ответ о состоянии {launch_id} (повтор через {poll_interval} сек).")
                time.sleep(poll_interval)
                continue

            # Проверка на ошибки API
            errors = state_response.get("errors")
            if errors:
                if isinstance(errors, list) and len(errors) > 0: error_details = ', '.join(map(str, errors))
                elif isinstance(errors, str): error_details = errors
                else: error_details = str(errors)
                err_msg = f"Критическая ошибка API: Задача {launch_id} не удалась. Детали: {error_details}"
                print(f"[PiperUpscale] {err_msg}")
                return (err_msg, empty_image)

            # Проверка на успешный результат
            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict):
                 output_image_url = outputs.get("image")
                 if output_image_url and isinstance(output_image_url, str):
                     # print(f"[PiperUpscale] Результат найден для {launch_id}. Загрузка...") # Убрано
                     try:
                         output_image_tensor = url_to_image_tensor(output_image_url)
                         status_text = f"Успех: Изображение обработано задачей {launch_id}."
                         #print(f"[PiperUpscale] {status_text}") # Выводим сообщение об успехе
                         return (status_text, output_image_tensor)
                     except Exception as e:
                         print(f"[PiperUpscale] Критическая ошибка обработки результирующего изображения ({launch_id}):")
                         traceback.print_exc()
                         err_msg = f"Критическая ошибка обработки результата: {e}"
                         return (err_msg, empty_image)
                 # else: # Если outputs есть, но URL еще нет - просто продолжаем опрос
                     # print(f"[PiperUpscale] Задача {launch_id} в процессе...") # Убрано

            # Если нет ни ошибки, ни результата - пауза перед следующим опросом
            # else:
                 # print(f"[PiperUpscale] Задача {launch_id} в процессе...") # Убрано

            time.sleep(poll_interval)

        # Сюда код не должен дойти при нормальной работе
        # err_msg = f"Критическая ошибка: Цикл опроса неожиданно завершился для {launch_id}."
        # print(f"[PiperUpscale] {err_msg}")
        # return (err_msg, empty_image)