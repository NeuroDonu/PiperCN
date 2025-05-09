import time
import json
from .utils import post_request, get_request, url_to_image_tensor, create_empty_image_tensor

class PiperGenerateFastFluxImage:
    ASPECT_RATIO_LIST = [
        "1:1", "21:9", "16:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:21", "9:16"
    ]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "positive_prompt": ("STRING", {"forceInput": True}),
                "aspect_ratio": (s.ASPECT_RATIO_LIST, {"default": "1:1"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "poll_interval": ("INT", {"default": 1, "min": 1, "max": 10}),
                "max_wait_time": ("INT", {"default": 60, "min": 10, "max": 300}),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("status_text", "output_image")
    FUNCTION = "generate_fast_flux_image"
    CATEGORY = "PiperAPI/Image"

    def generate_fast_flux_image(self, api_key, positive_prompt, aspect_ratio, seed, poll_interval, max_wait_time):
        print(f"PiperGenerateFastFluxImage called with seed: {seed} (Note: Seed is used for refresh, not sent to API)")

        launch_url = "https://app.piper.my/api/instant-flux-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        empty_image = create_empty_image_tensor()

        launch_data = {
            "inputs": {
                "prompt": positive_prompt,
                "aspectRatio": aspect_ratio,
                "imagesCount": 1
            }
        }
        print(f"Launching Fast Flux generation with data: {launch_data}")

        launch_response = post_request(launch_url, api_key, launch_data)

        if not launch_response or "_id" not in launch_response:
            err_msg = "Error: Failed to launch Fast Flux generation or get launch ID."
            print(err_msg)
            return (err_msg, empty_image)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)

        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Error: Timed out waiting for Fast Flux generation {launch_id}"
                print(err_msg)
                return (err_msg, empty_image)

            state_response = get_request(state_url, api_key)

            if not state_response:
                print(f"Retrying state check in {poll_interval}s...")
                time.sleep(poll_interval)
                continue

            errors = state_response.get("errors")
            if errors and isinstance(errors, list) and len(errors) > 0:
                err_msg = f"Error: Fast Flux generation failed (API Errors: {errors})"
                print(err_msg)
                print(f"Full state response: {state_response}")
                return (err_msg, empty_image)

            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict) and len(outputs) > 0:
                 output_image_url = outputs.get("image")

                 if output_image_url and isinstance(output_image_url, str):
                     output_image_tensor = url_to_image_tensor(output_image_url)
                     if output_image_tensor is not None:
                         status_msg = f"Success: Image generated from {output_image_url}"
                         return (status_msg, output_image_tensor,)
                     else:
                         err_msg = f"Completed, but failed to download/process Fast Flux image from {output_image_url}"
                         print(err_msg)
                         return (err_msg, empty_image)
                 else:
                     err_msg = f"Completed, but output image URL not found or invalid in outputs: {outputs}"
                     print(err_msg)
                     return (err_msg, empty_image)

            print(f"Outputs/Errors are empty for {launch_id}. Assuming 'running'. Waiting {poll_interval}s...")
            time.sleep(poll_interval)