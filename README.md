# Piper ComfyUI Custom Nodes

Welcome! This custom node package integrates various Piper API functionalities into ComfyUI.

Currently available nodes:

*   **Piper API Key**: Manage your Piper API key.
*   **Piper Positive Prompt**: Define a positive prompt.
*   **Piper Negative Prompt**: Define a negative prompt.
*   **Piper Generate Image (PiperAPI)**: Generate images using the Piper API.
*   **Piper Generate Video (PiperAPI)**: Generate videos using the Piper API.
*   **Piper Save Video (PiperAPI)**: Save generated videos.
*   **Piper Ask Deepseek (PiperAPI)**: Query the Deepseek LLM via Piper API.
*   **Piper LLM Question (PiperAPI)**: Define a question for an LLM.
*   **Piper Ask Any LLM (PiperAPI)**: Query various LLMs via Piper API.
*   **Piper Generate Flux Image (PiperAPI)**: Generate images using the Flux model via Piper API.
*   **Piper Generate Fast Flux (PiperAPI)**: Generate images using the Fast Flux model via Piper API.

---

# Пользовательские ноды Piper для ComfyUI

Добро пожаловать! Этот пакет пользовательских нод интегрирует различные функции Piper API в ComfyUI.

Доступные на данный момент ноды:

*   **Piper API Key**: Управление вашим API-ключом Piper.
*   **Piper Positive Prompt**: Определение позитивного промпта.
*   **Piper Negative Prompt**: Определение негативного промпта.
*   **Piper Generate Image (PiperAPI)**: Генерация изображений с использованием Piper API.
*   **Piper Generate Video (PiperAPI)**: Генерация видео с использованием Piper API.
*   **Piper Save Video (PiperAPI)**: Сохранение сгенерированных видео.
*   **Piper Ask Deepseek (PiperAPI)**: Запрос к LLM Deepseek через Piper API.
*   **Piper LLM Question (PiperAPI)**: Определение вопроса для LLM.
*   **Piper Ask Any LLM (PiperAPI)**: Запрос к различным LLM через Piper API.
*   **Piper Generate Flux Image (PiperAPI)**: Генерация изображений с использованием модели Flux через Piper API.
*   **Piper Generate Fast Flux (PiperAPI)**: Генерация изображений с использованием модели Fast Flux через Piper API.

---

## How to Create Your Own Nodes (using AI Assistance)

Creating new nodes based on the existing ones can be straightforward with AI tools like Cursor:

1.  Open this project in Cursor.
2.  Find an existing node file in the `nodes/` directory that is similar to what you want to achieve (e.g., `nodes/api_node.py`, `nodes/generate_node.py`).
3.  Select the file (e.g., by using `@filename.py` in the chat).
4.  Instruct the AI: "Based on `@filename.py`, create a new file named `new_node_name.py` with the following logic: [describe the node's purpose], these inputs: [list inputs and types], and these outputs: [list outputs and types]."
5.  Remember to add your new node class to `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` in `piper_nodes.py`.

---

## Как создавать свои ноды (с помощью ИИ)

Создание новых нод на основе существующих может быть простым с использованием ИИ-инструментов, таких как Cursor:

1.  Откройте этот проект в Cursor.
2.  Найдите существующий файл ноды в директории `nodes/`, который похож на то, что вы хотите сделать (например, `nodes/api_node.py`, `nodes/generate_node.py`).
3.  Выберите файл (например, используя `@имя_файла.py` в чате).
4.  Дайте инструкцию ИИ: "На основе `@имя_файла.py` создай новый файл с именем `имя_новой_ноды.py` со следующей логикой: [опишите назначение ноды], такими входами: [перечислите входы и типы] и такими выходами: [перечислите выходы и типы]."
5.  Не забудьте добавить ваш новый класс ноды в `NODE_CLASS_MAPPINGS` и `NODE_DISPLAY_NAME_MAPPINGS` в файле `piper_nodes.py`.