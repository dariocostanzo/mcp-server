import os
import requests
from dotenv import load_dotenv

load_dotenv()

FT_API_KEY = os.getenv("FT_API_KEY")
FT_API_URL = "https://api.ft.com/content/search/v1"

class FinancialTimesAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key or FT_API_KEY
        if not self.api_key:
            raise ValueError("Financial Times API key is required")
    
    def search_plc(self, company_name, max_results=5):
        """
        Search for articles about a specific PLC (Public Limited Company)
        """
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Create a query to search for articles about the company
        query = {
            "queryString": f"{company_name} AND PLC",
            "queryContext": {
                "curations": ["ARTICLES"]
            },
            "resultContext": {
                "maxResults": max_results,
                "aspects": ["title", "summary", "lifecycle", "location", "metadata"]
            }
        }
        
        response = requests.post(FT_API_URL, headers=headers, json=query)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API request failed with status code {response.status_code}", "details": response.text}
    
    def get_article_content(self, article_id):
        """
        Get the full content of an article by its ID
        """
        url = f"https://api.ft.com/content/{article_id}"
        headers = {"X-Api-Key": self.api_key}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API request failed with status code {response.status_code}", "details": response.text}