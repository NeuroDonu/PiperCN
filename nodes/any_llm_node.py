# nodes/any_llm_node.py
import time
import json

# Import helpers from utils.py
from .utils import post_request, get_request

class PiperAskAnyLLM:
    # Full list of models for the dropdown
    MODEL_LIST = [
        "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4", "gpt-4o", "o1", "o1-mini", "o3-mini",
        "gigachat", "meta-ai", "llama-2-7b", "llama-3-8b", "llama-3-70b", "llama-3.1-8b",
        "llama-3.1-70b", "llama-3.1-405b", "llama-3.2-1b", "llama-3.2-3b", "llama-3.2-11b",
        "llama-3.2-90b", "llama-3.3-70b", "mixtral-8x7b", "mixtral-8x22b", "mistral-nemo",
        "mixtral-small-24b", "hermes-3", "phi-3.5-mini", "phi-4", "wizardlm-2-7b",
        "wizardlm-2-8x22b", "gemini-exp", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0",
        "gemini-2.0-flash", "gemini-2.0-flash-thinking", "gemini-2.0-pro", "claude-3-haiku",
        "claude-3-sonnet", "claude-3-opus", "claude-3.5-sonnet", "claude-3.7-sonnet",
        "claude-3.7-sonnet-thinking", "reka-core", "blackboxai", "blackboxai-pro", "command-r",
        "command-r-plus", "command-r7b", "command-a", "qwen-1.5-7b", "qwen-2-72b",
        "qwen-2-vl-7b", "qwen-2.5-72b", "qwen-2.5-coder-32b", "qwen-2.5-1m", "qwen-2-5-max",
        "qwq-32b", "qvq-72b", "pi", "deepseek-chat", "deepseek-v3", "deepseek-r1",
        "janus-pro-7b", "grok-3", "grok-3-r1", "sonar", "sonar-pro", "sonar-reasoning",
        "sonar-reasoning-pro", "r1-1776", "nemotron-70b", "dbrx-instruct", "glm-4",
        "mini_max", "yi-34b", "dolphin-2.6", "dolphin-2.9", "airoboros-70b", "lzlv-70b",
        "minicpm-2.5", "tulu-3-1-8b", "tulu-3-70b", "tulu-3-405b", "olmo-1-7b", "olmo-2-13b",
        "olmo-2-32b", "olmo-4-synthetic", "lfm-40b", "evil"
    ]

    @classmethod
    def INPUT_TYPES(s):
        s.MODEL_LIST.sort() # Sort models alphabetically
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "question": ("STRING", {"forceInput": True}),
                "model": (s.MODEL_LIST, {"default": "gpt-4o-mini"}), # Add model selection
                "poll_interval": ("INT", {"default": 1, "min": 1, "max": 30}),
                "max_wait_time": ("INT", {"default": 120, "min": 10, "max": 600}), # Increased timeout slightly
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("llm_answer",)
    FUNCTION = "ask_any_llm" # New function name
    CATEGORY = "PiperAPI/LLM" # Main LLM category

    # New method name
    def ask_any_llm(self, api_key, question, model, poll_interval, max_wait_time):
        # Use the generic LLM agent URL
        launch_url = "https://app.piper.my/api/ask-llm-agent-free-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        default_error_result = "Error: Processing failed before completion"

        # 1. Launch LLM task including the selected model
        launch_data = {
            "inputs": {
                "question": question,
                "model": model # Pass selected model
            }
        }
        launch_response = post_request(launch_url, api_key, launch_data)

        if not launch_response or "_id" not in launch_response:
            err_msg = "Error: Failed to launch Any LLM task or get launch ID."
            print(err_msg)
            return (err_msg,)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)

        # 2. Poll based on 'outputs' and 'errors' fields (same logic as before)
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Error: Timed out waiting for Any LLM response {launch_id}"
                print(err_msg)
                return (err_msg,)

            state_response = get_request(state_url, api_key)

            if not state_response:
                print(f"Retrying state check in {poll_interval}s...")
                time.sleep(poll_interval)
                continue

            errors = state_response.get("errors")
            if errors and isinstance(errors, list) and len(errors) > 0:
                err_msg = f"Error: Any LLM task failed (API Errors: {errors})"
                print(err_msg)
                print(f"Full state response: {state_response}")
                return (f"Error: API processing failed - {json.dumps(errors)}",)

            outputs = state_response.get("outputs")
            if outputs:
                 answer = None
                 if isinstance(outputs, str):
                     answer = outputs
                 elif isinstance(outputs, dict):
                     answer = outputs.get("answer") or outputs.get("text") or outputs.get("result")
                     if answer is None and len(outputs) == 1:
                         answer = list(outputs.values())[0]

                 if answer is not None and isinstance(answer, str):
                     return (answer,)
                 else:
                     err_msg = f"Completed, but answer not found or invalid in outputs: {outputs}"
                     print(err_msg)
                     return (f"Completed (no answer found): {json.dumps(outputs)}",)

            time.sleep(poll_interval) 