"""
XORAS Systems LLC — Real-Time SerpAPI Integration Module
Provides structured JSON web search across Google, Bing, Baidu, Yandex, Google Scholar, and Google News.
"""

import json
import os
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional

class XORASSerpAPIClient:
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            self.api_key = api_key
        else:
            # Fallback to system environment config
            self.api_key = os.environ.get("SERPAPI_API_KEY", "e9978d7e19db5418e9a11815286be53af5a0a69675b1160c306c2636b667387e")

    def search(self, query: str, engine: str = "google", **kwargs) -> Dict[str, Any]:
        """Executes a structured search query via SerpAPI."""
        params = {
            "engine": engine,
            "q": query,
            "api_key": self.api_key
        }
        params.update(kwargs)
        
        encoded_url = f"https://serpapi.com/search.json?{urllib.parse.urlencode(params)}"
        req = urllib.request.urlopen(encoded_url)
        return json.loads(req.read().decode("utf-8"))

    def search_news(self, query: str) -> List[Dict[str, Any]]:
        """Searches live breaking news stories via Google News engine."""
        data = self.search(query, engine="google_news")
        return data.get("news_results", [])

    def search_scholar(self, query: str) -> List[Dict[str, Any]]:
        """Searches scientific whitepapers and academic literature via Google Scholar."""
        data = self.search(query, engine="google_scholar")
        return data.get("organic_results", [])

if __name__ == "__main__":
    client = XORASSerpAPIClient()
    res = client.search("XORAS agent framework 2026")
    print("SerpAPI Test Results Found:", len(res.get("organic_results", [])))
