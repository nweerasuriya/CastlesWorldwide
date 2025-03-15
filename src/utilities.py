"""
Utility functions for the project
"""

__date__ = "2025-03-10"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"



# Import required libraries
import numpy as np
import pandas as pd

    
def read_sort_get_countries_by_first_letter(csv_file: str, chosen_letter: str = None) -> list:
    """
    Read a CSV file, sort the country names and return a list of countries
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Sort the country names
    countries = sorted(df['Country'].unique())
    
    # Filter countries by the first letter
    if chosen_letter:
        countries = [country for country in countries if country.startswith(chosen_letter)]
    
    return countries

def separate_city_country(text: str):
    """
    Separate city and country from a text string that has the format 'City: city_name, Country: country_name'
    """
    if 'City' in text:
        city = text.split('City: ')[1].split(',')[0]
    else:
        city = np.nan
    if 'Country' in text:
        country = text.split('Country: ')[1].split('  ')[0]
    else:
        country
    return city, country

