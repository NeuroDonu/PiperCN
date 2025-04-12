# nodes/face_to_image_node.py
import time
import json

# Import helpers including upload and image conversion
from .utils import post_request, get_request, url_to_image_tensor, create_empty_image_tensor, upload_image_and_get_url

class PiperFaceToImage:
    # Define full options for dropdowns
    CHECKPOINT_LIST = [
        "raemuXL_v40.safetensors", # SDXL
        "aamXLAnimeMix_v10.safetensors", # SDXL, Fantasy
        "dreamweaverPony25D.1erv.safetensors", # SDXL
        "mixGEMAdam8witQegoow.NeWz.safetensors", # SDXL, Realistic
        "mfcgPDXL_v10.safetensors", # SDXL
        "aniku_0.2.fp16.safetensors", # SDXL, Fantasy, NSFW
        "flux1DevHyperNF4Flux1DevBNB_flux1DevHyperNF4.safetensors", # Flux
        "STOIQONewrealityFLUXSD_F1DPreAlpha.safetensors", # Flux
        "juggernautXL_v9Rundiffusionphoto2.safetensors", # SDXL
        "animaPencilXL_v260.safetensors", # SDXL, Fantasy
        "bluePencilXL_v401.safetensors", # SDXL, Fantasy
        "pixelArtDiffusionXL_spriteShaper.safetensors", # SDXL, Fantasy
        "albedobaseXL_v20.safetensors", # SDXL
        "leosamsHelloworldXL_helloworldXL50GPT4V.safetensors", # SDXL
        "dynavisionXLAllInOneStylized_releaseV0610Bakedvae.safetensors", # SDXL
        "photon_v1.safetensors", # SD 1.5
        "afroditexlNudePeople_20Bkdvae.safetensors", # NSFW
        "nosft-float8-e4m3fn.safetensors", # Flux, NSFW
        "asdf_0.4a_lorapov_0.2_lust_0.4.fp16.safetensors", # NSFW
        "PonyASDF_0.4_f6cosineb.fp16.safetensors", # NSFW
        "Sexy_Aesthetic_SDXL_0.4x0.2.fp16.safetensors", # NSFW
        "anikurender_0.4b.fp16.safetensors", # NSFW
    ]
    IMAGE_SIZE_LIST = [
        # SD 1.5 Sizes
        "512x512", "512x768", "512x912", "576x768", "704x1344", "704x1408",
        "768x512", "768x576", "768x768", "768x1280", "768x1344", "832x1152",
        "832x1216", "896x1088", "896x1152", "912x512",
        # SDXL / Flux / SD 1.5 Mix Sizes
        "960x1024", "960x1088", "1024x1024", "1024x960", "1088x896", "1088x960",
        "1152x832", "1152x896",
        # SDXL / Flux Sizes
        "1216x832", "1280x768", "1344x704", "1344x768", "1408x704",
        "1472x704", "1536x640", "1600x640", "1664x576", "1728x576"
    ]
    PERFORMANCE_LIST = ["speed", "quality", "express"]
    DEFAULT_PROMPT = "A man sits at a table, looking directly at the front camera. He has a neutral expression, soft lighting, and a sharp focus on his face. The background is minimal and slightly blurred. Cinematic composition, high detail, realistic skin texture, 4K resolution."

    # --- Compatibility Info (Internal Use for Warning) ---
    # Approximation based on user provided tags
    CHECKPOINT_TYPES = {
        "raemuXL_v40.safetensors": ["SDXL"],
        "aamXLAnimeMix_v10.safetensors": ["SDXL"],
        "dreamweaverPony25D.1erv.safetensors": ["SDXL"],
        "mixGEMAdam8witQegoow.NeWz.safetensors": ["SDXL"],
        "mfcgPDXL_v10.safetensors": ["SDXL"],
        "aniku_0.2.fp16.safetensors": ["SDXL", "NSFW"],
        "flux1DevHyperNF4Flux1DevBNB_flux1DevHyperNF4.safetensors": ["Flux"],
        "STOIQONewrealityFLUXSD_F1DPreAlpha.safetensors": ["Flux"],
        "juggernautXL_v9Rundiffusionphoto2.safetensors": ["SDXL"],
        "animaPencilXL_v260.safetensors": ["SDXL"],
        "bluePencilXL_v401.safetensors": ["SDXL"],
        "pixelArtDiffusionXL_spriteShaper.safetensors": ["SDXL"],
        "albedobaseXL_v20.safetensors": ["SDXL"],
        "leosamsHelloworldXL_helloworldXL50GPT4V.safetensors": ["SDXL"],
        "dynavisionXLAllInOneStylized_releaseV0610Bakedvae.safetensors": ["SDXL"],
        "photon_v1.safetensors": ["SD 1.5"],
        "afroditexlNudePeople_20Bkdvae.safetensors": ["NSFW"], # Assuming SDXL base if not specified
        "nosft-float8-e4m3fn.safetensors": ["Flux", "NSFW"],
        "asdf_0.4a_lorapov_0.2_lust_0.4.fp16.safetensors": ["NSFW"], # Assuming SD 1.5 base?
        "PonyASDF_0.4_f6cosineb.fp16.safetensors": ["NSFW"], # Assuming SDXL/Pony base?
        "Sexy_Aesthetic_SDXL_0.4x0.2.fp16.safetensors": ["NSFW"], # Assuming SDXL base
        "anikurender_0.4b.fp16.safetensors": ["NSFW"], # Assuming SD 1.5/Anime base?
    }
    IMAGE_SIZE_TYPES = {
        "512x512": ["SD 1.5"], "512x768": ["SD 1.5"], "512x912": ["SD 1.5"], "576x768": ["SD 1.5"],
        "704x1344": ["SD 1.5"], "704x1408": ["SD 1.5"], "768x512": ["SD 1.5"], "768x576": ["SD 1.5"],
        "768x768": ["SD 1.5"], "768x1280": ["SD 1.5"], "768x1344": ["SD 1.5"], "832x1152": ["SD 1.5"],
        "832x1216": ["SD 1.5"], "896x1088": ["SD 1.5"], "896x1152": ["SD 1.5"], "912x512": ["SD 1.5"],
        "960x1024": ["SDXL", "Flux", "SD 1.5"], "960x1088": ["SDXL", "Flux", "SD 1.5"],
        "1024x1024": ["SDXL", "Flux", "SD 1.5"], "1024x960": ["SDXL", "Flux", "SD 1.5"],
        "1088x896": ["SDXL", "Flux", "SD 1.5"], "1088x960": ["SDXL", "Flux", "SD 1.5"],
        "1152x832": ["SDXL", "Flux", "SD 1.5"], "1152x896": ["SDXL", "Flux", "SD 1.5"],
        "1216x832": ["SDXL", "Flux"], "1280x768": ["SDXL", "Flux"], "1344x704": ["SDXL", "Flux"],
        "1344x768": ["SDXL", "Flux"], "1408x704": ["SDXL", "Flux"], "1472x704": ["SDXL", "Flux"],
        "1536x640": ["SDXL", "Flux"], "1600x640": ["SDXL", "Flux"], "1664x576": ["SDXL", "Flux"],
        "1728x576": ["SDXL", "Flux"]
    }

    @classmethod
    def INPUT_TYPES(s):
        # Sort lists alphabetically for better UI presentation
        s.CHECKPOINT_LIST.sort()
        # Custom sort for image sizes (optional, can be complex)
        # s.IMAGE_SIZE_LIST.sort(key=lambda x: int(x.split('x')[0]) * int(x.split('x')[1]))
        return {
            "required": {
                "api_key": ("STRING", {"forceInput": True}),
                "face_image": ("IMAGE",),
                "positive_prompt": ("STRING", {"forceInput": True}),
                "checkpoint": (s.CHECKPOINT_LIST, {"default": "juggernautXL_v9Rundiffusionphoto2.safetensors"}),
                "imageSize": (s.IMAGE_SIZE_LIST, {"default": "1024x1024"}), # Use the full list
                "performance": (s.PERFORMANCE_LIST, {"default": "speed"}),
                "poll_interval": ("INT", {"default": 3, "min": 1, "max": 60}),
                "max_wait_time": ("INT", {"default": 300, "min": 30, "max": 1800}),
            },
            "optional": {
                 "negative_prompt": ("STRING", {"forceInput": True}),
                 "multilang": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("status_text", "output_image")
    FUNCTION = "generate_face_image"
    CATEGORY = "PiperAPI/Image"

    def generate_face_image(self, api_key, face_image, positive_prompt, checkpoint, imageSize, performance,
                              poll_interval, max_wait_time, negative_prompt="", multilang=False):
        # --- Add Compatibility Warning ---
        checkpoint_types = self.CHECKPOINT_TYPES.get(checkpoint, [])
        size_types = self.IMAGE_SIZE_TYPES.get(imageSize, [])
        # Check if there's *any* overlap or if either list is empty (unknown compatibility)
        is_compatible = not checkpoint_types or not size_types or any(ct in size_types for ct in checkpoint_types)
        if not is_compatible:
            print(f"⚠️ Piper Warning: Checkpoint '{checkpoint}' (Types: {checkpoint_types}) "
                  f"might be incompatible with image size '{imageSize}' (Types: {size_types}). "
                  f"Attempting API call anyway.")
        # --- End Warning ---

        launch_url = "https://app.piper.my/api/face-to-image-v1/launch"
        state_url_template = "https://app.piper.my/api/launches/{}/state"
        empty_image = create_empty_image_tensor()

        uploaded_face_url = upload_image_and_get_url(face_image, api_key)
        if not uploaded_face_url:
            err_msg = "Error: Failed to upload face image to get URL."
            return (err_msg, empty_image)

        launch_data = {
            "inputs": {
                "face": uploaded_face_url, "prompt": positive_prompt, "checkpoint": checkpoint,
                "imageSize": imageSize, "performance": performance, "multilang": multilang,
                "negativePrompt": negative_prompt,
            }
        }
        if not negative_prompt or not negative_prompt.strip():
            if "negativePrompt" in launch_data["inputs"]: del launch_data["inputs"]["negativePrompt"]

        print(f"Launching Piper FaceToImage with data: {launch_data}")
        launch_response = post_request(launch_url, api_key, launch_data)

        if not launch_response or "_id" not in launch_response:
            err_msg = "Error: Failed to launch FaceToImage or get launch ID."
            return (err_msg, empty_image)

        launch_id = launch_response["_id"]
        state_url = state_url_template.format(launch_id)
        print(f"Piper FaceToImage launched with ID: {launch_id}")

        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > max_wait_time:
                err_msg = f"Error: Timed out waiting for FaceToImage {launch_id}"
                return (err_msg, empty_image)

            print(f"Checking state for {launch_id}...")
            state_response = get_request(state_url, api_key)

            if not state_response:
                print(f"Retrying state check in {poll_interval}s...")
                time.sleep(poll_interval)
                continue

            errors = state_response.get("errors")
            if errors and isinstance(errors, list) and len(errors) > 0:
                err_msg = f"Error: FaceToImage failed (API Errors: {errors})"
                print(err_msg)
                print(f"Full state response: {state_response}")
                return (err_msg, empty_image)

            outputs = state_response.get("outputs")
            if outputs and isinstance(outputs, dict) and len(outputs) > 0:
                print(f"FaceToImage completed! Outputs: {outputs}")
                output_image_url = outputs.get("image")

                if output_image_url and isinstance(output_image_url, str):
                    print(f"Output image URL found: {output_image_url}")
                    output_image_tensor = url_to_image_tensor(output_image_url)
                    if output_image_tensor is not None:
                        return (f"Completed: {output_image_url}", output_image_tensor)
                    else:
                        err_msg = f"Completed, but failed to download/process image from {output_image_url}"
                        print(err_msg)
                        return (err_msg, empty_image)
                else:
                    err_msg = f"Completed, but output image URL not found or invalid in outputs: {outputs}"
                    print(err_msg)
                    return (err_msg, empty_image)

            print(f"Outputs/Errors are empty for {launch_id}. Assuming 'running'. Waiting {poll_interval}s...")
            time.sleep(poll_interval) 