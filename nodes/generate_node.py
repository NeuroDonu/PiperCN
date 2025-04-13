# nodes/generate_node.py
import time
import requests
# Remove unused imports
# import io
# import torch
# import numpy as np
# from PIL import Image

# Import helpers from utils.py within the same directory
# Now also importing the image helpers
from .utils import post_request, get_request, url_to_image_tensor, create_empty_image_tensor

# Remove function definitions for url_to_image_tensor and create_empty_image_tensor
# Function to download and convert image URL to ComfyUI IMAGE tensor
# def url_to_image_tensor(image_url):
#    ...

# Function to create a dummy/empty tensor
# def create_empty_image_tensor(width=64, height=64):
#    ...

class PiperGenerateImage:
    # List of models for the dropdown
    MODEL_LIST = [
        "sdxl-turbo",
        "sd-3.5",
        "flux",
        "flux-pro",
        "flux-dev",
        "flux-schnell",
        "dall-e-3",
        "midjourney",
        # Add more models if needed
    ]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "prompt": ("STRING", {"forceInput": True}),
                "model": (s.MODEL_LIST, ), # Add model dropdown
                "poll_interval": ("INT", {"default": 5, "min": 1, "max": 60}),
                "max_wait_time": ("INT", {"default": 300, "min": 30, "max": 1800}),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("status_text", "image_output")
    FUNCTION = "generate_image"
    CATEGORY = "PiperAPI/Image"

    def generate_image(self, api_key, prompt, model, poll_interval, max_wait_time):
        launch_url = "https://app.piper.my/api/generate-image-for-free-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        empty_image = create_empty_image_tensor() # Use imported helper

        # 1. Launch generation
        launch_data = {
            "inputs": {
                "prompt": prompt,
                "model": model # Add the selected model here
            }
        }
        print(f"Launching Piper generation with data: {launch_data}") # Log launch data

        launch_response = post_request(launch_url, api_key, launch_data)

        if not launch_response or "_id" not in launch_response:
            err_msg = "Error: Failed to launch generation or get launch ID."
            print(err_msg)
            return (err_msg, empty_image) # Return error and empty image

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)

        # 2. Poll based on 'outputs' and 'errors' fields
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Error: Timed out waiting for generation {launch_id}"
                print(err_msg)
                return (err_msg, empty_image)

            state_response = get_request(state_url, api_key)

            if not state_response:
                # Handle case where get_request failed (already prints error)
                print(f"Retrying state check in {poll_interval}s...")
                time.sleep(poll_interval)
                continue

            # Check for errors first
            errors = state_response.get("errors")
            if errors and isinstance(errors, list) and len(errors) > 0:
                err_msg = f"Error: Generation failed (API Errors: {errors})"
                print(err_msg)
                print(f"Full state response: {state_response}")
                return (err_msg, empty_image)

            # Check if outputs are populated
            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict) and len(outputs) > 0:
                 # --- Try to extract URL from outputs["image"] and download ---
                 image_url = outputs.get("image") # Extract URL from the 'image' key

                 if image_url and isinstance(image_url, str):
                     image_tensor = url_to_image_tensor(image_url) # Use imported helper
                     if image_tensor is not None:
                         # Success! Return the status text and the image tensor
                         status_msg = f"Success: Image generated from {image_url}"
                         return (status_msg, image_tensor,)
                     else:
                         # Download or processing failed
                         err_msg = f"Completed, but failed to download/process image from {image_url}"
                         print(err_msg)
                         return (err_msg, empty_image)
                 else:
                     # URL not found or not a string in outputs["image"]
                     err_msg = f"Completed, but image URL not found or invalid in outputs: {outputs}"
                     print(err_msg)
                     return (err_msg, empty_image)

            # If no errors and outputs are empty, assume it's still running
            print(f"Outputs/Errors are empty for {launch_id}. Assuming 'running'. Waiting {poll_interval}s...")
            time.sleep(poll_interval) 