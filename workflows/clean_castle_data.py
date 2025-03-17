"""
Clean and update the castle data
"""

__date__ = "2025-03-11"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"



# %% --------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Import Modules
import pandas as pd
import numpy as np
# Read the data
df = pd.read_csv("outputs/llm_descriptions_2.csv")

# filter out castles with missing or unknown names
df = df[df['name']!="Unknown"]
df = df[df['name']!=""]
df = df[df['name'].notnull()]

# filter out descriptions beginning with "Unfortunately" or "I'm sorry"
null_descriptions = df[df['description'].isnull()]
df = df[df['description'].notnull()]
removed_descriptions = df[df['description'].str.startswith("Unfortunately") | df['description'].str.startswith("I'm sorry") | df['description'].str.startswith("I'm afraid")]

df = df.drop(removed_descriptions.index)

filtered_df = df[['name', 'description', 'historic_type', 'castle_type', 'country']]

# removed descriptions with less than 50 words
filtered_df = filtered_df[filtered_df['description'].str.split().str.len() > 50]


# %% --------------------------------------------------------------------------
# Add City column
# -----------------------------------------------------------------------------

def separate_city_country(text: str):
    """
    Separate city and country from a text string that has the format 'City: city_name, Country: country_name'
    """
    if 'City' in text:
        city = text.split('City: ')[1].split(',')[0]
        if city == 'Unknown':
            city = np.nan
    else:
        city = np.nan
    if 'Country' in text:
        country = text.split('Country: ')[1].split('\n')[0]
    else:
        country = np.nan
    return city, country


cities, countries = zip(*filtered_df['description'].apply(separate_city_country))
cities

# fix cases where single quotes are within double quotes
cities = [city.replace("'", "") if isinstance(city, str) else city for city in cities]
filtered_df['city'] = cities

# sort by populated columns with the order of preference: description, city, historic_type, castle_type
# Define column weights (higher = more important)
weights = {
    'description': 4,
    'city': 3,
    'historic_type': 2,
    'castle_type': 1
}
# Default weight of 1 for unspecified columns

# Apply weights to the notna() result
weighted_counts = pd.DataFrame({
    col: filtered_df[col].notna() * weights.get(col, 1) for col in filtered_df.columns
}).sum(axis=1)

# Sort by the weighted counts
df_sorted = filtered_df.loc[weighted_counts.sort_values(ascending=False).index]
df_sorted.reset_index(drop=True, inplace=True)

df_sorted = df_sorted[['name', 'country', 'city', 'castle_type', 'description']]

# Save the cleaned data enabling utf-8 encoding
df_sorted.to_csv("outputs/cleaned_castle_data_2.csv", index=False, encoding='utf-8')

# %%

# %% --------------------------------------------------------------------------
# Join classified castle datasets and remove rows
# -----------------------------------------------------------------------------
import pandas as pd

# Load the classified castle data
df = pd.read_csv("outputs/classified_castles_2.csv")

# remove rows marked for removal in structure_type column. Any with 'remove' included in the string
df = df[~df['structure_type'].str.contains('remove', case=False)]
df = df[~df['structure_type'].str.contains('invalid', case=False)]
#combined.to_csv("outputs/castle_list_rest.csv", index=False)

# Remove any row with the word ruin in the description or name
df = df[~df['description'].str.contains('ruin', case=False)]
df = df[~df['name'].str.contains('ruin', case=False)]

# remove any castle types in 'castle_type' columns that are stately. the column contains nans
df = df[~df['castle_type'].str.contains('stately', case=False, na=False)]


# only keep castles, palaces and fortresses
#df = df[df['structure_type'].str.contains('castle|palace|fortress', case=False)]
df = df[['name', 'country', 'city', 'structure_type', 'description']].reset_index(drop=True)

df.to_csv("outputs/castle_list_rest.csv", index=False)


# %%

# %% --------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
import pandas as pd

# Load the classified castle data
class_1 = pd.read_csv("outputs/images/castle_data_with_images_1000.csv")
class_2 = pd.read_csv("outputs/images/castle_data_with_images_rest.csv")

# Combine the two dataframes
combined = pd.concat([class_1, class_2], ignore_index=True)

# remove columns with image descriptions
combined = combined.drop(columns=combined.filter(like='description_url').columns)

# create number of images column (columns with image urls are name image_url_n)
combined['num_images'] = combined.filter(like='image_url').count(axis=1)



#to csv
#combined.to_csv("outputs/castle_data_with_images.csv", index=False)
# %%
# number of rows with < 3 images
combined[combined['num_images'] < 3].shape[0]

# %%
import pandas as pd

df1 = pd.read_csv("outputs/final/castle_data_all_images_v1.csv")
df2 = pd.read_csv("outputs/final/castle_data_all_images_v1_rest.csv")

combined = pd.concat([df1, df2], ignore_index=True)

# remove columns with less than 3 images between the two columns "wikimedia_number_of_images" and "wikipedia_number_of_images"
combined = combined[combined['wikimedia_number_of_images'] + combined['wikipedia_number_of_images'] > 3]

# remove rows with the same name
combined = combined.drop_duplicates(subset=['name'], keep='first')

# save to csv
combined.to_csv("outputs/final/castle_data_all_images_v2.csv", index=False)