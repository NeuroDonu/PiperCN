# nodes/upscale_node.py
import time
import json

# Import multipart helper, remove upload helper
from .utils import get_request, url_to_image_tensor, create_empty_image_tensor, post_request_multipart

class PiperUpscaleImage:
    # Define options for upscaling factor
    UPSCALE_FACTORS = [2, 3, 4] # User request for int factors

    @classmethod
    def INPUT_TYPES(s):
        # Convert int factors to strings for the COMBO widget
        factor_strings = [str(f) for f in s.UPSCALE_FACTORS]
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "image": ("IMAGE",), # Input image tensor
                # Use COMBO for specific factors
                "upscaling_factor": (factor_strings, {"default": "2"}),
                "poll_interval": ("INT", {"default": 2, "min": 1, "max": 30}),
                "max_wait_time": ("INT", {"default": 300, "min": 30, "max": 1800}),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("status_text", "output_image")
    FUNCTION = "upscale_image"
    CATEGORY = "PiperAPI/Image" # Image processing category

    def upscale_image(self, api_key, image, upscaling_factor, poll_interval, max_wait_time):
        launch_url = "https://app.piper.my/api/upscale-image-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        empty_image = create_empty_image_tensor()

        # Convert factor to float
        try:
             upscale_value = float(upscaling_factor)
        except ValueError:
             err_msg = f"Error: Invalid upscaling factor '{upscaling_factor}'."
             return (err_msg, empty_image)

        # 1. Launch upscale task using multipart request
        # Prepare the JSON part of the multipart request
        json_input_data = {
            "inputs": {
                "upscalingResize": upscale_value
            }
        }
        # Use the new helper function, passing the image tensor directly
        launch_response = post_request_multipart(launch_url, api_key, json_input_data, image)

        if not launch_response or "_id" not in launch_response:
            err_msg = "Error: Failed to launch upscaling task or get launch ID."
            return (err_msg, empty_image)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)

        # 2. Poll based on 'outputs' and 'errors' fields (standard logic)
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Error: Timed out waiting for upscaling {launch_id}"
                return (err_msg, empty_image)

            state_response = get_request(state_url, api_key)

            if not state_response:
                time.sleep(poll_interval)
                continue

            errors = state_response.get("errors")
            if errors and isinstance(errors, list) and len(errors) > 0:
                err_msg = f"Error: Upscaling failed (API Errors: {errors})"
                return (err_msg, empty_image)

            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict) and len(outputs) > 0:
                 output_image_url = outputs.get("image")

                 if output_image_url and isinstance(output_image_url, str):
                     output_image_tensor = url_to_image_tensor(output_image_url)
                 else:
                     return (err_msg, empty_image)

            time.sleep(poll_interval) 