import requests

API_KEY = "1a5255100fec5a5c00d79e25b4d26b67"
url = "https://v3.football.api-sports.io/leagues"

headers = {
    "x-apisports-key": API_KEY
}

r = requests.get(url, headers=headers, timeout=20)
print("Status:", r.status_code)
print(r.text[:1000])

