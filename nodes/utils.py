# nodes/utils.py
import requests
import json
import io
import torch
import numpy as np
from PIL import Image

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