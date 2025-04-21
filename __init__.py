# api/__init__.py

# Импортируем маппинги из piper_nodes.py, чтобы ComfyUI мог их найти
from .piper_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Необязательно: для ясности можно добавить __all__
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

print("Piper API Custom Node Package Initialized (__init__.py)") 