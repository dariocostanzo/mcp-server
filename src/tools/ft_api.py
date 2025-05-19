import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

FT_API_KEY = os.getenv("FT_API_KEY")
FT_API_URL = "https://api.ft.com/content/search/v1"

class FinancialTimesAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key or FT_API_KEY
        # We'll still keep the API key for content search if available
        # But we won't require it for shareholder information
    
    def search_plc(self, company_name, max_results=5):
        """
        Search for articles about a specific PLC (Public Limited Company)
        """
        # If we don't have an API key, use mock data instead
        if not self.api_key:
            return self._get_mock_articles(company_name, max_results)
            
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
        # If we don't have an API key, use mock data instead
        if not self.api_key:
            return self._get_mock_article_content(article_id)
            
        url = f"https://api.ft.com/content/{article_id}"
        headers = {"X-Api-Key": self.api_key}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API request failed with status code {response.status_code}", "details": response.text}
    
    def get_shareholders(self, ticker="BARC:LSE"):
        """
        Get major shareholders for a company using Financial Times API.
        
        Args:
            ticker (str): The ticker symbol in format SYMBOL:EXCHANGE (default: "BARC:LSE" for Barclays PLC)
        
        Returns:
            list: List of dictionaries containing shareholder information
        """
        print(f"Fetching shareholders data for {ticker}...")
        
        # The URL for the shareholders data endpoint
        url = "https://markets.ft.com/research/webservices/securities/v1/holders"
        
        # Parameters for the request
        params = {
            "symbols": ticker,
            "source": "befd8ca75ac4a20e"  # API source key
        }
        
        # Set headers to mimic a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
            "Referer": f"https://markets.ft.com/data/equities/tearsheet/profile?s={ticker}"
        }
        
        # Make the request
        response = requests.get(url, params=params, headers=headers)
        
        # Check if the request was successful
        if response.status_code != 200:
            print(f"Error: API request failed with status code {response.status_code}")
            return []
        
        # Parse the JSON response
        data = response.json()
        
        # Extract the shareholders information
        shareholders = []
        
        # Navigate through the response structure
        if "data" in data and "items" in data["data"] and data["data"]["items"]:
            item = data["data"]["items"][0]  # Get the first item
            
            # Check for institutional holders
            if "institutionalHolders" in item:
                holders_data = item["institutionalHolders"]
                
                # Process each holder
                for holder in holders_data:
                    name = holder.get("name", "").strip()
                    shares = holder.get("sharesHeld", "")
                    stake = holder.get("percentageHeld", "")
                    
                    # Format numbers nicely
                    if isinstance(shares, (int, float)):
                        shares = f"{shares:,}"
                    if isinstance(stake, (int, float)):
                        stake = f"{stake:.2f}%"
                    
                    # Only include if it has a name
                    if name:
                        shareholders.append({
                            "name": name,
                            "shares": shares,
                            "stake": stake
                        })
            
            # Check for major holders as fallback
            elif "majorHolders" in item:
                holders_data = item["majorHolders"]
                
                # Process each holder
                for holder in holders_data:
                    name = holder.get("name", "").strip()
                    shares = holder.get("sharesHeld", "")
                    stake = holder.get("percentageHeld", "")
                    
                    # Format numbers nicely
                    if isinstance(shares, (int, float)):
                        shares = f"{shares:,}"
                    if isinstance(stake, (int, float)):
                        stake = f"{stake:.2f}%"
                    
                    # Only include if it has a name
                    if name:
                        shareholders.append({
                            "name": name,
                            "shares": shares,
                            "stake": stake
                        })
        
        return shareholders
    
    def _get_mock_articles(self, company_name, max_results=5):
        """Generate mock article data for a company"""
        company_key = company_name.lower().split()[0]
        
        mock_data = {
            "apple": [
                {"id": "apple-001", "title": {"title": "Apple Reports Record Quarterly Revenue"}, "summary": {"excerpt": "Apple Inc. announced financial results for its fiscal 2023 fourth quarter ended September 30, 2023, with record revenue."}, "lifecycle": {"initialPublishDateTime": "2023-11-02T18:30:00Z"}},
                {"id": "apple-002", "title": {"title": "Apple Unveils New iPhone 15 with Advanced AI Features"}, "summary": {"excerpt": "Apple's latest iPhone comes with groundbreaking AI capabilities and improved battery life."}, "lifecycle": {"initialPublishDateTime": "2023-09-12T17:00:00Z"}}
            ],
            "microsoft": [
                {"id": "msft-001", "title": {"title": "Microsoft Cloud Business Drives Strong Quarterly Results"}, "summary": {"excerpt": "Azure cloud services continue to be a major growth driver for Microsoft Corporation."}, "lifecycle": {"initialPublishDateTime": "2023-10-24T21:15:00Z"}},
                {"id": "msft-002", "title": {"title": "Microsoft Expands AI Capabilities in Office Suite"}, "summary": {"excerpt": "New AI features in Microsoft 365 aim to boost productivity and creativity for users."}, "lifecycle": {"initialPublishDateTime": "2023-09-21T16:30:00Z"}}
            ]
        }
        
        # Get company data or use generic data if not found
        articles = mock_data.get(company_key, [
            {"id": "generic-001", "title": {"title": f"{company_name} Reports Quarterly Earnings"}, "summary": {"excerpt": f"{company_name} announced its financial results for the most recent fiscal quarter."}, "lifecycle": {"initialPublishDateTime": "2023-10-15T14:30:00Z"}},
            {"id": "generic-002", "title": {"title": f"{company_name} Announces New Product Line"}, "summary": {"excerpt": f"A new range of products was unveiled at {company_name}'s annual showcase event."}, "lifecycle": {"initialPublishDateTime": "2023-09-22T16:45:00Z"}}
        ])
        
        # Limit to max_results
        limited_articles = articles[:max_results]
        
        return {"results": limited_articles}
    
    def _get_mock_article_content(self, article_id):
        """Generate mock article content for an article ID"""
        return {
            "id": article_id,
            "title": "Mock Article Title",
            "bodyXML": "<body><p>This is a mock article content generated for demonstration purposes.</p><p>In a real implementation, this would contain the actual article content from the Financial Times API.</p></body>",
            "publishedDate": "2023-11-15T10:30:00Z"
        }