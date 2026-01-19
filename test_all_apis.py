"""
Test all external APIs
"""

import requests

print("=" * 50)
print("TESTING ALL EXTERNAL APIs")
print("=" * 50)

# Test 1: Google Geocoding
print("\n1. Google Geocoding API")
try:
    r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params={
        'address': 'Dallas, TX',
        'key': 'AIzaSyCJlOD5zLaZkKYFdiUtU3-QfPBLVTrBQlo'
    })
    if r.status_code == 200 and r.json().get('status') == 'OK':
        loc = r.json()['results'][0]['geometry']['location']
        print(f"   ✅ OK - Dallas at lat={loc['lat']}, lng={loc['lng']}")
    else:
        print(f"   ❌ FAILED - {r.json().get('status')}")
except Exception as e:
    print(f"   ❌ ERROR - {e}")

# Test 2: Google Places
print("\n2. Google Places API (New)")
try:
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": "AIzaSyCJlOD5zLaZkKYFdiUtU3-QfPBLVTrBQlo",
        "X-Goog-FieldMask": "places.displayName"
    }
    data = {
        "includedTypes": ["gas_station"],
        "maxResultCount": 3,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": 32.7767, "longitude": -96.7970},
                "radius": 10000.0
            }
        }
    }
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 200:
        places = r.json().get('places', [])
        print(f"   ✅ OK - Found {len(places)} places")
    else:
        print(f"   ❌ FAILED - {r.status_code}")
except Exception as e:
    print(f"   ❌ ERROR - {e}")

# Test 3: Google Routes
print("\n3. Google Routes API")
try:
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": "AIzaSyCJlOD5zLaZkKYFdiUtU3-QfPBLVTrBQlo",
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters"
    }
    data = {
        "origin": {"address": "Dallas, TX"},
        "destination": {"address": "Memphis, TN"},
        "travelMode": "DRIVE"
    }
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 200:
        routes = r.json().get('routes', [])
        if routes:
            dist = routes[0].get('distanceMeters', 0) / 1609.34
            print(f"   ✅ OK - Dallas to Memphis: {dist:.1f} miles")
    else:
        print(f"   ❌ FAILED - {r.status_code}")
except Exception as e:
    print(f"   ❌ ERROR - {e}")

# Test 4: Azure OpenAI
print("\n4. Azure OpenAI API (gpt-4o-mini)")
try:
    url = "https://snigd-mkey0c72-eastus2.cognitiveservices.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2025-01-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": "7rYSvNAvEaWYW3dflM2PsNtNGLqAQhskWO6ycWbhcNgm4alx3YqeJQQJ99CAACHYHv6XJ3w3AAAAACOGGOjv"
    }
    data = {
        "messages": [{"role": "user", "content": "Say hello SafeTravels in 5 words"}],
        "max_tokens": 50
    }
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 200:
        response = r.json()["choices"][0]["message"]["content"]
        print(f"   ✅ OK - Response: {response}")
    else:
        print(f"   ❌ FAILED - {r.status_code}: {r.text[:100]}")
except Exception as e:
    print(f"   ❌ ERROR - {e}")

# Test 5: Open-Meteo Weather
print("\n5. Open-Meteo Weather API")
try:
    r = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": 32.7767,
        "longitude": -96.7970,
        "current_weather": "true"
    })
    if r.status_code == 200:
        weather = r.json().get("current_weather", {})
        print(f"   ✅ OK - Dallas: {weather.get('temperature')}°C, wind {weather.get('windspeed')} km/h")
    else:
        print(f"   ❌ FAILED - {r.status_code}")
except Exception as e:
    print(f"   ❌ ERROR - {e}")

print("\n" + "=" * 50)
print("API TEST COMPLETE")
print("=" * 50)
