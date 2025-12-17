import os
import requests
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# API Keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class AIClient:
    """Unified AI client for handling different AI provider APIs"""
    
    @staticmethod
    def call_api(model, messages, retries=3):
        """
        Unified API caller that routes to appropriate AI provider
        """
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
        api_key = GEMINI_API_KEY
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        if not api_key:
            raise ValueError("Gemini API Key is required. Please set GEMINI_API_KEY in the .env file.")

        # Prepare chat history for context (maps 'assistant' role to Gemini's 'model' role)
        chat_history = []

        for msg in messages:
            role = 'user' if msg['role'] == 'user' else 'model'
            chat_history.append({"role": role, "parts": [{"text": msg['content']}]})
        
        payload = {
            "contents": chat_history,
            "generationConfig": {
                "maxOutputTokens": 2048,
            }
        }

        for i in range(retries):
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
                data = response.json()
                generated_text = data.get('candidates')[0].get('content').get('parts')[0].get('text')
                if generated_text:
                    return generated_text
                else:
                    print("Gemini API returned no text content. Candidates:", data.get('candidates'))
                    return 'The model response was filtered or empty.'
            except requests.exceptions.RequestException as e:
                if response.status_code == 429 and i < retries - 1:
                    time.sleep(2 ** i)
                    continue
                raise Exception(f"Error calling Gemini API: {e}. Response: {response.text}")
            except Exception as e:
                raise Exception(f"Error processing Gemini API response: {e}")

    @staticmethod
    def _call_openai_api(model_name, messages, retries):
        """Call OpenAI API"""
        api_key = OPENAI_API_KEY
        url = 'https://api.openai.com/v1/chat/completions'

        if not api_key:
            raise ValueError("OpenAI API Key is required. Please set OPENAI_API_KEY in the .env file.")

        chat_history = []
        for msg in messages:
            role = 'user' if msg['role'] == 'user' else 'assistant'
            chat_history.append({"role": role, "content": msg['content']})
        
        payload = {
            "model": model_name,
            "messages": chat_history,
            "max_tokens": 2048,
        }

        for i in range(retries):
            try:
                response = requests.post(
                    url, 
                    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'},
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                generated_text = data.get('choices')[0].get('message').get('content')
                if generated_text:
                    return generated_text
                else:
                    print("OpenAI returned no text content. Choices:", data.get('choices'))
                    return 'The OpenAI model response was filtered or empty.'
            except requests.exceptions.RequestException as e:
                if response.status_code == 429 and i < retries - 1:
                    time.sleep(2 ** i)
                    continue
                raise Exception(f"Error calling OpenAI API: {e}. Response: {response.text}")
            except Exception as e:
                raise Exception(f"Error processing OpenAI API response: {e}")

    @staticmethod
    def _call_openrouter_api(model_name, messages, retries):
        """Call OpenRouter API"""
        api_key = OPENROUTER_API_KEY
        url = 'https://openrouter.ai/api/v1/chat/completions'

        if not api_key:
            raise ValueError("OpenRouter API Key is required. Please set OPENROUTER_API_KEY in the .env file.")

        chat_history = []
        for msg in messages:
            role = 'user' if msg['role'] == 'user' else 'assistant'
            chat_history.append({"role": role, "content": msg['content']})

        payload = {
            "model": model_name,
            "messages": chat_history,
            "max_tokens": 2048,
        }

        for i in range(retries):
            try:
                response = requests.post(
                    url,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {api_key}',
                        'HTTP-Referer': 'http://localhost:8000', # Placeholder, adjust if needed
                        'X-Title': 'Srvana AI Chat'  # Placeholder
                    },
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                generated_text = data.get('choices')[0].get('message').get('content')

                if generated_text:
                    return generated_text
                else:
                    print("OpenRouter returned no text content. Choices:", data.get('choices'))
                    return 'The OpenRouter model response was filtered or empty.'

            except requests.exceptions.RequestException as e:
                if response.status_code == 429 and i < retries - 1:
                    time.sleep(2 ** i)
                    continue
                elif response.status_code == 401:
                    # Handle unauthorized error specifically for OpenRouter
                    error_detail = ""
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('error', {}).get('message', '')
                    except:
                        error_detail = response.text
                    raise Exception(f"OpenRouter API Unauthorized: {error_detail}. Please check your API key and permissions.")
                raise Exception(f"Error calling OpenRouter API: {e}. Response: {response.text}")
            except Exception as e:
                raise Exception(f"Error processing OpenRouter API response: {e}")
