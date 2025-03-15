"""
Testing the castle data collection workflow.
"""

__date__ = "2025-03-10"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"


# %% --------------------------------------------------------------------------

# -----------------------------------------------------------------------------
import pandas as pd
import os
from src.openstreetmap import get_castles_from_overpass, get_castles_by_countries
from src.utilities import read_sort_get_countries_by_first_letter

# Read the country data
csv_path = "data/countries.csv"

def get_data(csv_path, chosen_letter):
    """
    Get castle data for countries starting with a specific letter
    
    """
    castle_countries = read_sort_get_countries_by_first_letter(csv_path, chosen_letter)


    # Get castle data
    castle_df = get_castles_by_countries(castle_countries)

    # Basic statistics
    print(f"Total castles collected: {len(castle_df)}")
    if len(castle_df) > 0:
        castle_df.to_csv(f"data/letter_{chosen_letter}_castles.csv", index=False)
        print(f"Castles per country:\n{castle_df['country'].value_counts()}")
# %%
for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    get_data(csv_path, letter)


# %% --------------------------------------------------------------------------
# Get Unassigned Castles with no country
# -----------------------------------------------------------------------------
# Get castle data
castle_df = get_castles_by_countries(None)
# Save to CSV
castle_df.to_csv(f"data/unassaigned_castles.csv", index=False)
# Basic statistics
print(f"Total castles collected: {len(castle_df)}")


# %% --------------------------------------------------------------------------
# Combine all data into a single CSV
# -----------------------------------------------------------------------------
file_path = "data/"
all_castles = pd.DataFrame()
for file in os.listdir(file_path):
    if file.endswith("_castles.csv"):
        df = pd.read_csv(file_path + file)
        all_castles = pd.concat([all_castles, df])
# combine all data
all_castles.to_csv(file_path + "all_castles.csv", index=False)
