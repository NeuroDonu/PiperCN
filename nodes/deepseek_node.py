# nodes/deepseek_node.py # Renamed file
import time
import json

# Import helpers from utils.py
from .utils import post_request, get_request

# Renamed class
class PiperAskDeepseek:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "question": ("STRING", {"forceInput": True}), # Take question as input
                "poll_interval": ("INT", {"default": 1, "min": 1, "max": 30}), # LLM should be fast
                "max_wait_time": ("INT", {"default": 60, "min": 10, "max": 300}), # Shorter timeout
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("llm_answer",)
    # Renamed function to reflect class name
    FUNCTION = "ask_deepseek"
    CATEGORY = "PiperAPI/LLM" # Keep in Main LLM category for now

    # Renamed method
    def ask_deepseek(self, api_key, question, poll_interval, max_wait_time):
        # Specific URL for Deepseek
        launch_url = "https://app.piper.my/api/ask-deepseek-r1-free-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        default_error_result = "Error: Processing failed before completion"

        # 1. Launch LLM task
        launch_data = {
            "inputs": {
                "question": question
            }
        }
        # print(f"Launching Piper Deepseek LLM with data: {launch_data}") # Remove info log
        launch_response = post_request(launch_url, api_key, launch_data)

        if not launch_response or "_id" not in launch_response:
            err_msg = "Error: Failed to launch Deepseek LLM task or get launch ID."
            print(err_msg) # Keep error log
            return (err_msg,)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)
        # print(f"Piper Deepseek LLM task launched with ID: {launch_id}") # Remove info log

        # 2. Poll based on 'outputs' and 'errors' fields (logic remains same)
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Error: Timed out waiting for Deepseek LLM response {launch_id}"
                print(err_msg) # Keep error log
                return (err_msg,)

            # print(f"Checking state for {launch_id}...") # Remove info log
            state_response = get_request(state_url, api_key)

            if not state_response:
                # print(f"Retrying state check in {poll_interval}s...") # Remove info log
                time.sleep(poll_interval)
                continue

            errors = state_response.get("errors")
            if errors and isinstance(errors, list) and len(errors) > 0:
                err_msg = f"Error: Deepseek LLM task failed (API Errors: {errors})"
                print(err_msg) # Keep error log
                print(f"Full state response: {state_response}") # Keep error details
                return (f"Error: API processing failed - {json.dumps(errors)}",)

            outputs = state_response.get("outputs")
            if outputs:
                 # print(f"Deepseek LLM task completed! Outputs: {outputs}") # Remove info log
                 answer = None
                 if isinstance(outputs, str):
                     answer = outputs
                 elif isinstance(outputs, dict):
                     answer = outputs.get("answer") or outputs.get("text") or outputs.get("result")
                     if answer is None and len(outputs) == 1:
                         answer = list(outputs.values())[0]

                 if answer is not None and isinstance(answer, str):
                     # print(f"Deepseek LLM Answer found: {answer[:100]}...") # Remove info log
                     return (answer,)
                 else:
                     err_msg = f"Completed, but answer not found or invalid in outputs: {outputs}"
                     print(err_msg) # Keep error log
                     return (f"Completed (no answer found): {json.dumps(outputs)}",)

            # print(f"Outputs/Errors are empty/None for {launch_id}. Assuming 'running'. Waiting {poll_interval}s...") # Remove info log
            time.sleep(poll_interval) 