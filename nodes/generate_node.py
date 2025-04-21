import time
from .utils import post_request, get_request, url_to_image_tensor, create_empty_image_tensor

class PiperGenerateImage:
    MODEL_LIST = [
        "sdxl-turbo",
        "sd-3.5",
        "flux",
        "flux-pro",
        "flux-dev",
        "flux-schnell",
        "dall-e-3",
        "midjourney",
    ]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "prompt": ("STRING", {"forceInput": True}),
                "model": (s.MODEL_LIST, ),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "poll_interval": ("INT", {"default": 5, "min": 1, "max": 60}),
                "max_wait_time": ("INT", {"default": 300, "min": 30, "max": 1800}),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("status_text", "image_output")
    FUNCTION = "generate_image"
    CATEGORY = "PiperAPI/Image"

    def generate_image(self, api_key, prompt, model, seed, poll_interval, max_wait_time):
        print(f"PiperGenerateImage called with seed: {seed} (Note: Seed is used for refresh, not sent to API)")

        launch_url = "https://app.piper.my/api/generate-image-for-free-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        empty_image = create_empty_image_tensor()

        launch_data = {
            "inputs": {
                "prompt": prompt,
                "model": model
            }
        }
        print(f"Launching Piper generation with data: {launch_data}")

        launch_response = post_request(launch_url, api_key, launch_data)

        if not launch_response or "_id" not in launch_response:
            err_msg = "Error: Failed to launch generation or get launch ID."
            print(err_msg)
            return (err_msg, empty_image)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)

        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Error: Timed out waiting for generation {launch_id}"
                print(err_msg)
                return (err_msg, empty_image)

            state_response = get_request(state_url, api_key)

            if not state_response:
                print(f"Retrying state check in {poll_interval}s...")
                time.sleep(poll_interval)
                continue

            errors = state_response.get("errors")
            if errors and isinstance(errors, list) and len(errors) > 0:
                err_msg = f"Error: Generation failed (API Errors: {errors})"
                print(err_msg)
                print(f"Full state response: {state_response}")
                return (err_msg, empty_image)

            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict) and len(outputs) > 0:
                 image_url = outputs.get("image")

                 if image_url and isinstance(image_url, str):
                     image_tensor = url_to_image_tensor(image_url)
                     if image_tensor is not None:
                         status_msg = f"Success: Image generated from {image_url}"
                         return (status_msg, image_tensor,)
                     else:
                         err_msg = f"Completed, but failed to download/process image from {image_url}"
                         print(err_msg)
                         return (err_msg, empty_image)
                 else:
                     err_msg = f"Completed, but image URL not found or invalid in outputs: {outputs}"
                     print(err_msg)
                     return (err_msg, empty_image)

            print(f"Outputs/Errors are empty for {launch_id}. Assuming 'running'. Waiting {poll_interval}s...")
            time.sleep(poll_interval)