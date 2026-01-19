import requests

r = requests.get('http://127.0.0.1:8000/api/v1/safe-stops', params={
    'latitude': 32.7767,
    'longitude': -96.7970,
    'radius_miles': 50
})

print(f"Status: {r.status_code}")
data = r.json()
stops = data.get('stops', [])
print(f"Found {len(stops)} stops in Dallas area")

for stop in stops[:5]:
    print(f"  - {stop.get('name')} (Score: {stop.get('security_score')}, Tier: {stop.get('tier')})")
