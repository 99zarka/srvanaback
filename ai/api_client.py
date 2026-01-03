"""
This script provides a unified and enhanced AI client (`AIClient`) for interacting with
various Large Language Model (LLM) providers, including Google Gemini, OpenAI, and any
provider compatible with the OpenRouter API.

Features:
- Unified Interface: A single `call_llm` method to access different models.
- Multi-Provider Support: Routes requests to Gemini, OpenAI, or OpenRouter based on the model name prefix.
- Multi-Modal Input: Handles text prompts, conversation history, image URLs, file URLs, and structured context from a RAG system.
- Retry Logic: Automatically retries API calls on transient errors (like rate limiting).
- Standalone Testing: Can be run directly to test its functionalities.

-------------------------------------------------------------------------------
SETUP
-------------------------------------------------------------------------------

1.  **Dependencies**: Ensure you have the required Python packages installed.
    ```bash
    pip install requests python-dotenv numpy
    ```

2.  **Environment Variables**: Create a `.env` file in the same directory as this script
    and add your API keys. The script will automatically load them.

    Example `.env` file:
    ```
    GEMINI_API_KEY="your_google_gemini_api_key"
    OPENAI_API_KEY="your_openai_api_key"
    OPENROUTER_API_KEY="your_openrouter_api_key"
    ```

-------------------------------------------------------------------------------
USAGE AS A LIBRARY
-------------------------------------------------------------------------------

Import the `AIClient` and use the static `call_llm` method to make requests.

**Example 1: Simple text prompt**
```python
from api_client import AIClient

response = AIClient.call_llm(
    model="gemini-1.5-flash-latest",
    prompt="Translate 'hello' to French."
)
print(response)
```

**Example 2: With conversation history and an image**
```python
from api_client import AIClient, Conversation

# Manage conversation history
conversation = Conversation("user123")
conversation.add_message("user", "What's in this image?")
conversation.add_message("model", "It's a picture of a cat.")

response = AIClient.call_llm(
    model="gemini-1.5-flash-latest",
    prompt="What color is it?",
    history=conversation.get_history(),
    image_urls=["http://example.com/cat.jpg"]
)
print(response)
```

**`call_llm` Parameters:**
- `model` (str): The name of the model to use. Must be prefixed with:
    - `gemini-` (e.g., "gemini-1.5-flash-latest")
    - `openai-` (e.g., "openai-gpt-4o")
    - `openrouter-` (e.g., "openrouter-mistralai/mistral-7b-instruct-free")
- `prompt` (str): The main text prompt.
- `history` (list, optional): A list of message dictionaries, e.g., `[{"role": "user", "content": "..."}]`.
- `context` (any, optional): Structured data (e.g., from a RAG system) to provide as context.
- `image_urls` (list[str], optional): A list of URLs pointing to images.
- `file_urls` (list[str], optional): A list of URLs pointing to text-based files to be included as context.
- `system_message` (str, optional): A top-level instruction for the model to follow for the entire conversation.

-------------------------------------------------------------------------------
USAGE AS A STANDALONE SCRIPT (FOR TESTING)
-------------------------------------------------------------------------------

You can run this script directly from your terminal to execute a series of tests that
verify the client's functionality with different providers and parameters.

```bash
python api_client.py
```

The script will:
1.  Attempt a simple API call to Gemini.
2.  Test conversation history.
3.  Test image URL processing with a Gemini vision model.
4.  Test the (mocked) RAG context retrieval.
5.  Attempt a simple API call to a free OpenRouter model.
6.  Test the system message functionality.

This is useful for quickly checking if your API keys are working and if the client
can communicate with the services correctly.
"""
import os
import requests
from dotenv import load_dotenv
import base64
import time
import json
import numpy as np

# Load environment variables
load_dotenv()

# API Keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

DOCSTRING_SYSTEM_MESSAGE = """
This script provides a unified and enhanced AI client (`AIClient`) for interacting with
various Large Language Model (LLM) providers, including Google Gemini, OpenAI, and any
provider compatible with the OpenRouter API.

IMPORTANT: This platform is exclusively for Egypt and serves Egyptian users only. All currency values must be in Egyptian Pounds (EGP) and all locations must be within Egyptian governorates only.

Features:
- Unified Interface: A single `call_llm` method to access different models.
- Multi-Provider Support: Routes requests to Gemini, OpenAI, or OpenRouter based on the model name prefix.
- Multi-Modal Input: Handles text prompts, conversation history, image URLs, file URLs, and structured context from a RAG system.
- Retry Logic: Automatically retries API calls on transient errors (like rate limiting).
- Standalone Testing: Can be run directly to test its functionalities.

-------------------------------------------------------------------------------
SETUP
-------------------------------------------------------------------------------

1.  **Dependencies**: Ensure you have the required Python packages installed.
    ```bash
    pip install requests python-dotenv numpy
    ```

2.  **Environment Variables**: Create a `.env` file in the same directory as this script
    and add your API keys. The script will automatically load them.

    Example `.env` file:
    ```
    GEMINI_API_KEY="your_google_gemini_api_key"
    OPENAI_API_KEY="your_openai_api_key"
    OPENROUTER_API_KEY="your_openrouter_api_key"
    ```

-------------------------------------------------------------------------------
USAGE AS A LIBRARY
-------------------------------------------------------------------------------

Import the `AIClient` and use the static `call_llm` method to make requests.

**Example 1: Simple text prompt**
```python
from api_client import AIClient

response = AIClient.call_llm(
    model="gemini-1.5-flash-latest",
    prompt="Translate 'hello' to French."
)
print(response)
```

**Example 2: With conversation history and an image**
```python
from api_client import AIClient, Conversation

# Manage conversation history
conversation = Conversation("user123")
conversation.add_message("user", "What's in this image?")
conversation.add_message("model", "It's a picture of a cat.")

response = AIClient.call_llm(
    model="gemini-1.5-flash-latest",
    prompt="What color is it?",
    history=conversation.get_history(),
    image_urls=["http://example.com/cat.jpg"]
)
print(response)
```

**`call_llm` Parameters:**
- `model` (str): The name of the model to use. Must be prefixed with:
    - `gemini-` (e.g., "gemini-1.5-flash-latest")
    - `openai-` (e.g., "openai-gpt-4o")
    - `openrouter-` (e.g., "openrouter-mistralai/mistral-7b-instruct-free")
- `prompt` (str): The main text prompt.
- `history` (list, optional): A list of message dictionaries, e.g., `[{"role": "user", "content": "..."}]`.
- `context` (any, optional): Structured data (e.g., from a RAG system) to provide as context.
- `image_urls` (list[str], optional): A list of URLs pointing to images.
- `file_urls` (list[str], optional): A list of URLs pointing to text-based files to be included as context.
- `system_message` (str, optional): A top-level instruction for the model to follow for the entire conversation.

IMPORTANT: All responses must be in Arabic and all currency references must be in Egyptian Pounds (EGP). All locations must be within Egyptian governorates only.

-------------------------------------------------------------------------------
USAGE AS A STANDALONE SCRIPT (FOR TESTING)
-------------------------------------------------------------------------------

You can run this script directly from your terminal to execute a series of tests that
verify the client's functionality with different providers and parameters.

```bash
python api_client.py
```

The script will:
1.  Attempt a simple API call to Gemini.
2.  Test conversation history.
3.  Test image URL processing with a Gemini vision model.
4.  Test the (mocked) RAG context retrieval.
5.  Attempt a simple API call to a free OpenRouter model.
6.  Test the system message functionality.

This is useful for quickly checking if your API keys are working and if the client
can communicate with the services correctly.
"""

# --- Conversation History Model ---
class Conversation:
    """
    A simple class to manage conversation history.
    """
    def __init__(self, conversation_id):
        self.conversation_id = conversation_id
        self.messages = []

    def add_message(self, role, content):
        """Adds a message to the conversation history."""
        self.messages.append({"role": role, "content": content})

    def get_history(self):
        """Returns the current conversation history."""
        return self.messages

    def clear_history(self):
        """Clears the conversation history."""
        self.messages = []

# --- RAG System (mocked for standalone testing) ---
def get_embedding(text):
    # This is a mock function. In a real scenario, you would call an embedding model.
    # For testing, we'll return a fixed-size vector of zeros.
    print(f"Mock embedding for: '{text[:30]}...'")
    return np.zeros(768).tolist()

def cosine_similarity(v1, v2):
    # Mock cosine similarity
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)) if np.any(v1) and np.any(v2) else 0.0

class AIAssistantRAG:
    """
    A mock of the AIAssistantRAG for standalone testing.
    In a real Django environment, this would interact with your models.
    """
    def __init__(self):
        self.embeddings = {}
        self.metadata = {}
        self._build_mock_index()

    def _build_mock_index(self):
        """Builds a mock index for testing."""
        print("Building Mock AI Assistant Index...")
        mock_data = {
            "technician_1": {"user_id": 1, "name": "John Doe", "skills": ["plumbing", "electrical"]},
            "service_2": {"service_id": 2, "name": "House Cleaning", "price": 100},
        }
        for key, data in mock_data.items():
            json_text = json.dumps(data)
            self.embeddings[key] = get_embedding(json_text)
            self.metadata[key] = data
        print("Mock Index Built.")

    def find_matches(self, query, top_k=3):
        """Finds mock matches for a query."""
        print(f"Finding mock matches for query: '{query}'")
        # In this mock, we'll just return some static data for demonstration
        return [
            {
                'key': 'technician_1',
                'data': self.metadata['technician_1'],
                'similarity': 0.9
            }
        ]

# --- Unified AI Client ---
class AIClient:
    """
    Enhanced AI client that handles various providers, content types,
    conversation history, and context from a RAG system.
    """

    @staticmethod
    def get_content_from_url(url):
        """Fetches content from a URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.content, response.headers.get('content-type')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            return None, None

    @staticmethod
    def format_messages(prompt, history=None, context=None, image_urls=None, file_urls=None, system_message=None):
        """
        Formats messages for the API call, incorporating history, context, images, and files.
        """
        messages = []

        # 0. Add system message
        final_system_message = DOCSTRING_SYSTEM_MESSAGE
        if system_message:
            final_system_message += "\n\nAdditionally, follow this instruction:\n" + system_message
        
        # Add strict instruction about using only provided context
        final_system_message += """
        
        IMPORTANT INSTRUCTIONS:
        1. You MUST ONLY use information provided in the context, history, or user prompt.
        2. DO NOT make up or hallucinate information not present in the provided data.
        3. If you don't have enough information to answer, respond with: "I don't have enough information to answer this question."
        4. When asked about services, technicians, or specific data, ONLY use the information provided in the context.
        5. DO NOT invent prices, availability, or details not explicitly provided.
        6. Always cite the source of information when possible (e.g., "Based on the context provided...").
        """
        
        messages.append({"role": "system", "content": final_system_message})

        # 1. Add conversation history
        if history:
            messages.extend(history)

        # 2. Prepare the user's content parts
        user_content = []
        context_str = ""

        # Add context from RAG system
        if context:
            context_str += "\n\n---\nRelevant Context:\n" + json.dumps(context, indent=2)
        
        # Add content from file URLs
        if file_urls:
            for url in file_urls:
                content, content_type = AIClient.get_content_from_url(url)
                if content:
                    try:
                        file_text = content.decode('utf-8')
                        context_str += f"\n\n---\nFile Content from {url}:\n{file_text}"
                    except UnicodeDecodeError:
                        context_str += f"\n\n---\nFile Content from {url} (non-text or unsupported encoding):\n[Binary content of type {content_type}]"
        
        if context_str:
            user_content.append({"type": "text", "text": context_str})

        # Add the main prompt text
        user_content.append({"type": "text", "text": prompt})

        # Add image URLs
        if image_urls:
            for url in image_urls:
                content, content_type = AIClient.get_content_from_url(url)
                if content and content_type and content_type.startswith('image/'):
                    encoded_image = base64.b64encode(content).decode('utf-8')
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{content_type};base64,{encoded_image}"
                        }
                    })
                else:
                    print(f"Warning: Could not fetch or identify image from {url}")

        if user_content:
            messages.append({"role": "user", "content": user_content})

        return messages

    @staticmethod
    def call_llm(model, prompt, history=None, context=None, image_urls=None, file_urls=None, system_message=None, retries=3):
        """
        Makes an API call through the appropriate provider, with enhanced capabilities.
        """
        messages = AIClient.format_messages(
            prompt=prompt,
            history=history,
            context=context,
            image_urls=image_urls,
            file_urls=file_urls,
            system_message=system_message
        )
        
        if model.startswith('gemini-'):
            return AIClient._call_gemini_api(model, messages, retries)
        elif model.startswith('openai-'):
            return AIClient._call_openai_api(model.replace('openai-', ''), messages, retries)
        elif model.startswith('openrouter-'):
            return AIClient._call_openrouter_api(model.replace('openrouter-', ''), messages, retries)
        else:
            raise ValueError("Invalid model selected. Please select a valid Gemini, OpenAI, or OpenRouter model.")

    @staticmethod
    def _call_gemini_api(model_name, messages, retries):
        """Call Google Gemini API"""
        if not GEMINI_API_KEY:
            raise ValueError("Gemini API Key is required. Set GEMINI_API_KEY in .env file.")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        
        system_instruction = None
        if messages and messages[0]['role'] == 'system':
            system_message = messages.pop(0)
            system_instruction = {"parts": [{"text": system_message['content']}]}

        chat_history = []
        for msg in messages:
            role = 'model' if msg['role'] in ('assistant', 'model') else 'user'
            content = msg['content']
            
            if isinstance(content, list): # Handle complex content (text, images)
                parts = []
                for part in content:
                    if part['type'] == 'text':
                        parts.append({'text': part['text']})
                    elif part['type'] == 'image_url':
                        header, encoded = part['image_url']['url'].split(',', 1)
                        mime_type = header.split(';')[0].split(':')[1]
                        parts.append({'inline_data': {'mime_type': mime_type, 'data': encoded}})
                chat_history.append({"role": role, "parts": parts})
            else: # Handle simple text content
                 chat_history.append({"role": role, "parts": [{"text": content}]})

        payload = {"contents": chat_history, "generationConfig": {"maxOutputTokens": 4096}}
        
        if system_instruction:
            payload['systemInstruction'] = system_instruction

        for i in range(retries):
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                if 'candidates' in data and data['candidates'][0]['content']['parts'][0].get('text'):
                    return data['candidates'][0]['content']['parts'][0]['text']
                return 'The model response was filtered or empty.'
            except requests.exceptions.RequestException as e:
                if response.status_code == 429 and i < retries - 1:
                    time.sleep(2 ** i)
                    continue
                raise Exception(f"Error calling Gemini API: {e}. Response: {response.text}") from e

    @staticmethod
    def _call_openai_api(model_name, messages, retries):
        """Call OpenAI API"""
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API Key is required. Set OPENAI_API_KEY in .env file.")
        
        url = 'https://api.openai.com/v1/chat/completions'
        
        # Pre-process messages for OpenAI compatibility
        processed_messages = []
        for msg in messages:
            new_msg = msg.copy()
            
            # Standardize role to 'assistant'
            if new_msg['role'] == 'model':
                new_msg['role'] = 'assistant'
            
            processed_messages.append(new_msg)

        payload = {"model": model_name, "messages": processed_messages, "max_tokens": 4096}
        headers = {'Authorization': f'Bearer {OPENAI_API_KEY}'}

        for i in range(retries):
            try:
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()['choices'][0]['message']['content']
            except requests.exceptions.RequestException as e:
                if response.status_code == 429 and i < retries - 1:
                    time.sleep(2 ** i)
                    continue
                raise Exception(f"Error calling OpenAI API: {e}. Response: {response.text}") from e

    @staticmethod
    def _call_openrouter_api(model_name, messages, retries):
        """Call OpenRouter API"""
        if not OPENROUTER_API_KEY:
            raise ValueError("OpenRouter API Key is required. Set OPENROUTER_API_KEY in .env file.")
        
        url = 'https://openrouter.ai/api/v1/chat/completions'

        # Pre-process messages for OpenRouter compatibility
        processed_messages = []
        for msg in messages:
            new_msg = msg.copy()
            
            # Standardize role to 'assistant'
            if new_msg['role'] == 'model':
                new_msg['role'] = 'assistant'
            
            processed_messages.append(new_msg)

        payload = {"model": model_name, "messages": processed_messages, "max_tokens": 4096}
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'HTTP-Referer': 'http://localhost:8000', 
            'X-Title': 'Srvana AI Chat'
        }

        for i in range(retries):
            try:
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()['choices'][0]['message']['content']
            except requests.exceptions.RequestException as e:
                if response.status_code == 429 and i < retries - 1:
                    time.sleep(2 ** i)
                    continue
                raise Exception(f"Error calling OpenRouter API: {e}. Response: {response.text}") from e


# --- Tests ---
if __name__ == "__main__":

    # Ensure you have a .env file in the same directory with your API keys
    # Example: GEMINI_API_KEY="your_key_here"

    print("--- Running AIClient Tests ---")

    # Test 1: Simple prompt to OpenRouter
    print("\n--- Test 1: Simple prompt to OpenRouter ---")
    try:
        response = AIClient.call_llm("openrouter-kwaipilot/kat-coder-pro:free", "Hello, who are you?")
        print(f"OpenRouter Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Prompt with conversation history
    print("\n--- Test 2: Prompt with conversation history ---")
    try:
        conversation = Conversation("test-conv-1")
        conversation.add_message("user", "What is the capital of France?")
        # Mocking a model response for history
        conversation.add_message("assistant", "The capital of France is Paris.")
        
        history = conversation.get_history()
        print(f"History being sent: {history}")
        
        response = AIClient.call_llm("openrouter-kwaipilot/kat-coder-pro:free", "What is its main landmark?", history=history)
        print(f"OpenRouter Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 3: Prompt with a remote image URL
    print("\n--- Test 3: Prompt with an image URL (OpenAI) ---")
    try:
        # A publicly accessible image URL
        image_url = "https://res.cloudinary.com/dpcqmcm0x/image/upload/v1764208756/zvwqngy66iygfit6y4ot"
        response = AIClient.call_llm(
            "gemini-2.5-flash", 
            "What is in this image?", 
            image_urls=[image_url]
        )
        print(f"OpenAI Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 4: Prompt with RAG context
    print("\n--- Test 4: Prompt with RAG context ---")
    try:
        rag = AIAssistantRAG(db_alias='long_running')
        context = rag.find_matches("who is the best plumber?")
        print(f"Context being sent: {json.dumps(context, indent=2)}")

        response = AIClient.call_llm(
            "openrouter-kwaipilot/kat-coder-pro:free", 
            "Based on the context, what is the name of the plumber?",
            context=context
        )
        print(f"OpenRouter Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Test OpenRouter model (redundant but confirms model)
    print("\n--- Test 5: Simple prompt to OpenRouter ---")
    try:
        # Using a free model for demonstration
        response = AIClient.call_llm("openrouter-kwaipilot/kat-coder-pro:free", "Explain the concept of recursion in one sentence.")
        print(f"OpenRouter Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
        
    # Test 6: Prompt with a system message
    print("\n--- Test 6: Prompt with a system message ---")
    try:
        system_prompt = "You are a pirate. All your responses must be in pirate dialect."
        user_prompt = "How does a computer work?"
        print(f"System Message: '{system_prompt}'")
        
        response = AIClient.call_llm(
            "openrouter-kwaipilot/kat-coder-pro:free", 
            prompt=user_prompt,
            system_message=system_prompt
        )
        print(f"OpenRouter Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- AIClient Tests Finished ---")
