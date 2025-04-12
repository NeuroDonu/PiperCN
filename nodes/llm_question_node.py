# nodes/llm_question_node.py

class PiperLLMQuestion:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "question": ("STRING", {"multiline": True, "default": "What is your name?"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("question",)
    FUNCTION = "get_question"
    # Place input/output config nodes in a sub-subcategory
    CATEGORY = "PiperAPI/LLM/Config"

    def get_question(self, question):
        return (question,) 