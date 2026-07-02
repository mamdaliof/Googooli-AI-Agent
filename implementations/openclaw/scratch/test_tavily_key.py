import requests

tavily_key = "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"
tavily_url = "https://api.tavily.com/search"
payload = {
    "api_key": tavily_key,
    "query": "farhad hoseyni",
    "search_depth": "smart",
    "include_answer": False
}

try:
    response = requests.post(tavily_url, json=payload, timeout=15.0)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
except Exception as e:
    print("Error:", e)
