import os
import json
import ollama
from dotenv import load_dotenv
import subprocess
import time
import requests

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

class OllamaClient:
    def __init__(self, model=OLLAMA_MODEL, host=OLLAMA_HOST):
        self.model = model
        self.host = host
        self.ensure_ollama_running()
    
    def ensure_ollama_running(self):
        """Ensure Ollama is running, start it if not"""
        try:
            response = requests.get(f"{self.host}/api/tags")
            if response.status_code != 200:
                raise Exception("Ollama server not responding correctly")
        except:
            print("Ollama server not running. Attempting to start...")
            try:
                # For Windows
                subprocess.Popen(["ollama", "serve"], 
                                 creationflags=subprocess.CREATE_NEW_CONSOLE)
                # Wait for server to start
                time.sleep(5)
                print("Ollama server started")
            except Exception as e:
                print(f"Failed to start Ollama server: {e}")
                print("Please start Ollama manually before continuing")
    
    def generate(self, prompt, system="", stream=False):
        """Generate a response from Ollama"""
        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                system=system,
                stream=stream
            )
            return response
        except Exception as e:
            return {"error": str(e)}
    
    def chat(self, messages, stream=False):
        """Chat with Ollama"""
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                stream=stream
            )
            return response
        except Exception as e:
            return {"error": str(e)}