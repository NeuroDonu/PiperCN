# nodes/llm_output_node.py

class PiperLLMOutput:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # This node takes text input, likely the answer from the LLM node
                "llm_answer": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("llm_answer",)
    FUNCTION = "get_answer"
    # Place input/output config nodes in a sub-subcategory
    CATEGORY = "PiperAPI/LLM/Config"

    def get_answer(self, llm_answer):
        # Simply pass the input text through
        return (llm_answer,) 