"""
Enter script name

Enter short description of the script
"""

__date__ = "2025-03-16"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"



# %% --------------------------------------------------------------------------
# Import Modules
import math
import pandas as pd
from src.wikipedia import WikipediaImageFinder

# Load your castle data
castle_df = pd.read_csv('outputs/images/castle_data_with_images_rest.csv')

# Initialize the finder
finder = WikipediaImageFinder()

# Process the castle data
result_df = finder.process_castle_data(
    castle_df,
    castle_name_col='name',
    country_col='country',  # Your country column name
    region_col='region',    # Your region/state column name if available
    max_images=5
)

# Save the results
result_df.to_csv('outputs/images/castle_data_with_wikipedia_images_2.csv', index=False)


# %% --------------------------------------------------------------------------
# Combine image URLs into a single column
# -----------------------------------------------------------------------------
df = result_df.copy()
# combined wikipedia image urls into a single column as a list without keeping nans
df['wikipedia_image_urls'] = df[['wiki_image_1_url', 'wiki_image_2_url', 'wiki_image_3_url', 'wiki_image_4_url', 'wiki_image_5_url']].values.tolist()
# drop nan values in list
df['wikipedia_image_urls'] = df['wikipedia_image_urls'].apply(lambda x: [i for i in x if not (isinstance(i, float) and math.isnan(i))])
df = df.drop(columns=['wiki_image_1_url', 'wiki_image_2_url', 'wiki_image_3_url', 'wiki_image_4_url', 'wiki_image_5_url'])

# combine wikimedia image urls into a single column as a list
df['wikimedia_image_urls'] = df[['image_url_1', 'image_url_2', 'image_url_3', 'image_url_4', 'image_url_5']].values.tolist()
# drop nan values in list
df['wikimedia_image_urls'] = df['wikimedia_image_urls'].apply(lambda x: [i for i in x if not (isinstance(i, float) and math.isnan(i))])
df = df.drop(columns=[
    'image_url_1', 'image_url_2', 'image_url_3', 'image_url_4', 'image_url_5', 'image_url_6', 'image_url_7', 'image_url_8', 'image_url_9', 'image_url_10'
    ])

df['wikipedia_number_of_images'] = df['wikipedia_image_urls'].apply(lambda x: len([i for i in x if i != '']))
df['wikimedia_number_of_images'] = df['wikimedia_image_urls'].apply(lambda x: len([i for i in x if i != '']))

# sort by number of wikipedia images
df = df.sort_values(by='wikipedia_number_of_images', ascending=False)
df.to_csv("outputs/final/castle_data_all_images_rest.csv", index=False)

# %%
