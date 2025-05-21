import os
import requests
import ollama
import time
import subprocess
from dotenv import load_dotenv

load_dotenv()

# Get configuration from environment variables or use defaults
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")  # Using Mistral model


class OllamaClient:
    """Client for interacting with Ollama API"""

    def __init__(self, model=OLLAMA_MODEL, host=OLLAMA_HOST):
        """Initialize the Ollama client with model and host"""
        self.model = model
        self.host = host
        self.ensure_ollama_running()

    def ensure_ollama_running(self):
        """Check if Ollama is running, attempt to start if not"""
        try:
            # Simple check to see if Ollama is responding
            response = requests.get(f"{self.host}/api/tags")
            if response.status_code == 200:
                print(f"Ollama is running with model: {self.model}")
                return
        except:
            print("Ollama server not running. Attempting to start...")
            try:
                # For Windows
                if os.name == 'nt':
                    subprocess.Popen(["ollama", "serve"],
                                     creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    # For macOS and Linux
                    subprocess.Popen(["ollama", "serve"])

                # Wait for server to start
                time.sleep(5)
                print("Ollama server started")
            except Exception as e:
                print(f"Failed to start Ollama server: {e}")
                print("Please start Ollama manually before continuing")

    def chat(self, messages, temperature=0.1):
        """
        Send a chat request to Ollama

        Args:
            messages (list): List of message objects with role and content
            temperature (float): Controls randomness in response generation (0.0-1.0)
                                Lower values = more deterministic responses

        Returns:
            dict: Response from Ollama
        """
        try:
            # Ensure Ollama is running
            self.ensure_ollama_running()

            # Prepare the request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,  # Add temperature parameter
                "stream": False
            }

            # Send the request to Ollama
            response = requests.post(
                f"{self.host}/api/chat",
                json=payload
            )

            # Check if the request was successful
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
