# SafeTravels Data Sources

This document lists all data sources used in the SafeTravels project, with links to access them.

---

## 📊 Primary Data Sources

### 1. FBI Crime Data (UCR)
**What:** State and county-level crime statistics (property crime, motor vehicle theft, larceny, burglary)

| Field | Value |
|-------|-------|
| **Source** | FBI Uniform Crime Report (UCR) Program |
| **Website** | https://crime-data-explorer.fr.cloud.gov |
| **API Docs** | https://crime-data-api.fr.cloud.gov/swagger-ui/ |
| **API Key** | https://api.data.gov/signup/ (Free) |
| **Format** | JSON, CSV |
| **Coverage** | All 50 US states, counties |
| **Update Frequency** | Annual |

**Local File:** `data/fbi_crime_data.json`

---

### 2. DOT Truck Stop Parking (Jason's Law Survey)
**What:** Truck stop and rest area locations with GPS coordinates

| Field | Value |
|-------|-------|
| **Source** | US Department of Transportation / Bureau of Transportation Statistics |
| **Website** | https://data.gov/dataset/truck-stop-parking |
| **Direct Download** | https://geodata.bts.gov/datasets/usdot::truck-stop-parking |
| **ArcGIS API** | https://geo.dot.gov/server/rest/services/NTAD/Truck_Stop_Parking/MapServer |
| **Format** | JSON, GeoJSON, CSV, Shapefile |
| **Coverage** | All US states |
| **Fields** | State, Highway, Milepost, City, County, Latitude, Longitude, Parking Spots |

**Local File:** `data/dot_truck_stops.json`

---

### 3. OpenStreetMap (Overpass API)
**What:** Truck stops, fuel stations, amenities

| Field | Value |
|-------|-------|
| **Source** | OpenStreetMap Contributors |
| **Website** | https://www.openstreetmap.org |
| **API** | https://overpass-api.de/api/interpreter |
| **Query Tool** | https://overpass-turbo.eu |
| **Format** | JSON, XML |
| **Coverage** | Worldwide |
| **Tags** | `highway=services`, `amenity=fuel`, `hgv=yes` |

**Query Example:**
```
[out:json];
node["highway"="services"]({{bbox}});
out body;
```

---

### 4. NHTSA FARS (Fatality Analysis Reporting System)
**What:** Fatal crash data by location

| Field | Value |
|-------|-------|
| **Source** | National Highway Traffic Safety Administration |
| **Website** | https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars |
| **API Docs** | https://crashviewer.nhtsa.dot.gov/CrashAPI |
| **Format** | JSON, CSV, XML |
| **Coverage** | All US states (2010-present) |
| **Fields** | State, County, City, Latitude, Longitude, Date, Vehicle Type |

---

### 5. FMCSA Carrier Safety Data
**What:** Motor carrier safety records, inspections, crashes

| Field | Value |
|-------|-------|
| **Source** | Federal Motor Carrier Safety Administration |
| **Website** | https://safer.fmcsa.dot.gov |
| **API (QCMobile)** | https://mobile.fmcsa.dot.gov/qc/services/ |
| **Format** | JSON |
| **Coverage** | All registered US carriers |

---

## 📰 Secondary Data Sources (Reports/Analysis)

### 6. CargoNet (Theft Trends)
**What:** Cargo theft incident analysis and trends

| Field | Value |
|-------|-------|
| **Source** | Verisk CargoNet |
| **Website** | https://www.cargonet.com |
| **Reports** | https://www.cargonet.com/supply-chain-risk-trends/ |
| **Format** | PDF reports (free summaries) |
| **Note** | Full incident data requires paid subscription |

---

### 7. Overhaul Cargo Theft Reports
**What:** Quarterly cargo theft statistics

| Field | Value |
|-------|-------|
| **Source** | Overhaul |
| **Website** | https://over-haul.com |
| **Reports** | https://over-haul.com/resources/reports/ |
| **Format** | PDF (free download with email) |
| **Coverage** | US, Mexico, Canada |

---

### 8. NICB Vehicle Theft Reports
**What:** Vehicle theft hotspots and trends

| Field | Value |
|-------|-------|
| **Source** | National Insurance Crime Bureau |
| **Website** | https://www.nicb.org |
| **Reports** | https://www.nicb.org/news/news-releases |
| **Format** | PDF |

---

## 🗺️ Additional Location Data

### 9. POI Factory Rest Areas
**What:** Rest area locations with amenities

| Field | Value |
|-------|-------|
| **Source** | POI Factory (Community) |
| **Website** | https://www.poi-factory.com |
| **Download** | https://www.poi-factory.com/node/21138 |
| **Format** | CSV, GPX |
| **Records** | 3000+ locations |

---

---

## 📅 Internal / Static Data Sources

### 10. High Risk Corridors
**What:** Defined geolocation paths of known high-risk highway segments.
**File:** `data/high_risk_corridors.json`

### 11. HOS (Hours of Service) Regulations
**What:** Federal rules for driver driving limits and break requirements.
**File:** `data/hos_regulations.json`

### 12. US Holidays
**What:** Calendar of major holidays for temporal risk adjustment.
**File:** `data/us_holidays.json`

---

## 📋 Data Usage Summary

| Data Source | Status | Documents Created |
|-------------|--------|-------------------|
| FBI Crime Data | ✅ Loaded | 50 states, 25 counties, 3 analysis docs |
| DOT Truck Stops | ✅ Loaded | 40 truck stops with GPS + security |
| OpenStreetMap | ✅ Loaded | 2,500+ service locations (`osm_truck_stops.json`) |
| High Risk Corridors | ✅ Loaded | Major interstates (I-10, I-40, I-80) |
| NHTSA FARS | 🔄 Pending | - |
| FMCSA Carrier | 🔄 Pending | - |

---

## 🔑 API Keys Required

| Service | Key Required | How to Get |
|---------|--------------|------------|
| FBI Crime API | ✅ Yes | https://api.data.gov/signup/ |
| OpenStreetMap | ❌ No | Free, no key needed |
| NHTSA FARS | ❌ No | Free, no key needed |
| FMCSA QCMobile | ✅ Yes | https://mobile.fmcsa.dot.gov/qc/services/ |

---

*Last Updated: January 2026*
