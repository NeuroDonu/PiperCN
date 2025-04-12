# nodes/dress_node.py
import time
import json

# Import helpers from utils.py
# Includes post_request, get_request, url_to_image_tensor, create_empty_image_tensor, upload_image_and_get_url
from .utils import post_request, get_request, url_to_image_tensor, create_empty_image_tensor, upload_image_and_get_url

class PiperDressFactory:
    # Define options for dropdowns
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
    # Remove default image URL as we now take IMAGE input
    # DEFAULT_IMAGE_URL = "https://huggingface.co/PiperMy/Pipelines/resolve/main/assets/persons/stewardess.jpg"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                # Change input type from STRING to IMAGE
                "image": ("IMAGE",),
                "gender": (s.GENDER_LIST, {"default": "auto"}),
                "style": (s.STYLE_LIST, {"default": "red_swimsuit"}),
                "poll_interval": ("INT", {"default": 3, "min": 1, "max": 60}),
                "max_wait_time": ("INT", {"default": 300, "min": 30, "max": 1800}),
            },
            "optional": { # Prompt is optional for this endpoint based on API spec
                 "prompt": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("status_text", "output_image")
    FUNCTION = "dress_image"
    CATEGORY = "PiperAPI/Image" # Keep in Image category

    def dress_image(self, api_key, image, gender, style, poll_interval, max_wait_time, prompt=None):
        launch_url = "https://app.piper.my/api/dress-factory-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        empty_image = create_empty_image_tensor() # Use shared helper

        # --- Upload Image First ---
        uploaded_image_url = upload_image_and_get_url(image, api_key)
        if not uploaded_image_url:
            err_msg = "Error: Failed to upload image to get URL for Dress Factory."
            print(err_msg) # Keep error log
            return (err_msg, empty_image)
        # --- End Upload ---

        # 1. Launch dress factory task using uploaded URL
        launch_data = {
            "inputs": {
                "image": uploaded_image_url, # Use URL from upload
                "gender": gender,
                "style": style
            }
        }
        # Add prompt only if provided
        if prompt and prompt.strip():
            launch_data["inputs"]["prompt"] = prompt.strip()

        # print(f"Launching Piper Dress Factory with data: {launch_data}") # Remove info log
        launch_response = post_request(launch_url, api_key, launch_data)

        if not launch_response or "_id" not in launch_response:
            err_msg = "Error: Failed to launch dress factory or get launch ID."
            print(err_msg) # Keep error log
            return (err_msg, empty_image)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)
        # print(f"Piper Dress Factory launched with ID: {launch_id}") # Remove info log

        # 2. Poll based on 'outputs' and 'errors' fields (same logic as generate_image)
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Error: Timed out waiting for dress factory {launch_id}"
                print(err_msg) # Keep error log
                return (err_msg, empty_image)

            # print(f"Checking state for {launch_id}...") # Remove info log
            state_response = get_request(state_url, api_key)

            if not state_response:
                # print(f"Retrying state check in {poll_interval}s...") # Remove info log
                time.sleep(poll_interval)
                continue

            errors = state_response.get("errors")
            if errors and isinstance(errors, list) and len(errors) > 0:
                err_msg = f"Error: Dress Factory failed (API Errors: {errors})"
                print(err_msg) # Keep error log
                print(f"Full state response: {state_response}") # Keep error details
                return (err_msg, empty_image)

            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict) and len(outputs) > 0:
                 # print(f"Dress Factory completed! Outputs: {outputs}") # Remove info log
                 output_image_url = outputs.get("image")

                 if output_image_url and isinstance(output_image_url, str):
                     # print(f"Output image URL found: {output_image_url}") # Remove info log
                     output_image_tensor = url_to_image_tensor(output_image_url) # Use shared helper
                     if output_image_tensor is not None:
                         # Success!
                         return (f"Completed: {output_image_url}", output_image_tensor)
                     else:
                         err_msg = f"Completed, but failed to download/process image from {output_image_url}"
                         print(err_msg) # Keep error log
                         return (err_msg, empty_image)
                 else:
                     err_msg = f"Completed, but output image URL not found or invalid in outputs: {outputs}"
                     print(err_msg) # Keep error log
                     return (err_msg, empty_image)

            # print(f"Outputs/Errors are empty for {launch_id}. Assuming 'running'. Waiting {poll_interval}s...") # Remove info log
            time.sleep(poll_interval) 