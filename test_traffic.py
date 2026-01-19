import requests

GOOGLE_API_KEY = 'AIzaSyCJlOD5zLaZkKYFdiUtU3-QfPBLVTrBQlo'
url = 'https://routes.googleapis.com/directions/v2:computeRoutes'

headers = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': GOOGLE_API_KEY,
    'X-Goog-FieldMask': 'routes.duration,routes.staticDuration,routes.distanceMeters'
}

data = {
    'origin': {'address': 'Dallas, TX'},
    'destination': {'address': 'Memphis, TN'},
    'travelMode': 'DRIVE',
    'routingPreference': 'TRAFFIC_AWARE'
}

r = requests.post(url, headers=headers, json=data, timeout=10)
print("API Status:", r.status_code)
print("\nFull Response:")
print(r.json())

if r.status_code == 200:
    route = r.json().get('routes', [{}])[0]
    duration = int(route.get('duration', '0s').replace('s', ''))
    static = int(route.get('staticDuration', '0s').replace('s', ''))
    delay = duration - static
    
    print("\n=== TRAFFIC ANALYSIS ===")
    print(f"Static Duration (no traffic): {static//3600}h {(static%3600)//60}m")
    print(f"Real-Time Duration (with traffic): {duration//3600}h {(duration%3600)//60}m")
    print(f"Traffic Delay: +{delay//60} minutes")
