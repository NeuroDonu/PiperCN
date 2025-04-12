# nodes/negative_prompt_node.py

class PiperNegativePrompt:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "negative_prompt": ("STRING", {"multiline": True, "default": "ugly, deformed, blurry"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("negative_prompt",)
    FUNCTION = "get_prompt"
    CATEGORY = "PiperAPI/Config" # Keep in Config category

    def get_prompt(self, negative_prompt):
        return (negative_prompt,) 