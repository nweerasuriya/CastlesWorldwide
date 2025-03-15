"""
Extract data from OpenStreetMap
"""

__date__ = "2025-03-10"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"



import requests
import pandas as pd
import time
from tqdm import tqdm

def get_castles_from_overpass(country=None):
    """
    Fetch castle data from OpenStreetMap using Overpass API
    
    Parameters:
    country (str, optional): Country name to limit the search
    
    Returns:
    list: List of dictionaries containing castle information
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Build query based on whether a country is specified
    if country:
        overpass_query = f"""
        [out:json];
        area["name"="{country}"][admin_level=2];
        (
          node["historic"="castle"](area);
          way["historic"="castle"](area);
          relation["historic"="castle"](area);
          
        );
        out center;
        """
    else:
        overpass_query = """
        [out:json];
        (
          node["historic"="castle"];
          way["historic"="castle"];
          relation["historic"="castle"];
        );
        out center;
        """
    
    response = requests.get(overpass_url, params={'data': overpass_query})
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []
    
    data = response.json()
    
    castles = []
    for element in data['elements']:
        # Extract location data
        if element['type'] == 'node':
            lat = element['lat']
            lon = element['lon']
        elif 'centre' in element:
            lat = element['center']['lat']
            lon = element['center']['lon']
        else:
            lat = None
            lon = None        
        # Get tags
        tags = element.get('tags', {})
        
        # Basic castle information
        castle_info = {
            'id': element['id'],
            'osm_type': element['type'],
            'name': tags.get('name', 'Unknown'),
            'historic_type': tags.get('historic', ''),
            'castle_type': tags.get('castle_type', ''),
            'architecture': tags.get('architecture', ''),
            'start_date': tags.get('start_date', ''),
            'wikimedia_commons': tags.get('wikimedia_commons', ''),
            'wikipedia': tags.get('wikipedia', ''),
            'latitude': lat,
            'longitude': lon,
            'country': tags.get('country', '') or country,
            'city': tags.get('addr:city', ''),
            'address': ', '.join([tags.get(t, '') for t in ['addr:street', 'addr:city', 'addr:postcode'] if t in tags and tags[t]]),
            'website': tags.get('website', ''),
            'description': tags.get('description', '')
        }
        
        castles.append(castle_info)

    return castles

def get_castles_by_countries(countries):
    """
    Get castles for a list of countries
    
    Parameters:
    countries (list): List of country names
    
    Returns:
    pd.DataFrame: DataFrame with castle information
    """
    all_castles = []

    if countries:    
        for country in tqdm(countries, desc="Fetching countries"):
            print(f"Getting castles in {country}...")
            try:
                country_castles = get_castles_from_overpass(country)
                for castle in country_castles:
                    if 'country' not in castle or not castle['country']:
                        castle['country'] = country
                all_castles.extend(country_castles)
                print(f"Found {len(country_castles)} castles in {country}")
                # Be nice to the API
                time.sleep(1)
            except Exception as e:
                print(f"Error getting castles for {country}: {e}")
    else:
        all_castles = get_castles_from_overpass()

    # Convert to DataFrame
    df = pd.DataFrame(all_castles)
    
    # Remove duplicates based on location
    df = df.drop_duplicates(subset=['latitude', 'longitude'])
    
    return df
