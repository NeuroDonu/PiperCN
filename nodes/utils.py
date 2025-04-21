# nodes/utils.py
import requests
import json
import io
import torch
import numpy as np
from PIL import Image
import base64

# Helper function to make POST requests
def post_request(url, api_key, data):
    headers = {
        'content-Type': 'application/json',
        'api-token': api_key
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            pass
        return None
    except json.JSONDecodeError:
        return None

def post_request_json(url, api_key, json_data):
    """
    Отправляет POST-запрос с данными JSON и API-ключом в заголовке.

    Args:
        url (str): URL для POST-запроса.
        api_key (str): Ваш API-ключ.
        json_data (dict): Словарь Python для отправки в теле запроса как JSON.

    Returns:
        dict or None: Ответ сервера в виде словаря Python или None в случае ошибки.
    """
    headers = {
        'api-token': api_key,
        'content-type': 'application/json' # Указываем, что отправляем JSON
    }
    try:
        # Сериализуем словарь Python в строку JSON
        data_payload = json.dumps(json_data)
        response = requests.post(url, headers=headers, data=data_payload, timeout=60) # timeout - время ожидания ответа
        response.raise_for_status() # Проверяем на HTTP-ошибки (4xx, 5xx)
        return response.json() # Возвращаем ответ сервера как словарь
    except requests.exceptions.RequestException as e:
        print(f"[Utils] Ошибка POST JSON запроса к {url}: {e}")
        # Попытаемся извлечь текст ответа, если он есть, для диагностики
        error_content = None
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_content = e.response.text
                print(f"[Utils] Ответ сервера при ошибке: {error_content}")
                # Попытка распарсить как JSON, если это возможно
                return e.response.json()
            except (AttributeError, ValueError, json.JSONDecodeError): # Если ответ не JSON или его нет
                 # Возвращаем словарь с ошибкой, чтобы нода могла его обработать
                 return {"error": f"HTTP Error: {e.response.status_code}. Response: {error_content or 'No content'}"}
        return {"error": f"Request failed: {e}"} # Если нет ответа сервера (например, таймаут, DNS)
    except json.JSONDecodeError:
        print(f"[Utils] Ошибка декодирования JSON ответа от {url}. Текст ответа: {response.text}")
        return {"error": "Invalid JSON response from server"}
    except Exception as e:
        # Ловим другие возможные ошибки
        print(f"[Utils] Непредвиденная ошибка при POST JSON запросе к {url}: {e}")
        return {"error": f"Unexpected error: {e}"}

# Helper function to make GET requests
def get_request(url, api_key):
    headers = {
        'api-token': api_key
    }
    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            pass
        return None
    except json.JSONDecodeError:
        return None

# --- Image Helper Functions ---

# Function to download and convert image URL to ComfyUI IMAGE tensor
def url_to_image_tensor(image_url):
    try:
        response = requests.get(image_url, timeout=60)
        response.raise_for_status()
        img_data = response.content
        i = Image.open(io.BytesIO(img_data))
        i = i.convert("RGB")
        image = np.array(i).astype(np.float32) / 255.0
        tensor = torch.from_numpy(image)[None,]
        return tensor
    except requests.exceptions.RequestException as e:
        return None
    except Exception as e:
        return None

# Function to create a dummy/empty tensor
def create_empty_image_tensor(width=64, height=64):
    image = np.zeros((height, width, 3), dtype=np.float32)
    tensor = torch.from_numpy(image)[None,]
    return tensor

# --- New Function: Upload Image Tensor ---
def tensor_to_pil(tensor):
    """Converts a ComfyUI IMAGE tensor to a PIL Image list."""
    if tensor is None:
        return []
    # Remove batch dimension, scale from 0-1 to 0-255, convert to numpy uint8
    images = tensor.cpu().numpy().squeeze(0) * 255.0
    images = np.clip(images, 0, 255).astype(np.uint8)
    # Convert to PIL Images
    pil_images = [Image.fromarray(img) for img in images]
    return pil_images

def upload_image_and_get_url(image_tensor, api_key):
    """
    Converts the first image from a tensor batch to PNG bytes,
    uploads it to the assumed Piper upload endpoint, and returns the public URL.
    Returns None if upload fails.
    """
    upload_url = "https://app.piper.my/api/upload-file-v1" # Assumed endpoint
    pil_images = tensor_to_pil(image_tensor)

    if not pil_images:
        return None

    # Use the first image from the batch
    image_pil = pil_images[0]

    # Convert PIL image to PNG bytes in memory
    with io.BytesIO() as byte_buffer:
        image_pil.save(byte_buffer, format="PNG")
        image_bytes = byte_buffer.getvalue()

    # Prepare headers and files for upload
    headers = {'api-token': api_key}
    # Assuming the API expects the file part named 'file'
    files = {'file': ('image.png', image_bytes, 'image/png')}

    try:
        response = requests.post(upload_url, headers=headers, files=files, timeout=60)
        response.raise_for_status()
        response_json = response.json()
        uploaded_url = response_json.get("url")
        if uploaded_url:
            return uploaded_url
        else:
            return None
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            pass
        return None
    except json.JSONDecodeError:
        return None
    except Exception as e:
        return None

# --- New Helper: Multipart POST Request ---
def post_request_multipart(url, api_key, json_data, image_tensor):
    """
    Sends a multipart/form-data request with a JSON 'inputs' part and an 'image' file part.
    """
    headers = {'api-token': api_key}
    # No 'Content-Type' header here, requests library handles it for multipart

    pil_images = tensor_to_pil(image_tensor)
    if not pil_images:
        return None
    image_pil = pil_images[0] # Use the first image

    # Convert PIL image to PNG bytes
    with io.BytesIO() as byte_buffer:
        image_pil.save(byte_buffer, format="PNG")
        image_bytes = byte_buffer.getvalue()

    # Prepare the multipart data
    # 'inputs' part containing the JSON data as a string
    # 'image' part containing the image file data
    files = {
        'inputs': (None, json.dumps(json_data), 'application/json'),
        'image': ('image.png', image_bytes, 'image/png')
    }

    try:
        response = requests.post(url, headers=headers, files=files, timeout=120) # Increased timeout
        response.raise_for_status()
        # Assume response is still JSON like other launch endpoints
        return response.json()
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            pass
        return None
    except json.JSONDecodeError:
        return None
    except Exception as e:
        return None 

def tensor_to_base64_data_uri(image_tensor, image_format='PNG'):
    """
    Конвертирует тензор изображения ComfyUI в строку Data URI (Base64).

    Args:
        image_tensor (torch.Tensor): Входной тензор (ожидается формат B, H, W, C, где B=1).
        image_format (str): Формат изображения ('PNG' или 'JPEG'). PNG рекомендуется для качества.

    Returns:
        str or None: Строка Data URI (например, "data:image/png;base64,...") или None в случае ошибки.
    """
    # 1. Конвертация Тензора в PIL Изображение (аналогично save_tensor_to_temp_file)
    try:
        if image_tensor.dim() == 4 and image_tensor.shape[0] == 1:
            image_tensor = image_tensor.squeeze(0)
        elif image_tensor.dim() != 3:
            print(f"[PiperUtils] Ошибка B64: Неожиданная размерность тензора: {image_tensor.shape}")
            return None

        image_tensor_cpu = image_tensor.cpu()
        image_np = image_tensor_cpu.numpy()

        if image_np.min() < 0.0 or image_np.max() > 1.0:
             print(f"[PiperUtils] B64 Предупреждение: Диапазон [{image_np.min()}, {image_np.max()}] выходит за [0.0, 1.0].")
             image_np = np.clip(image_np, 0.0, 1.0)

        image_np = (image_np * 255).astype(np.uint8)

        if image_np.shape[2] == 1:
            image_pil = Image.fromarray(image_np.squeeze(2), 'L')
        elif image_np.shape[2] == 3:
            image_pil = Image.fromarray(image_np, 'RGB')
        elif image_np.shape[2] == 4:
             image_pil = Image.fromarray(image_np, 'RGBA')
             # Если выбран JPEG, конвертируем в RGB, так как JPEG не поддерживает альфа-канал
             if image_format.upper() == 'JPEG':
                 print("[PiperUtils] B64 Предупреждение: RGBA конвертировано в RGB для сохранения в JPEG.")
                 image_pil = image_pil.convert('RGB')
        else:
            print(f"[PiperUtils] Ошибка B64: Неподдерживаемое кол-во каналов: {image_np.shape[2]}")
            return None
    except Exception as e:
        print(f"[PiperUtils] Ошибка B64 при конвертации тензора в PIL: {e}")
        traceback.print_exc()
        return None

    # 2. Сохранение PIL Изображения в байты в памяти
    try:
        buffer = io.BytesIO()
        # Убедимся, что формат поддерживается PIL
        valid_format = image_format.upper()
        if valid_format not in ['PNG', 'JPEG']:
            print(f"[PiperUtils] B64 Ошибка: Неподдерживаемый формат '{image_format}'. Используется PNG.")
            valid_format = 'PNG'

        # Качество для JPEG (опционально)
        save_kwargs = {}
        if valid_format == 'JPEG':
            save_kwargs['quality'] = 95 # Можно настроить качество

        image_pil.save(buffer, format=valid_format, **save_kwargs)
        image_bytes = buffer.getvalue()
        buffer.close()
    except Exception as e:
        print(f"[PiperUtils] Ошибка B64 при сохранении PIL в байты (формат {valid_format}): {e}")
        traceback.print_exc()
        return None

    # 3. Кодирование байтов в Base64
    try:
        base64_bytes = base64.b64encode(image_bytes)
        base64_string = base64_bytes.decode('utf-8') # Преобразуем байты base64 в строку
    except Exception as e:
        print(f"[PiperUtils] Ошибка B64 при кодировании в Base64: {e}")
        traceback.print_exc()
        return None

    # 4. Формирование строки Data URI
    mime_type = f"image/{valid_format.lower()}" # image/png или image/jpeg
    data_uri = f"data:{mime_type};base64,{base64_string}"

    #print(f"[PiperUtils] Тензор успешно конвертирован в Data URI (формат: {valid_format}, длина строки: {len(data_uri)})")
    return data_uri