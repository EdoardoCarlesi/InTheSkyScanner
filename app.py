import math
import os
from datetime import datetime, timedelta
import toml
import streamlit as st
import requests
from streamlit_folium import st_folium
import folium


@st.cache_data(ttl=86400)
def search_flights_cached(departure_iata, arrival_iata, outbound_date, return_date, _api_key):
    """Search flights using SerpApi Google Flights API with caching."""
    params = {
        "engine": "google_flights",
        "api_key": _api_key,
        "departure_id": departure_iata,
        "arrival_id": arrival_iata,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": "USD",
        "hl": "en"
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None


@st.cache_data(ttl=86400)
def search_flights_rapidapi(departure_iata, arrival_iata, outbound_date, return_date, _api_key):
    """Search flights using RapidAPI Kiwi.com API as fallback."""
    url = "https://kiwi-com-flight-search-v1.p.rapidapi.com/v2/flights"
    
    headers = {
        "X-RapidAPI-Key": _api_key,
        "X-RapidAPI-Host": "kiwi-com-flight-search-v1.p.rapidapi.com"
    }
    
    params = {
        "fly_from": departure_iata,
        "fly_to": arrival_iata,
        "date_from": outbound_date,
        "date_to": outbound_date,
        "return_from": return_date,
        "return_to": return_date,
        "curr": "EUR"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            flights = []
            if "data" in data:
                for f in data["data"][:3]:
                    flights.append({
                        "price": f"${f.get('price', 0)}",
"currency": "EUR",
                        "total_duration": f.get('duration', {}).get('total', 0),
                        "flights": [{
                            "airline": f.get('airlines', [''])[0] if f.get('airlines') else "Unknown",
                            "flight_number": f.get('flight_no', ''),
                        }],
                        "route": f.get('route', []),
                        "booking_token": f.get('booking_token', '')
                    })
            return {"rapidapi_flights": flights, "currency": "EUR"}
        return None
    except Exception:
        return None


def search_flights(departure_iata, arrival_iata, outbound_date, return_date):
    """Search flights using SerpApi with RapidAPI fallback."""
    api_key = st.secrets.get("SERPAPI_API_KEY")
    if not api_key:
        return None
    
    result = search_flights_cached(departure_iata, arrival_iata, outbound_date, return_date, api_key)
    
    if result and (result.get("best_flights") or result.get("other_flights")):
        return result
    
    rapidapi_key = st.secrets.get("RAPIDAPI_KEY")
    if rapidapi_key:
        fallback = search_flights_rapidapi(departure_iata, arrival_iata, outbound_date, return_date, rapidapi_key)
        if fallback:
            return fallback
    
    return result

MAJOR_AIRPORTS = [
    {"name": "Malpensa", "iata": "MXP", "lat": 45.6306, "lng": 8.7231, "city": "Milan"},
    {"name": "Linate", "iata": "LIN", "lat": 45.4451, "lng": 9.2787, "city": "Milan"},
    {"name": "Bergamo", "iata": "BGY", "lat": 45.6739, "lng": 9.6662, "city": "Bergamo"},
    {"name": "Fiumicino", "iata": "FCO", "lat": 41.8003, "lng": 12.2389, "city": "Rome"},
    {"name": "Ciampino", "iata": "CIA", "lat": 41.7994, "lng": 12.5949, "city": "Rome"},
    {"name": "Zurich", "iata": "ZRH", "lat": 47.4647, "lng": 8.5492, "city": "Zurich"},
    {"name": "Geneva", "iata": "GVA", "lat": 46.2381, "lng": 6.1089, "city": "Geneva"},
    {"name": "Basel", "iata": "BSL", "lat": 47.2953, "lng": 7.6289, "city": "Basel"},
    {"name": "Bern", "iata": "BRN", "lat": 46.9144, "lng": 7.4967, "city": "Bern"},
    {"name": "Stuttgart", "iata": "STR", "lat": 48.6899, "lng": 9.2219, "city": "Stuttgart"},
    {"name": "Frankfurt", "iata": "FRA", "lat": 50.0379, "lng": 8.5622, "city": "Frankfurt"},
    {"name": "Munich", "iata": "MUC", "lat": 48.3538, "lng": 11.7861, "city": "Munich"},
    {"name": "Berlin Brandenburg", "iata": "BER", "lat": 52.3661, "lng": 13.5067, "city": "Berlin"},
    {"name": "Hamburg", "iata": "HAM", "lat": 53.6304, "lng": 9.9882, "city": "Hamburg"},
    {"name": "Düsseldorf", "iata": "DUS", "lat": 51.2895, "lng": 6.7668, "city": "Düsseldorf"},
    {"name": "Copenhagen", "iata": "CPH", "lat": 55.6180, "lng": 12.6508, "city": "Copenhagen"},
    {"name": "Stockholm Arlanda", "iata": "ARN", "lat": 59.6519, "lng": 17.9186, "city": "Stockholm"},
    {"name": "Gothenburg", "iata": "GOT", "lat": 57.7229, "lng": 11.9708, "city": "Gothenburg"},
    {"name": "Malmö", "iata": "MMX", "lat": 55.5363, "lng": 13.2717, "city": "Malmö"},
    {"name": "Paris CDG", "iata": "CDG", "lat": 49.0097, "lng": 2.5479, "city": "Paris"},
    {"name": "Paris Orly", "iata": "ORY", "lat": 48.7262, "lng": 2.3652, "city": "Paris"},
    {"name": "Beauvais", "iata": "BVA", "lat": 49.3544, "lng": 2.1128, "city": "Paris"},
    {"name": "Lyon", "iata": "LYS", "lat": 45.7260, "lng": 5.0908, "city": "Lyon"},
    {"name": "Marseille", "iata": "MRS", "lat": 43.4367, "lng": 5.4134, "city": "Marseille"},
    {"name": "Nantes", "iata": "NTE", "lat": 47.1534, "lng": -1.6093, "city": "Nantes"},
    {"name": "Brest", "iata": "BES", "lat": 48.2669, "lng": -4.1515, "city": "Brest"},
    {"name": "Barcelona", "iata": "BCN", "lat": 41.2974, "lng": 2.0833, "city": "Barcelona"},
    {"name": "Madrid", "iata": "MAD", "lat": 40.4983, "lng": -3.5676, "city": "Madrid"},
    {"name": "Valencia", "iata": "VLC", "lat": 39.4893, "lng": -0.4816, "city": "Valencia"},
    {"name": "Seville", "iata": "SVQ", "lat": 37.4180, "lng": -5.8931, "city": "Seville"},
    {"name": "Amsterdam Schiphol", "iata": "AMS", "lat": 52.3105, "lng": 4.7683, "city": "Amsterdam"},
    {"name": "Rotterdam", "iata": "RTM", "lat": 51.9523, "lng": 4.4792, "city": "Rotterdam"},
    {"name": "Brussels", "iata": "BRU", "lat": 50.9014, "lng": 4.4844, "city": "Brussels"},
    {"name": "Charleroi", "iata": "CRL", "lat": 50.4592, "lng": 4.4538, "city": "Charleroi"},
    {"name": "London Heathrow", "iata": "LHR", "lat": 51.4706, "lng": -0.4619, "city": "London"},
    {"name": "London Gatwick", "iata": "LGW", "lat": 51.1537, "lng": -0.1900, "city": "London"},
    {"name": "London Stansted", "iata": "STN", "lat": 51.8860, "lng": 0.2389, "city": "London"},
    {"name": "Manchester", "iata": "MAN", "lat": 53.3536, "lng": -2.2750, "city": "Manchester"},
    {"name": "Birmingham", "iata": "BHX", "lat": 52.4539, "lng": -1.7442, "city": "Birmingham"},
    {"name": "Edinburgh", "iata": "EDI", "lat": 55.9500, "lng": -3.3500, "city": "Edinburgh"},
    {"name": "Glasgow", "iata": "GLA", "lat": 55.8654, "lng": -4.4330, "city": "Glasgow"},
    {"name": "Dublin", "iata": "DUB", "lat": 53.4264, "lng": -6.2499, "city": "Dublin"},
    {"name": "Vienna", "iata": "VIE", "lat": 48.1103, "lng": 16.5697, "city": "Vienna"},
    {"name": "Salzburg", "iata": "SZG", "lat": 47.7897, "lng": 13.0046, "city": "Salzburg"},
    {"name": "Prague", "iata": "PRG", "lat": 50.1068, "lng": 14.2608, "city": "Prague"},
    {"name": "Budapest", "iata": "BUD", "lat": 47.4367, "lng": 19.2556, "city": "Budapest"},
    {"name": "Warsaw", "iata": "WAW", "lat": 52.1657, "lng": 20.9671, "city": "Warsaw"},
    {"name": "Krakow", "iata": "KRK", "lat": 50.0777, "lng": 19.7848, "city": "Krakow"},
    {"name": "Athens", "iata": "ATH", "lat": 37.9365, "lng": 23.9443, "city": "Athens"},
    {"name": "Thessaloniki", "iata": "SKG", "lat": 40.5197, "lng": 22.9709, "city": "Thessaloniki"},
    {"name": "Lisbon", "iata": "LIS", "lat": 38.7742, "lng": -9.1342, "city": "Lisbon"},
    {"name": "Porto", "iata": "OPO", "lat": 41.2353, "lng": -8.6790, "city": "Porto"},
    {"name": "Helsinki", "iata": "HEL", "lat": 60.3172, "lng": 24.9633, "city": "Helsinki"},
    {"name": "Oslo", "iata": "OSL", "lat": 60.1939, "lng": 11.1004, "city": "Oslo"},
    {"name": "Moscow Sheremetyevo", "iata": "SVO", "lat": 55.9726, "lng": 37.4146, "city": "Moscow"},
    {"name": "Moscow Domodedovo", "iata": "DME", "lat": 55.4106, "lng": 37.9026, "city": "Moscow"},
    {"name": "Saint Petersburg", "iata": "LED", "lat": 59.8003, "lng": 30.2625, "city": "St. Petersburg"},
    {"name": "New York JFK", "iata": "JFK", "lat": 40.6413, "lng": -73.7781, "city": "New York"},
    {"name": "New York LaGuardia", "iata": "LGA", "lat": 40.7769, "lng": -73.8740, "city": "New York"},
    {"name": "Newark", "iata": "EWR", "lat": 40.6895, "lng": -74.1745, "city": "Newark"},
    {"name": "Los Angeles", "iata": "LAX", "lat": 33.9416, "lng": -118.4085, "city": "Los Angeles"},
    {"name": "Chicago O'Hare", "iata": "ORD", "lat": 41.9742, "lng": -87.9073, "city": "Chicago"},
    {"name": "Chicago Midway", "iata": "MDW", "lat": 41.7868, "lng": -87.7522, "city": "Chicago"},
    {"name": "San Francisco", "iata": "SFO", "lat": 37.6213, "lng": -122.3790, "city": "San Francisco"},
    {"name": "Miami", "iata": "MIA", "lat": 25.7959, "lng": -80.2870, "city": "Miami"},
    {"name": "Boston", "iata": "BOS", "lat": 42.3656, "lng": -71.0096, "city": "Boston"},
    {"name": "Seattle", "iata": "SEA", "lat": 47.4502, "lng": -122.3088, "city": "Seattle"},
    {"name": "Denver", "iata": "DEN", "lat": 39.8561, "lng": -104.6737, "city": "Denver"},
    {"name": "Dallas Fort Worth", "iata": "DFW", "lat": 32.8998, "lng": -97.0403, "city": "Dallas"},
    {"name": "Atlanta", "iata": "ATL", "lat": 33.6407, "lng": -84.4277, "city": "Atlanta"},
    {"name": "Washington Dulles", "iata": "IAD", "lat": 38.9531, "lng": -77.4565, "city": "Washington"},
    {"name": "Washington Reagan", "iata": "DCA", "lat": 38.8512, "lng": -77.0402, "city": "Washington"},
    {"name": "Toronto Pearson", "iata": "YYZ", "lat": 43.6777, "lng": -79.6248, "city": "Toronto"},
    {"name": "Toronto City", "iata": "YTZ", "lat": 43.6273, "lng": -79.3962, "city": "Toronto"},
    {"name": "Vancouver", "iata": "YVR", "lat": 49.1967, "lng": -123.1815, "city": "Vancouver"},
    {"name": "Montreal", "iata": "YUL", "lat": 45.4706, "lng": -73.7408, "city": "Montreal"},
    {"name": "Mexico City", "iata": "MEX", "lat": 19.4361, "lng": -99.0719, "city": "Mexico City"},
    {"name": "São Paulo GRU", "iata": "GRU", "lat": -23.4356, "lng": -46.4731, "city": "São Paulo"},
    {"name": "São Paulo Congonhas", "iata": "CGH", "lat": -23.6272, "lng": -46.6566, "city": "São Paulo"},
    {"name": "Rio de Janeiro", "iata": "GIG", "lat": -22.8099, "lng": -43.2515, "city": "Rio de Janeiro"},
    {"name": "Buenos Aires Ezeiza", "iata": "EZE", "lat": -34.8222, "lng": -58.5358, "city": "Buenos Aires"},
    {"name": "Buenos Aires Jorge Newbery", "iata": "AEP", "lat": -34.5592, "lng": -58.4163, "city": "Buenos Aires"},
    {"name": "Dubai", "iata": "DXB", "lat": 25.2532, "lng": 55.3657, "city": "Dubai"},
    {"name": "Abu Dhabi", "iata": "AUH", "lat": 24.4331, "lng": 54.6511, "city": "Abu Dhabi"},
    {"name": "Doha", "iata": "DOH", "lat": 25.2731, "lng": 51.6080, "city": "Doha"},
    {"name": "Riyadh", "iata": "RUH", "lat": 24.7104, "lng": 46.6723, "city": "Riyadh"},
    {"name": "Jeddah", "iata": "JED", "lat": 21.6796, "lng": 39.1565, "city": "Jeddah"},
    {"name": "Kuwait", "iata": "KWI", "lat": 29.2250, "lng": 47.6433, "city": "Kuwait"},
    {"name": "Tel Aviv", "iata": "TLV", "lat": 32.0114, "lng": 34.8867, "city": "Tel Aviv"},
    {"name": "Istanbul", "iata": "IST", "lat": 41.2753, "lng": 28.7519, "city": "Istanbul"},
    {"name": "Istanbul Sabiha", "iata": "SAW", "lat": 40.8986, "lng": 29.3092, "city": "Istanbul"},
    {"name": "Antalya", "iata": "AYT", "lat": 36.9833, "lng": 30.9500, "city": "Antalya"},
    {"name": "Tokyo Narita", "iata": "NRT", "lat": 35.7720, "lng": 140.3929, "city": "Tokyo"},
    {"name": "Tokyo Haneda", "iata": "HND", "lat": 35.5494, "lng": 139.7798, "city": "Tokyo"},
    {"name": "Osaka Kansai", "iata": "KIX", "lat": 34.4273, "lng": 135.2444, "city": "Osaka"},
    {"name": "Seoul Incheon", "iata": "ICN", "lat": 37.4602, "lng": 126.4407, "city": "Seoul"},
    {"name": "Seoul Gimpo", "iata": "GMP", "lat": 37.5588, "lng": 126.7926, "city": "Seoul"},
    {"name": "Beijing", "iata": "PEK", "lat": 40.0799, "lng": 116.6031, "city": "Beijing"},
    {"name": "Beijing Daxing", "iata": "PKX", "lat": 39.5099, "lng": 116.4106, "city": "Beijing"},
    {"name": "Shanghai Pudong", "iata": "PVG", "lat": 31.1443, "lng": 121.8083, "city": "Shanghai"},
    {"name": "Shanghai Hongqiao", "iata": "SHA", "lat": 31.1439, "lng": 121.3353, "city": "Shanghai"},
    {"name": "Hong Kong", "iata": "HKG", "lat": 22.3080, "lng": 113.9185, "city": "Hong Kong"},
    {"name": "Taipei", "iata": "TPE", "lat": 25.0797, "lng": 121.2342, "city": "Taipei"},
    {"name": "Singapore", "iata": "SIN", "lat": 1.3644, "lng": 103.9915, "city": "Singapore"},
    {"name": "Kuala Lumpur", "iata": "KUL", "lat": 2.7456, "lng": 101.7099, "city": "Kuala Lumpur"},
    {"name": "Bangkok", "iata": "BKK", "lat": 13.6900, "lng": 100.7501, "city": "Bangkok"},
    {"name": "Phuket", "iata": "HKT", "lat": 8.1089, "lng": 98.3169, "city": "Phuket"},
    {"name": "Jakarta", "iata": "CGK", "lat": -6.1256, "lng": 106.6559, "city": "Jakarta"},
    {"name": "Bali", "iata": "DPS", "lat": -8.7474, "lng": 115.1672, "city": "Bali"},
    {"name": "Manila", "iata": "MNL", "lat": 14.5086, "lng": 121.0195, "city": "Manila"},
    {"name": "Ho Chi Minh", "iata": "SGN", "lat": 10.8188, "lng": 106.6519, "city": "Ho Chi Minh"},
    {"name": "Hanoi", "iata": "HAN", "lat": 21.2212, "lng": 105.8069, "city": "Hanoi"},
    {"name": "Mumbai", "iata": "BOM", "lat": 19.0896, "lng": 72.8656, "city": "Mumbai"},
    {"name": "Delhi", "iata": "DEL", "lat": 28.5562, "lng": 77.1000, "city": "Delhi"},
    {"name": "Bangalore", "iata": "BLR", "lat": 13.1979, "lng": 77.7063, "city": "Bangalore"},
    {"name": "Kolkata", "iata": "CCU", "lat": 22.6508, "lng": 88.3419, "city": "Kolkata"},
    {"name": "Chennai", "iata": "MAA", "lat": 12.9944, "lng": 80.1708, "city": "Chennai"},
    {"name": "Sydney", "iata": "SYD", "lat": -33.9399, "lng": 151.1753, "city": "Sydney"},
    {"name": "Melbourne", "iata": "MEL", "lat": -37.6690, "lng": 144.8410, "city": "Melbourne"},
    {"name": "Brisbane", "iata": "BNE", "lat": -27.3942, "lng": 153.1218, "city": "Brisbane"},
    {"name": "Perth", "iata": "PER", "lat": -31.9403, "lng": 115.9672, "city": "Perth"},
    {"name": "Auckland", "iata": "AKL", "lat": -37.0082, "lng": 174.7850, "city": "Auckland"},
    {"name": "Wellington", "iata": "WLG", "lat": -41.3272, "lng": 174.8050, "city": "Wellington"},
    {"name": "Cairo", "iata": "CAI", "lat": 30.1219, "lng": 31.4056, "city": "Cairo"},
    {"name": "Casablanca", "iata": "CMN", "lat": 33.3675, "lng": -7.5898, "city": "Casablanca"},
    {"name": "Tunis", "iata": "TUN", "lat": 36.8512, "lng": 10.2272, "city": "Tunis"},
    {"name": "Algiers", "iata": "ALG", "lat": 36.6913, "lng": 3.2157, "city": "Algiers"},
    {"name": "Lagos", "iata": "LOS", "lat": 6.5774, "lng": 3.3215, "city": "Lagos"},
    {"name": "Nairobi", "iata": "NBO", "lat": -1.3192, "lng": 36.8178, "city": "Nairobi"},
    {"name": "Johannesburg", "iata": "JNB", "lat": -26.1367, "lng": 28.2411, "city": "Johannesburg"},
    {"name": "Cape Town", "iata": "CPT", "lat": -33.9715, "lng": 18.6021, "city": "Cape Town"},
    {"name": "Addis Ababa", "iata": "ADD", "lat": 8.9779, "lng": 38.7993, "city": "Addis Ababa"},
    {"name": "Kingston", "iata": "KIN", "lat": 17.9357, "lng": -76.7885, "city": "Kingston"},
    {"name": "Havana", "iata": "HAV", "lat": 22.9892, "lng": -82.4089, "city": "Havana"},
    {"name": "Panama City", "iata": "PTY", "lat": 9.0714, "lng": -79.4086, "city": "Panama City"},
    {"name": "San Jose CR", "iata": "SJO", "lat": 9.9935, "lng": -84.2008, "city": "San Jose"},
]

def get_airports(lat, lng, radius_km=150):
    result = []
    for ap in MAJOR_AIRPORTS:
        try:
            R = 6371
            phi1, phi2 = math.radians(lat), math.radians(ap["lat"])
            dphi = math.radians(ap["lat"] - lat)
            dlambda = math.radians(ap["lng"] - lng)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            dist = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            if dist <= radius_km:
                result.append({**ap, "distance": dist})
        except:
            pass
    return sorted(result, key=lambda x: x["distance"])[:3]

st.set_page_config(page_title="Concert Map", page_icon="📍")

API_BASE_URL = "https://rest.bandsintown.com"

secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")

if os.path.exists(secrets_path):
    secrets = toml.load(secrets_path)
    app_id = secrets.get("BANDSINTOWN_APP_ID", "test")
else:
    app_id = os.environ.get("BANDSINTOWN_APP_ID", "test")

artist = "Nanowar of Steel"
artist_id = "1281830"

logo_path = os.path.join(os.path.dirname(__file__), "static", "logo.png")
if os.path.exists(logo_path):
    st.image(logo_path, width=600)
else:
    st.title("In The Sky Scanner")

airport_options = [(f"{ap['city']} ({ap['iata']}) - {ap['name']}", ap) for ap in MAJOR_AIRPORTS]
airport_options = sorted(airport_options, key=lambda x: x[0])
if "flight_search_done" not in st.session_state:
    st.session_state.flight_search_done = False

if "airport_select" not in st.session_state:
    st.session_state.airport_select = 0

if st.session_state.get("airport_select") != st.session_state.get("last_airport_index"):
    st.session_state.flight_search_done = False
    st.session_state.last_airport_index = st.session_state.airport_select

departure_airport = airport_options[st.session_state.airport_select][1]

url = f"{API_BASE_URL}/artists/id_{artist_id}/events?app_id={app_id}&date=upcoming"
response = requests.get(url)

if response.status_code == 200:
    events = response.json()
    
    cities = []
    for event in events:
        venue = event.get("venue", {})
        lat = venue.get("latitude")
        lng = venue.get("longitude")
        city = venue.get("city", "")
        country = venue.get("country", "")
        
        if lat and lng:
            try:
                lat = float(lat)
                lng = float(lng)
                offers = event.get("offers", [])
                ticket_url = offers[0].get("url", "") if offers else ""
                cities.append({
                    "city": city,
                    "country": country,
                    "venue": venue.get("name", ""),
                    "datetime": event.get("datetime", ""),
                    "lat": lat,
                    "lng": lng,
                    "ticket_url": ticket_url
                })
            except (ValueError, TypeError):
                pass
    
    if cities:
        st.success(f"Found {len(cities)} upcoming events")
        
        center_lat = sum(c["lat"] for c in cities) / len(cities)
        center_lng = sum(c["lng"] for c in cities) / len(cities)
        
        m = folium.Map(location=[center_lat, center_lng], zoom_start=5)
        
        folium.Marker(
            location=[departure_airport["lat"], departure_airport["lng"]],
            popup=f"DEPARTURE: {departure_airport['name']} ({departure_airport['iata']})",
            icon=folium.Icon(color="green", icon="play")
        ).add_to(m)
        
        for c in cities:
            venue_date = c["datetime"][:10]
            show_date = datetime.strptime(venue_date, "%Y-%m-%d")
            dep_date = (show_date - timedelta(days=1)).strftime("%Y-%m-%d")
            ret_date = (show_date + timedelta(days=1)).strftime("%Y-%m-%d")
            
            folium.Marker(
                location=[c["lat"], c["lng"]],
                popup=f"{c['venue']}<br>{c['city']}, {c['country']}<br>{c['datetime'][:10]}",
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)
            
            if st.session_state.flight_search_done:
                airports = get_airports(c["lat"], c["lng"], radius_km=150)
                for ap in airports:
                    folium.Marker(
                        location=[ap["lat"], ap["lng"]],
                        popup=f"Airport: {ap['name']}<br>IATA: {ap['iata']}<br>Dist: {ap['distance']:.1f} km",
                        icon=folium.Icon(color="blue", icon="plane")
                    ).add_to(m)
                    folium.PolyLine(
                        locations=[
                            [departure_airport["lat"], departure_airport["lng"]],
                            [ap["lat"], ap["lng"]]
                        ],
                        color="green",
                        weight=2,
                        opacity=0.7
                    ).add_to(m)
        
        st_folium(m, height=600, use_container_width=True)
        
        st.write("### Upcoming Events")
        for c in cities:
            venue_date = c["datetime"][:10]
            ticket_link = f"[TICKET]({c['ticket_url']})" if c.get("ticket_url") else "Tickets unavailable"
            st.write(f"- **{c['venue']}** in {c['city']}, {c['country']} on {venue_date} | {ticket_link}")
        
        st.write("### Select Departure Airport")
        st.selectbox(
            "Choose your departure airport",
            range(len(airport_options)),
            format_func=lambda i: airport_options[i][0],
            key="airport_select"
        )
        
        st.write("---")
        
        if not st.session_state.flight_search_done:
            if st.button("🔍 Search Flights", type="primary"):
                st.session_state.flight_search_done = True
                st.rerun()
        
        if st.session_state.flight_search_done:
            st.write("### Flight Options")
            
            with st.spinner("Searching for flights..."):
                for c in cities:
                    venue_date = c["datetime"][:10]
                    show_date = datetime.strptime(venue_date, "%Y-%m-%d")
                    dep_date = (show_date - timedelta(days=1)).strftime("%Y-%m-%d")
                    ret_date = (show_date + timedelta(days=1)).strftime("%Y-%m-%d")
                    
                    airports = get_airports(c["lat"], c["lng"], radius_km=150)
                    ticket_link = f"[TICKET]({c['ticket_url']})" if c.get("ticket_url") else "Tickets unavailable"
                    st.write(f"**{c['city']}, {c['country']}** - {c['venue']} on {venue_date} | {ticket_link}")
                    st.write(f"Departure: {dep_date}, Return: {ret_date}")
                    
                    for ap in airports[:3]:
                        route = f"{departure_airport['iata']} → {ap['iata']}"
                        st.write(f"**{route}**")
                        
                        result = search_flights(
                            departure_airport['iata'],
                            ap['iata'],
                            dep_date,
                            ret_date
                        )
                        
                        if result:
                            rapid_flights = result.get("rapidapi_flights")
                            if rapid_flights:
                                currency = result.get("currency", "USD")
                                for flight in rapid_flights:
                                    price = flight.get("price", "N/A")
                                    duration = flight.get("total_duration", 0)
                                    hours = duration // 60
                                    mins = duration % 60
                                    flights = flight.get("flights", [])
                                    airlines = [f.get("airline", "Unknown") for f in flights]
                                    stops = len(flights) - 1
                                    
                                    st.write(f"  • **{price}** {currency} | {hours}h {mins}m | {stops} stop(s) | {', '.join(airlines) if airlines else 'Multiple airlines'}")
                            else:
                                best = result.get("best_flights", [])
                                other = result.get("other_flights", [])
                                all_flights = best + other
                                if all_flights:
                                    currency = result.get("search_parameters", {}).get("currency", "USD")
                                    for flight in all_flights[:3]:
                                        price = flight.get("price", "N/A")
                                        duration = flight.get("total_duration", 0)
                                        hours = duration // 60
                                        mins = duration % 60
                                        flights = flight.get("flights", [])
                                        stops = len(flights) - 1
                                        airlines = list(set(f.get("airline", "") for f in flights if f.get("airline")))
                                        
                                        link = f"https://www.google.com/travel/flights?hl=en&q={departure_airport['iata']}%20to%20{ap['iata']}%20{dep_date}"
                                        st.markdown(f"  • **[{price}]({link})** {currency} | {hours}h {mins}m | {stops} stop(s) | {', '.join(airlines) if airlines else 'Multiple airlines'}")
                                else:
                                    st.write("  No flights found")
                        else:
                            st.write("  Search failed")
                        st.write("")
                st.write("")
    else:
        st.warning("No events with location data found")
else:
    st.error(f"Error: {response.status_code}")
