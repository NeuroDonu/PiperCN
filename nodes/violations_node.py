# nodes/violations_node.py
import time
import json # For formatting the output string

# Import helpers from utils.py within the same directory
from .utils import post_request, get_request, upload_image_and_get_url

class PiperViolationsDetector:
    # Define default checks and maybe other constants if needed
    DEFAULT_CHECKS = "underage,nsfw"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "image": ("IMAGE",),
                "checks": ("STRING", {"multiline": False, "default": s.DEFAULT_CHECKS}),
                "poll_interval": ("INT", {"default": 2, "min": 1, "max": 60}), # Faster polling might be okay here
                "max_wait_time": ("INT", {"default": 120, "min": 10, "max": 600}), # Probably faster than image gen
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("results_text",)
    FUNCTION = "detect_violations"
    CATEGORY = "PiperAPI/Image"

    def parse_checks(self, checks_string):
        """Parses the comma-separated checks string into a list."""
        if not checks_string:
            return []
        return [check.strip() for check in checks_string.split(',') if check.strip()]

    def detect_violations(self, api_key, image, checks, poll_interval, max_wait_time):
        launch_url = "https://app.piper.my/api/violations-detector-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        default_error_result = json.dumps({"error": "Processing failed before completion"})

        # Upload image first
        uploaded_image_url = upload_image_and_get_url(image, api_key)
        if not uploaded_image_url:
            err_msg = "Error: Failed to upload image to get URL."
            print(err_msg)
            return (json.dumps({"error": err_msg}),)

        # Parse checks string into a list
        checks_list = self.parse_checks(checks)
        if not checks_list:
             # Use default if parsing resulted in empty list? Or error? Let's default.
             print(f"Warning: No valid checks provided, using default: {self.DEFAULT_CHECKS}")
             checks_list = self.parse_checks(self.DEFAULT_CHECKS)

        # 1. Launch detection
        launch_data = {
            "inputs": {
                "image": uploaded_image_url,
                "checks": checks_list
            }
        }
        print(f"Launching Piper violations detection with data: {launch_data}")
        launch_response = post_request(launch_url, api_key, launch_data)

        if not launch_response or "_id" not in launch_response:
            err_msg = "Error: Failed to launch detection or get launch ID."
            print(err_msg)
            return (json.dumps({"error": err_msg}),)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)
        print(f"Piper detection launched with ID: {launch_id}")

        # 2. Poll based on 'outputs' and 'errors' fields
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Error: Timed out waiting for detection {launch_id}"
                print(err_msg)
                return (json.dumps({"error": err_msg}),)

            print(f"Checking state for {launch_id}...")
            state_response = get_request(state_url, api_key)

            if not state_response:
                print(f"Retrying state check in {poll_interval}s...")
                time.sleep(poll_interval)
                continue

            # Check for errors first
            errors = state_response.get("errors")
            if errors and isinstance(errors, list) and len(errors) > 0:
                err_msg = f"Error: Detection failed (API Errors: {errors})"
                print(err_msg)
                print(f"Full state response: {state_response}")
                # Return the errors list as JSON string
                return (json.dumps({"error": "API processing failed", "details": errors}),)

            # Check if outputs are populated
            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict) and len(outputs) > 0:
                 print(f"Detection completed! Outputs: {outputs}")
                 # Return the whole outputs dictionary as a JSON string
                 return (json.dumps(outputs, indent=2),)

            # If no errors and outputs are empty, assume it's still running
            print(f"Outputs/Errors are empty for {launch_id}. Assuming 'running'. Waiting {poll_interval}s...")
            time.sleep(poll_interval) 