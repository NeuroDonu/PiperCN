# nodes/save_video_node.py
import os
import requests
import folder_paths # Use ComfyUI's path handling

class PiperSaveVideo:
    def __init__(self):
        # Get the default ComfyUI output directory
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output" # Indicate this node saves files

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "video_url": ("STRING", {"forceInput": True}),
                "filename_prefix": ("STRING", {"default": "PiperVideo"}),
            },
            "optional": {
                 # Allow specifying a custom output directory relative to ComfyUI root
                 "output_dir": ("STRING", {"default": "", "multiline": False}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"}, # Standard hidden inputs
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("saved_video_path",)
    FUNCTION = "save_video"
    OUTPUT_NODE = True # Important for nodes that save files
    CATEGORY = "PiperAPI/Video"

    def get_sanitized_filename(self, filename):
        """ Basic sanitization to remove potentially problematic characters """
        # Remove path separators and control characters
        invalid_chars = r'<>:"/\|?*' + ''.join(chr(i) for i in range(32))
        sanitized = "".join(c for c in filename if c not in invalid_chars)
        # Replace spaces with underscores
        sanitized = sanitized.replace(" ", "_")
        # Limit length (optional)
        max_len = 100
        return sanitized[:max_len] if len(sanitized) > max_len else sanitized


    def save_video(self, video_url, filename_prefix, output_dir="", prompt=None, extra_pnginfo=None):
        # --- Determine Output Path ---
        # Use custom dir if provided, otherwise default ComfyUI output
        target_output_dir = self.output_dir
        subfolder = ""
        if output_dir and output_dir.strip():
             # Treat output_dir as relative to the ComfyUI base directory
             custom_path = os.path.abspath(os.path.join(folder_paths.base_path, output_dir.strip()))
             # Basic security check: ensure it's still within ComfyUI's base or default output path
             if custom_path.startswith(folder_paths.base_path) or custom_path.startswith(self.output_dir):
                 if not os.path.exists(custom_path):
                     try:
                         os.makedirs(custom_path, exist_ok=True)
                         print(f"Created output directory: {custom_path}")
                         target_output_dir = custom_path
                         # Determine subfolder relative to the *main* output dir for display name consistency
                         try:
                             subfolder = os.path.relpath(custom_path, self.output_dir)
                         except ValueError: # If on different drives, just use the custom dir name
                             subfolder = os.path.basename(custom_path)
                     except Exception as e:
                         print(f"Warning: Could not create custom output directory '{custom_path}'. Using default output. Error: {e}")
                         subfolder = "" # Reset subfolder if creation fails
                 else:
                     target_output_dir = custom_path
                     try:
                         subfolder = os.path.relpath(custom_path, self.output_dir)
                     except ValueError:
                         subfolder = os.path.basename(custom_path)
             else:
                 print(f"Warning: Custom output directory '{output_dir}' is outside allowed paths. Using default output.")
                 subfolder = ""
        else:
             subfolder = "" # No custom dir means saving directly to default output


        # --- Generate Filename (using folder_paths logic) ---
        # We need a placeholder extension for get_save_image_path, it will be replaced.
        # It doesn't actually look at image dimensions if we provide width/height=0
        full_output_folder, filename, counter, current_subfolder, _ = \
            folder_paths.get_save_image_path(filename_prefix, target_output_dir, 0, 0) # width=0, height=0

        # Replace the dummy extension with .mp4 (or determine from URL if possible)
        # Basic check, assuming mp4 for now. Could be improved by checking Content-Type header.
        file_extension = ".mp4"
        filename_no_ext = os.path.splitext(filename)[0]
        final_filename = f"{filename_no_ext}{file_extension}"
        full_filepath = os.path.join(full_output_folder, final_filename)

        # --- Download Video ---
        saved = False
        try:
            print(f"Attempting to download video from: {video_url}")
            print(f"Attempting to save video to: {full_filepath}")
            response = requests.get(video_url, stream=True, timeout=120) # Longer timeout for video
            response.raise_for_status()
            with open(full_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192 * 16): # Larger chunk size for video
                    f.write(chunk)
            print(f"Video successfully downloaded and saved: {full_filepath}")
            saved = True
        except requests.exceptions.RequestException as e:
            print(f"Error downloading video: {e}")
        except Exception as e:
            print(f"Error saving video file: {e}")

        # --- Return Result ---
        if saved:
            # Structure expected by ComfyUI frontend for display
            results = list()
            results.append({
                 "filename": final_filename,
                 "subfolder": current_subfolder if current_subfolder else subfolder, # Use subfolder from get_save_image_path if possible
                 "type": self.type
            })
            return {"ui": {"videos": results}, "result": (full_filepath,)} # Pass path back and UI info
        else:
            return {"ui": {"error": ["Video download/save failed."]}, "result": ("ERROR: Download failed",)} 