import requests

API_KEY = "1a5255100fec5a5c00d79e25b4d26b67"

url = "https://v3.football.api-sports.io/teams"
headers = {"x-apisports-key": API_KEY}
params = {
    "league": 39,   # Premier League
    "season": 2024
}

r = requests.get(url, headers=headers, params=params)
data = r.json()

for team in data["response"]:
    print(team["team"]["id"], "-", team["team"]["name"])
