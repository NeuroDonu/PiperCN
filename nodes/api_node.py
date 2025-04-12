class PiperApiKey:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "api_key": ("STRING", {"multiline": False, "default": "[YOUR_API_KEY_HERE]"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("api_key",)
    FUNCTION = "get_api_key"
    CATEGORY = "PiperAPI/Config" # Updated Category

    def get_api_key(self, api_key):
        return (api_key,) 