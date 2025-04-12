# nodes/flux_image_node.py
import time
import json

# Import helpers (no upload needed for this one)
from .utils import post_request, get_request, url_to_image_tensor, create_empty_image_tensor

class PiperGenerateFluxImage:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "positive_prompt": ("STRING", {"forceInput": True}), # Input for prompt
                "poll_interval": ("INT", {"default": 2, "min": 1, "max": 30}), # Flux might be faster
                "max_wait_time": ("INT", {"default": 180, "min": 30, "max": 1800}),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("status_text", "output_image")
    FUNCTION = "generate_flux_image"
    CATEGORY = "PiperAPI/Image" # Keep in Image category

    def generate_flux_image(self, api_key, positive_prompt, poll_interval, max_wait_time):
        launch_url = "https://app.piper.my/api/generate-images-for-free-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        empty_image = create_empty_image_tensor()

        # 1. Launch Flux generation task
        launch_data = {
            "inputs": {
                "prompt": positive_prompt
            }
        }

        launch_response = post_request(launch_url, api_key, launch_data)

        if not launch_response or "_id" not in launch_response:
            err_msg = "Error: Failed to launch Flux generation or get launch ID."
            print(err_msg)
            return (err_msg, empty_image)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)

        # 2. Poll based on 'outputs' and 'errors' fields (standard logic)
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Error: Timed out waiting for Flux generation {launch_id}"
                print(err_msg)
                return (err_msg, empty_image)

            state_response = get_request(state_url, api_key)

            if not state_response:
                time.sleep(poll_interval)
                continue

            errors = state_response.get("errors")
            if errors and isinstance(errors, list) and len(errors) > 0:
                err_msg = f"Error: Flux generation failed (API Errors: {errors})"
                print(err_msg)
                print(f"Full state response: {state_response}")
                return (err_msg, empty_image)

            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict) and len(outputs) > 0:
                 output_image_url = outputs.get("image")

                 if output_image_url and isinstance(output_image_url, str):
                     output_image_tensor = url_to_image_tensor(output_image_url)
                     if output_image_tensor is not None:
                         return (f"Completed: {output_image_url}", output_image_tensor)
                     else:
                         err_msg = f"Completed, but failed to download/process Flux image from {output_image_url}"
                         print(err_msg)
                         return (err_msg, empty_image)
                 else:
                     err_msg = f"Completed, but output image URL not found or invalid in outputs: {outputs}"
                     print(err_msg)
                     return (err_msg, empty_image)

            time.sleep(poll_interval) 