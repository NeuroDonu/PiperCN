# nodes/dress_node.py
import time
import torch
import traceback # Для вывода критических ошибок

# Импортируем нужные хелперы
from .utils import (
    # post_request, # Заменяем на post_request_json
    post_request_json,
    get_request,
    url_to_image_tensor,
    create_empty_image_tensor,
    tensor_to_base64_data_uri # Наш конвертер
    # upload_image_and_get_url # Больше не нужен
)

class PiperDressFactory:
    # Списки опций оставляем
    GENDER_LIST = ["auto", "male", "female"]
    STYLE_LIST = [
        "red_swimsuit", "dress_cyber_bloom", "dress_vintage_muse", "dress_celestial_queen",
        "dress_streetwave_rebel", "dress_sakura_spirit", "dress_desert_mirage", "dress_arctic_elegance",
        "dress_pixel_pop", "dress_royal_bloom", "dress_rainy_day_chic", "dress_velvet_desire",
        "dress_neon_temptation", "dress_scarlet_heat", "dress_shadow_lace", "dress_tropical_tease",
        "dress_golden_mirage", "dress_leather_nights", "dress_crystal_kiss", "dress_midnight_flame",
        "dress_pearl_fantasy", "lingerie_silken_whisper", "lingerie_crimson_lace", "lingerie_noir_allure",
        "lingerie_golden_hour", "lingerie_moonlight_veil", "lingerie_velvet_sin", "lingerie_cherry_bloom",
        "lingerie_shadow_net", "lingerie_pearl_touch", "lingerie_electric_kiss"
    ]

    # Задаем константы для опроса
    DEFAULT_POLL_INTERVAL = 3  # Секунды
    DEFAULT_MAX_WAIT_TIME = 300 # Секунды

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "image": ("IMAGE",), # Входное изображение
                "gender": (s.GENDER_LIST, {"default": "auto"}),
                "style": (s.STYLE_LIST, {"default": "red_swimsuit"}),
                # Убрали poll_interval и max_wait_time
                "image_format": (["PNG", "JPEG"], {"default": "PNG"}) # Формат для Base64
            },
            "optional": {
                 "prompt": ("STRING", {"multiline": True, "default": ""}),
                 # Seed здесь не нужен, как и в ViolationsDetector
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("status_text", "output_image")
    FUNCTION = "dress_image"
    CATEGORY = "PiperAPI/Image"

    # Убираем poll_interval, max_wait_time из аргументов, добавляем image_format
    def dress_image(self, api_key, image, gender, style, image_format, prompt=None):
        # Используем константы
        poll_interval = self.DEFAULT_POLL_INTERVAL
        max_wait_time = self.DEFAULT_MAX_WAIT_TIME

        launch_url = "https://app.piper.my/api/dress-factory-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        empty_image = create_empty_image_tensor()
        status_text = "Ошибка: Неизвестный сбой."

        # 1. Конвертация изображения в Base64
        try:
            base64_image_uri = tensor_to_base64_data_uri(image, image_format=image_format)
            if not base64_image_uri:
                err_msg = "Критическая ошибка: Не удалось конвертировать изображение в Base64."
                print(f"[PiperDress] {err_msg}")
                return (err_msg, empty_image)
        except Exception as e:
            print(f"[PiperDress] Критическая ошибка при конвертации в Base64:")
            traceback.print_exc()
            err_msg = f"Критическая ошибка подготовки Base64: {e}"
            return (err_msg, empty_image)

        # 2. Подготовка и запуск задачи
        launch_data = {
            "inputs": {
                "image": base64_image_uri, # Используем Base64
                "gender": gender,
                "style": style,
                # Добавляем prompt только если он не пустой
                **({"prompt": prompt.strip()} if prompt and prompt.strip() else {})
            }
        }

        try:
            # print("[PiperDress] Отправка запроса на запуск...") # Убрано
            # Используем post_request_json
            launch_response = post_request_json(launch_url, api_key, launch_data)
        except Exception as e:
             print(f"[PiperDress] Критическая ошибка сети при запуске задачи:")
             traceback.print_exc()
             err_msg = f"Критическая ошибка сети (запуск): {e}"
             return (err_msg, empty_image)

        # 3. Проверка ответа на запуск
        if not launch_response or not isinstance(launch_response, dict) or "_id" not in launch_response:
            api_error_details = "Неизвестно"
            if launch_response and isinstance(launch_response, dict): api_error_details = launch_response.get('error', launch_response)
            elif launch_response: api_error_details = str(launch_response)

            err_msg = f"Критическая ошибка: Не удалось запустить задачу или получить ID. Ответ API: {api_error_details}"
            print(f"[PiperDress] {err_msg}")
            return (err_msg, empty_image)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)
        # print(f"[PiperDress] Задача запущена. ID: {launch_id}. Опрос...") # Убрано

        # 4. Опрос состояния
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Критическая ошибка: Таймаут ({max_wait_time} сек) ожидания задачи {launch_id}"
                print(f"[PiperDress] {err_msg}")
                return (err_msg, empty_image)

            try:
                state_response = get_request(state_url, api_key)
            except Exception as e:
                 print(f"[PiperDress] Ошибка сети при опросе {launch_id} (повтор через {poll_interval} сек): {e}")
                 time.sleep(poll_interval)
                 continue

            if not state_response or not isinstance(state_response, dict):
                print(f"[PiperDress] Предупреждение: Некорректный ответ о состоянии {launch_id} (повтор через {poll_interval} сек).")
                time.sleep(poll_interval)
                continue

            errors = state_response.get("errors")
            if errors:
                if isinstance(errors, list) and len(errors) > 0: error_details = ', '.join(map(str, errors))
                elif isinstance(errors, str): error_details = errors
                else: error_details = str(errors)
                err_msg = f"Критическая ошибка API: Задача {launch_id} не удалась. Детали: {error_details}"
                print(f"[PiperDress] {err_msg}")
                # print(f"Full state response on error: {state_response}") # Можно раскомментировать для отладки
                return (err_msg, empty_image)

            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict):
                 output_image_url = outputs.get("image")
                 if output_image_url and isinstance(output_image_url, str):
                     try:
                         output_image_tensor = url_to_image_tensor(output_image_url)
                         if output_image_tensor is None:
                             raise ValueError("Не удалось загрузить/обработать изображение по URL")
                         status_text = f"Успех: Изображение обработано задачей {launch_id}."
                         print(f"[PiperDress] {status_text}") # Сообщение об успехе
                         return (status_text, output_image_tensor)
                     except Exception as e:
                         print(f"[PiperDress] Критическая ошибка обработки результирующего изображения ({launch_id}, URL: {output_image_url}):")
                         traceback.print_exc()
                         err_msg = f"Критическая ошибка обработки результата: {e}"
                         return (err_msg, empty_image)
                 else:
                     err_msg = f"Критическая ошибка: В результатах задачи {launch_id} отсутствует или некорректен URL изображения. Ответ: {outputs}"
                     print(f"[PiperDress] {err_msg}")
                     return (err_msg, empty_image)

            # Если нет ни ошибок, ни outputs - ждем дальше
            time.sleep(poll_interval)

        # Сюда код не должен дойти
        # err_msg = f"Критическая ошибка: Цикл опроса неожиданно завершился для {launch_id}."
        # print(f"[PiperDress] {err_msg}")
        # return (err_msg, empty_image)