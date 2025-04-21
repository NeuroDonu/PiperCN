# nodes/face_to_image_node.py
import time
import torch
import traceback # Оставляем для вывода критических ошибок

# Импортируем нужные хелперы, включая Base64 конвертер
from .utils import (
    # post_request, # Заменяем на post_request_json если они делают одно и то же
    post_request_json,
    get_request,
    url_to_image_tensor,
    create_empty_image_tensor,
    tensor_to_base64_data_uri # Наш конвертер
    # upload_image_and_get_url # Больше не нужен
)

class PiperFaceToImage:
    # Списки моделей и размеров оставляем как есть
    CHECKPOINT_LIST = [
        "raemuXL_v40.safetensors", "aamXLAnimeMix_v10.safetensors", "dreamweaverPony25D.1erv.safetensors",
        "mixGEMAdam8witQegoow.NeWz.safetensors", "mfcgPDXL_v10.safetensors", "aniku_0.2.fp16.safetensors",
        "flux1DevHyperNF4Flux1DevBNB_flux1DevHyperNF4.safetensors", "STOIQONewrealityFLUXSD_F1DPreAlpha.safetensors",
        "juggernautXL_v9Rundiffusionphoto2.safetensors", "animaPencilXL_v260.safetensors", "bluePencilXL_v401.safetensors",
        "pixelArtDiffusionXL_spriteShaper.safetensors", "albedobaseXL_v20.safetensors", "leosamsHelloworldXL_helloworldXL50GPT4V.safetensors",
        "dynavisionXLAllInOneStylized_releaseV0610Bakedvae.safetensors", "photon_v1.safetensors", "afroditexlNudePeople_20Bkdvae.safetensors",
        "nosft-float8-e4m3fn.safetensors", "asdf_0.4a_lorapov_0.2_lust_0.4.fp16.safetensors", "PonyASDF_0.4_f6cosineb.fp16.safetensors",
        "Sexy_Aesthetic_SDXL_0.4x0.2.fp16.safetensors", "anikurender_0.4b.fp16.safetensors",
    ]
    IMAGE_SIZE_LIST = [
        "512x512", "512x768", "512x912", "576x768", "704x1344", "704x1408", "768x512", "768x576", "768x768",
        "768x1280", "768x1344", "832x1152", "832x1216", "896x1088", "896x1152", "912x512", "960x1024", "960x1088",
        "1024x1024", "1024x960", "1088x896", "1088x960", "1152x832", "1152x896", "1216x832", "1280x768", "1344x704",
        "1344x768", "1408x704", "1472x704", "1536x640", "1600x640", "1664x576", "1728x576"
    ]
    PERFORMANCE_LIST = ["speed", "quality", "express"]
    DEFAULT_PROMPT = "A man sits at a table, looking directly at the front camera. He has a neutral expression, soft lighting, and a sharp focus on his face. The background is minimal and slightly blurred. Cinematic composition, high detail, realistic skin texture, 4K resolution." # Оставляем, может быть полезно

    # Информация о совместимости (оставляем для предупреждений)
    CHECKPOINT_TYPES = {
        "raemuXL_v40.safetensors": ["SDXL"],"aamXLAnimeMix_v10.safetensors": ["SDXL"],"dreamweaverPony25D.1erv.safetensors": ["SDXL"],
        "mixGEMAdam8witQegoow.NeWz.safetensors": ["SDXL"],"mfcgPDXL_v10.safetensors": ["SDXL"],"aniku_0.2.fp16.safetensors": ["SDXL", "NSFW"],
        "flux1DevHyperNF4Flux1DevBNB_flux1DevHyperNF4.safetensors": ["Flux"],"STOIQONewrealityFLUXSD_F1DPreAlpha.safetensors": ["Flux"],
        "juggernautXL_v9Rundiffusionphoto2.safetensors": ["SDXL"],"animaPencilXL_v260.safetensors": ["SDXL"],
        "bluePencilXL_v401.safetensors": ["SDXL"],"pixelArtDiffusionXL_spriteShaper.safetensors": ["SDXL"],
        "albedobaseXL_v20.safetensors": ["SDXL"],"leosamsHelloworldXL_helloworldXL50GPT4V.safetensors": ["SDXL"],
        "dynavisionXLAllInOneStylized_releaseV0610Bakedvae.safetensors": ["SDXL"],"photon_v1.safetensors": ["SD 1.5"],
        "afroditexlNudePeople_20Bkdvae.safetensors": ["NSFW"],"nosft-float8-e4m3fn.safetensors": ["Flux", "NSFW"],
        "asdf_0.4a_lorapov_0.2_lust_0.4.fp16.safetensors": ["NSFW"],"PonyASDF_0.4_f6cosineb.fp16.safetensors": ["NSFW"],
        "Sexy_Aesthetic_SDXL_0.4x0.2.fp16.safetensors": ["NSFW"],"anikurender_0.4b.fp16.safetensors": ["NSFW"],
    }
    IMAGE_SIZE_TYPES = {
        "512x512": ["SD 1.5"], "512x768": ["SD 1.5"], "512x912": ["SD 1.5"], "576x768": ["SD 1.5"],"704x1344": ["SD 1.5"],
        "704x1408": ["SD 1.5"], "768x512": ["SD 1.5"], "768x576": ["SD 1.5"], "768x768": ["SD 1.5"],"768x1280": ["SD 1.5"],
        "768x1344": ["SD 1.5"], "832x1152": ["SD 1.5"],"832x1216": ["SD 1.5"], "896x1088": ["SD 1.5"], "896x1152": ["SD 1.5"],
        "912x512": ["SD 1.5"],"960x1024": ["SDXL", "Flux", "SD 1.5"], "960x1088": ["SDXL", "Flux", "SD 1.5"],
        "1024x1024": ["SDXL", "Flux", "SD 1.5"], "1024x960": ["SDXL", "Flux", "SD 1.5"],"1088x896": ["SDXL", "Flux", "SD 1.5"],
        "1088x960": ["SDXL", "Flux", "SD 1.5"],"1152x832": ["SDXL", "Flux", "SD 1.5"], "1152x896": ["SDXL", "Flux", "SD 1.5"],
        "1216x832": ["SDXL", "Flux"], "1280x768": ["SDXL", "Flux"], "1344x704": ["SDXL", "Flux"],"1344x768": ["SDXL", "Flux"],
        "1408x704": ["SDXL", "Flux"], "1472x704": ["SDXL", "Flux"],"1536x640": ["SDXL", "Flux"], "1600x640": ["SDXL", "Flux"],
        "1664x576": ["SDXL", "Flux"], "1728x576": ["SDXL", "Flux"]
    }

    # Задаем константы для опроса
    DEFAULT_POLL_INTERVAL = 3  # Секунды
    DEFAULT_MAX_WAIT_TIME = 300 # Секунды

    @classmethod
    def INPUT_TYPES(s):
        # Сортировка для UI
        s.CHECKPOINT_LIST.sort()
        # s.IMAGE_SIZE_LIST.sort(...) # Оставляем как есть или добавляем сложную сортировку
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "face_image": ("IMAGE",), # Входное изображение лица
                "positive_prompt": ("STRING", {"forceInput": True, "default": s.DEFAULT_PROMPT}), # Используем дефолтный промпт
                "checkpoint": (s.CHECKPOINT_LIST, {"default": "juggernautXL_v9Rundiffusionphoto2.safetensors"}),
                "imageSize": (s.IMAGE_SIZE_LIST, {"default": "1024x1024"}),
                "performance": (s.PERFORMANCE_LIST, {"default": "speed"}),
                # Убрали poll_interval и max_wait_time
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}), # Оставляем для UI
                "image_format": (["PNG", "JPEG"], {"default": "PNG"}) # Формат для Base64
            },
            "optional": {
                 "negative_prompt": ("STRING", {"forceInput": True}),
                 "multilang": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("status_text", "output_image")
    FUNCTION = "generate_face_image"
    CATEGORY = "PiperAPI/Image"

    # Убираем poll_interval, max_wait_time из аргументов, добавляем image_format
    def generate_face_image(self, api_key, face_image, positive_prompt, checkpoint, imageSize, performance,
                              seed, image_format, negative_prompt="", multilang=False):

        # Используем константы
        poll_interval = self.DEFAULT_POLL_INTERVAL
        max_wait_time = self.DEFAULT_MAX_WAIT_TIME

        # --- Предупреждение о совместимости (оставляем, т.к. полезно) ---
        checkpoint_types = self.CHECKPOINT_TYPES.get(checkpoint, [])
        size_types = self.IMAGE_SIZE_TYPES.get(imageSize, [])
        is_compatible = not checkpoint_types or not size_types or any(ct in size_types for ct in checkpoint_types)
        if not is_compatible:
            # Выводим как предупреждение, а не просто print
            print(f"⚠️ [PiperFaceToImage Предупреждение]: Чекпоинт '{checkpoint}' (Типы: {checkpoint_types}) "
                  f"может быть несовместим с размером '{imageSize}' (Типы: {size_types}).")
        # --- Конец предупреждения ---

        launch_url = "https://app.piper.my/api/face-to-image-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        empty_image = create_empty_image_tensor()
        status_text = "Ошибка: Неизвестный сбой."

        # 1. Конвертация изображения лица в Base64
        try:
            base64_face_uri = tensor_to_base64_data_uri(face_image, image_format=image_format)
            if not base64_face_uri:
                err_msg = "Критическая ошибка: Не удалось конвертировать изображение лица в Base64."
                print(f"[PiperFaceToImage] {err_msg}") # Логируем ошибку
                return (err_msg, empty_image)
        except Exception as e:
            print(f"[PiperFaceToImage] Критическая ошибка при конвертации лица в Base64:")
            traceback.print_exc()
            err_msg = f"Критическая ошибка подготовки Base64 лица: {e}"
            return (err_msg, empty_image)

        # 2. Подготовка и запуск задачи
        launch_data = {
            "inputs": {
                "face": base64_face_uri, # Используем Base64
                "prompt": positive_prompt,
                "checkpoint": checkpoint,
                "imageSize": imageSize,
                "performance": performance,
                "multilang": multilang,
                # Добавляем negativePrompt только если он не пустой
                **({"negativePrompt": negative_prompt} if negative_prompt and negative_prompt.strip() else {})
            }
        }

        try:
            # Используем post_request_json
            launch_response = post_request_json(launch_url, api_key, launch_data)
        except Exception as e:
             print(f"[PiperFaceToImage] Критическая ошибка сети при запуске задачи:")
             traceback.print_exc()
             err_msg = f"Критическая ошибка сети (запуск): {e}"
             return (err_msg, empty_image)

        # 3. Проверка ответа на запуск
        if not launch_response or not isinstance(launch_response, dict) or "_id" not in launch_response:
            api_error_details = "Неизвестно"
            if launch_response and isinstance(launch_response, dict): api_error_details = launch_response.get('error', launch_response)
            elif launch_response: api_error_details = str(launch_response)

            err_msg = f"Критическая ошибка: Не удалось запустить задачу или получить ID. Ответ API: {api_error_details}"
            print(f"[PiperFaceToImage] {err_msg}")
            return (err_msg, empty_image)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)
        # print(f"[PiperFaceToImage] Задача запущена. ID: {launch_id}. Опрос...") # Убрано

        # 4. Опрос состояния
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Критическая ошибка: Таймаут ({max_wait_time} сек) ожидания задачи {launch_id}"
                print(f"[PiperFaceToImage] {err_msg}")
                return (err_msg, empty_image)

            try:
                state_response = get_request(state_url, api_key)
            except Exception as e:
                 print(f"[PiperFaceToImage] Ошибка сети при опросе {launch_id} (повтор через {poll_interval} сек): {e}")
                 time.sleep(poll_interval)
                 continue

            if not state_response or not isinstance(state_response, dict):
                print(f"[PiperFaceToImage] Предупреждение: Некорректный ответ о состоянии {launch_id} (повтор через {poll_interval} сек).")
                time.sleep(poll_interval)
                continue

            errors = state_response.get("errors")
            if errors:
                if isinstance(errors, list) and len(errors) > 0: error_details = ', '.join(map(str, errors))
                elif isinstance(errors, str): error_details = errors
                else: error_details = str(errors)
                err_msg = f"Критическая ошибка API: Задача {launch_id} не удалась. Детали: {error_details}"
                print(f"[PiperFaceToImage] {err_msg}")
                # print(f"Full state response on error: {state_response}") # Можно раскомментировать для полной отладки ошибок API
                return (err_msg, empty_image)

            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict):
                 output_image_url = outputs.get("image")
                 if output_image_url and isinstance(output_image_url, str):
                     try:
                         output_image_tensor = url_to_image_tensor(output_image_url)
                         if output_image_tensor is None: # Проверка, если url_to_image_tensor вернул None
                             raise ValueError("Не удалось загрузить/обработать изображение по URL")
                         #status_text = f"Успех: Изображение сгенерировано задачей {launch_id}."
                         print(f"[PiperFaceToImage] {status_text}") # Выводим сообщение об успехе
                         return (status_text, output_image_tensor)
                     except Exception as e:
                         print(f"[PiperFaceToImage] Критическая ошибка обработки результирующего изображения ({launch_id}, URL: {output_image_url}):")
                         traceback.print_exc()
                         err_msg = f"Критическая ошибка обработки результата: {e}"
                         return (err_msg, empty_image)
                 else:
                     # Это тоже критическая ошибка - outputs есть, а URL картинки нет
                     err_msg = f"Критическая ошибка: В результатах задачи {launch_id} отсутствует или некорректен URL изображения. Ответ: {outputs}"
                     print(f"[PiperFaceToImage] {err_msg}")
                     return (err_msg, empty_image)

            # Если нет ни ошибок, ни outputs - ждем дальше
            time.sleep(poll_interval)