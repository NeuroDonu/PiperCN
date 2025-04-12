class PiperPositivePrompt:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "positive_prompt": ("STRING", {"multiline": True, "default": "A beautiful landscape"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("positive_prompt",)
    FUNCTION = "get_prompt"
    CATEGORY = "PiperAPI/Config"

    def get_prompt(self, positive_prompt):
        return (positive_prompt,) 