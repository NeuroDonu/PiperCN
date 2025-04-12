# piper_nodes.py
# Removed requests and time imports as they are not directly used here anymore
import folder_paths # ComfyUI specific import for paths
import os
import sys
import importlib
import traceback

# Add the parent directory of 'nodes' to the path to allow imports like .nodes.utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import node classes directly
from .nodes.api_node import PiperApiKey
from .nodes.prompt_node import PiperPositivePrompt
from .nodes.negative_prompt_node import PiperNegativePrompt
from .nodes.generate_node import PiperGenerateImage
#from .nodes.violations_node import PiperViolationsDetector
from .nodes.video_node import PiperGenerateVideo
#from .nodes.dress_node import PiperDressFactory
from .nodes.save_video_node import PiperSaveVideo
from .nodes.deepseek_node import PiperAskDeepseek
from .nodes.llm_question_node import PiperLLMQuestion
#from .nodes.face_to_image_node import PiperFaceToImage
from .nodes.any_llm_node import PiperAskAnyLLM
#from .nodes.upscale_node import PiperUpscaleImage
from .nodes.flux_image_node import PiperGenerateFluxImage
from .nodes.fast_flux_image_node import PiperGenerateFastFluxImage

# --- Helper functions removed ---

# --- Node Mappings ---
NODE_CLASS_MAPPINGS = {
    "PiperApiKey": PiperApiKey,
    "PiperPositivePrompt": PiperPositivePrompt,
    "PiperNegativePrompt": PiperNegativePrompt,
    "PiperGenerateImage": PiperGenerateImage,
    #"PiperViolationsDetector": PiperViolationsDetector,
    "PiperGenerateVideo": PiperGenerateVideo,
    #"PiperDressFactory": PiperDressFactory,
    "PiperSaveVideo": PiperSaveVideo,
    "PiperAskDeepseek": PiperAskDeepseek,
    "PiperLLMQuestion": PiperLLMQuestion,
    #"PiperFaceToImage": PiperFaceToImage,
    "PiperAskAnyLLM": PiperAskAnyLLM,
    #"PiperUpscaleImage": PiperUpscaleImage,
    "PiperGenerateFluxImage": PiperGenerateFluxImage,
    "PiperGenerateFastFluxImage": PiperGenerateFastFluxImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PiperApiKey": "Piper API Key",
    "PiperPositivePrompt": "Piper Positive Prompt",
    "PiperNegativePrompt": "Piper Negative Prompt",
    "PiperGenerateImage": "Piper Generate Image (PiperAPI)",
    #"PiperViolationsDetector": "Piper Violations Detector (PiperAPI)",
    "PiperGenerateVideo": "Piper Generate Video (PiperAPI)",
    #"PiperDressFactory": "Piper Dress Factory (PiperAPI)",
    "PiperSaveVideo": "Piper Save Video (PiperAPI)",
    "PiperAskDeepseek": "Piper Ask Deepseek (PiperAPI)",
    "PiperLLMQuestion": "Piper LLM Question (PiperAPI)",
    #"PiperFaceToImage": "Piper Face To Image (PiperAPI)",
    "PiperAskAnyLLM": "Piper Ask Any LLM (PiperAPI)",
    #"PiperUpscaleImage": "Piper Upscale Image (PiperAPI)",
    "PiperGenerateFluxImage": "Piper Generate Flux Image (PiperAPI)",
    "PiperGenerateFastFluxImage": "Piper Generate Fast Flux (PiperAPI)",
}

# Optional: If you add custom JavaScript files for the UI
# WEB_DIRECTORY = "./js"

# Version and registration (optional)
__version__ = "1.0.0"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"] 