"""Static NFL stadium lookup table for weather service.

{team_abbr: {lat, lon, indoor, name}}

Update when teams relocate or open new stadiums.
9 stadiums are indoor/dome: LV, LAR, LAC, IND, DET, MIN, ATL, ARI, HOU.
"""

NFL_STADIUMS: dict[str, dict] = {
    "ARI": {"lat": 33.5277, "lon": -112.2626, "indoor": True,  "name": "State Farm"},
    "ATL": {"lat": 33.7554, "lon": -84.4008,  "indoor": True,  "name": "Mercedes-Benz"},
    "BAL": {"lat": 39.2780, "lon": -76.6227,  "indoor": False, "name": "M&T Bank"},
    "BUF": {"lat": 42.7738, "lon": -78.7870,  "indoor": False, "name": "Highmark"},
    "CAR": {"lat": 35.2258, "lon": -80.8530,  "indoor": False, "name": "Bank of America"},
    "CHI": {"lat": 41.8623, "lon": -87.6167,  "indoor": False, "name": "Soldier Field"},
    "CIN": {"lat": 39.0954, "lon": -84.5160,  "indoor": False, "name": "Paycor"},
    "CLE": {"lat": 41.5061, "lon": -81.6995,  "indoor": False, "name": "Huntington Bank"},
    "DAL": {"lat": 32.7473, "lon": -97.0945,  "indoor": False, "name": "AT&T"},
    "DEN": {"lat": 39.7439, "lon": -105.0201, "indoor": False, "name": "Empower Field"},
    "DET": {"lat": 42.3400, "lon": -83.0456,  "indoor": True,  "name": "Ford Field"},
    "GB":  {"lat": 44.5013, "lon": -88.0622,  "indoor": False, "name": "Lambeau"},
    "HOU": {"lat": 29.6847, "lon": -95.4107,  "indoor": True,  "name": "NRG"},
    "IND": {"lat": 39.7601, "lon": -86.1639,  "indoor": True,  "name": "Lucas Oil"},
    "JAX": {"lat": 30.3240, "lon": -81.6373,  "indoor": False, "name": "EverBank"},
    "KC":  {"lat": 39.0490, "lon": -94.4839,  "indoor": False, "name": "Arrowhead"},
    "LAC": {"lat": 33.9535, "lon": -118.3392, "indoor": True,  "name": "SoFi"},
    "LAR": {"lat": 33.9535, "lon": -118.3392, "indoor": True,  "name": "SoFi"},
    "LV":  {"lat": 36.0909, "lon": -115.1833, "indoor": True,  "name": "Allegiant"},
    "MIA": {"lat": 25.9580, "lon": -80.2389,  "indoor": False, "name": "Hard Rock"},
    "MIN": {"lat": 44.9740, "lon": -93.2577,  "indoor": True,  "name": "US Bank"},
    "NE":  {"lat": 42.0909, "lon": -71.2643,  "indoor": False, "name": "Gillette"},
    "NO":  {"lat": 29.9511, "lon": -90.0812,  "indoor": False, "name": "Caesars Superdome"},
    "NYG": {"lat": 40.8135, "lon": -74.0745,  "indoor": False, "name": "MetLife"},
    "NYJ": {"lat": 40.8135, "lon": -74.0745,  "indoor": False, "name": "MetLife"},
    "PHI": {"lat": 39.9008, "lon": -75.1675,  "indoor": False, "name": "Lincoln Financial"},
    "PIT": {"lat": 40.4468, "lon": -80.0158,  "indoor": False, "name": "Acrisure"},
    "SF":  {"lat": 37.4033, "lon": -121.9694, "indoor": False, "name": "Levi's"},
    "SEA": {"lat": 47.5952, "lon": -122.3316, "indoor": False, "name": "Lumen Field"},
    "TB":  {"lat": 27.9759, "lon": -82.5033,  "indoor": False, "name": "Raymond James"},
    "TEN": {"lat": 36.1665, "lon": -86.7713,  "indoor": False, "name": "Nissan"},
    "WAS": {"lat": 38.9076, "lon": -76.8645,  "indoor": False, "name": "FedEx Field"},
}

WEATHER_WIND_THRESHOLD_MPH: int = 20
WEATHER_RAIN_CODE_THRESHOLD: int = 63   # WMO code >= 63 is heavy rain
