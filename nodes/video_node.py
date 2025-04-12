# nodes/video_node.py
import time
import json

# Import helpers from utils.py within the same directory
from .utils import post_request, get_request

class PiperGenerateVideo:
    # Define modes for the dropdown
    MODE_LIST = ["preview", "draft", "production"]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "prompt": ("STRING", {"forceInput": True}),
                "mode": (s.MODE_LIST, {"default": "preview"}), # Mode dropdown
                "poll_interval": ("INT", {"default": 5, "min": 1, "max": 60}), # Polling might take longer for video
                "max_wait_time": ("INT", {"default": 600, "min": 30, "max": 3600}), # Video can take time
            }
        }

    # Output will be the video URL or status message
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_url_or_status",)
    FUNCTION = "generate_video"
    CATEGORY = "PiperAPI/Video" # Assign to the Video category

    def generate_video(self, api_key, prompt, mode, poll_interval, max_wait_time):
        launch_url = "https://app.piper.my/api/generate-video-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        default_error_result = json.dumps({"error": "Processing failed before completion"})

        # 1. Launch video generation
        launch_data = {
            "inputs": {
                "prompt": prompt,
                "mode": mode
            }
        }
        print(f"Launching Piper video generation with data: {launch_data}")
        launch_response = post_request(launch_url, api_key, launch_data)

        if not launch_response or "_id" not in launch_response:
            err_msg = "Error: Failed to launch video generation or get launch ID."
            print(err_msg)
            return (err_msg,) # Return error message

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)

        # 2. Poll based on 'outputs' and 'errors' fields
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Error: Timed out waiting for video generation {launch_id}"
                print(err_msg)
                return (err_msg,)

            state_response = get_request(state_url, api_key)

            if not state_response:
                print(f"Retrying state check in {poll_interval}s...")
                time.sleep(poll_interval)
                continue

            # Check for errors first
            errors = state_response.get("errors")
            if errors and isinstance(errors, list) and len(errors) > 0:
                err_msg = f"Error: Video generation failed (API Errors: {errors})"
                print(err_msg)
                print(f"Full state response: {state_response}")
                # Return the errors list as JSON string within the status message
                return (f"Error: API processing failed - {json.dumps(errors)}",)

            # Check if outputs are populated
            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict) and len(outputs) > 0:
                 # --- Try to extract video URL from outputs ---
                 # Guessing the key might be 'video', 'video_url', or 'url'
                 video_url = outputs.get("video") or outputs.get("video_url") or outputs.get("url")

                 if video_url and isinstance(video_url, str):
                     # Success! Return the video URL
                     return (video_url,)
                 else:
                     # URL not found or invalid in outputs
                     err_msg = f"Completed, but video URL not found or invalid in outputs: {outputs}"
                     print(err_msg)
                     # Return the outputs dict as string for debugging
                     return (f"Completed (no URL found): {json.dumps(outputs)}",)

            # If no errors and outputs are empty, assume it's still running
            time.sleep(poll_interval) 