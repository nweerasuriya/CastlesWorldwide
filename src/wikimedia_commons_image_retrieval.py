"""
Enter script name

Enter short description of the script
"""

__date__ = "2025-03-15"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"



import pandas as pd
import requests
import time
from tqdm import tqdm
import os

class WikimediaImageScraper:
    def __init__(self, delay=1):
        """
        Initialize the Wikimedia Commons image scraper.
        
        Args:
            delay (float): Delay between API requests in seconds
        """
        self.base_url = "https://commons.wikimedia.org/w/api.php"
        self.delay = delay
        self.session = requests.Session()
        
    def search_images(self, query, max_images=10):
        """
        Search for images related to a specific query.
        
        Args:
            query (str): Search query
            max_images (int): Maximum number of images to return
            
        Returns:
            list: List of image metadata dictionaries
        """
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": f"{query} filetype:bitmap",
            "srnamespace": 6,  # File namespace
            "srlimit": max_images
        }
        
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("query", {}).get("search", []):
                title = item.get("title", "")
                if title.lower().endswith(('.jpg', '.jpeg', '.png')):
                    results.append({
                        "title": title,
                        "pageid": item.get("pageid")
                    })
            
            return results[:max_images]
        
        except requests.exceptions.RequestException as e:
            print(f"Error searching for images: {e}")
            return []
    
    def get_image_urls(self, image_titles):
        """
        Get the URLs for the specified image titles.
        
        Args:
            image_titles (list): List of image titles
            
        Returns:
            dict: Dictionary mapping image titles to URLs
        """
        if not image_titles:
            return {}
            
        params = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "titles": "|".join(image_titles),
            "iiprop": "url|size|extmetadata",
            "iiurlwidth": 800,  # Thumbnail width
        }
        
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            image_urls = {}
            pages = data.get("query", {}).get("pages", {})
            
            for page_id, page_data in pages.items():
                title = page_data.get("title", "")
                image_info = page_data.get("imageinfo", [{}])[0]
                if image_info:
                    image_urls[title] = {
                        "url": image_info.get("url", ""),
                        "thumb_url": image_info.get("thumburl", ""),
                        "descriptionurl": image_info.get("descriptionurl", ""),
                        "width": image_info.get("width", 0),
                        "height": image_info.get("height", 0),
                        "size": image_info.get("size", 0)
                    }
            
            return image_urls
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching image URLs: {e}")
            return {}
    
    def process_castle_data(self, castle_df, castle_name_col='name', country_name_col="country", output_col_prefix="image_url_", max_images=10):
        """
        Process a DataFrame of castle data and add image URLs.
        
        Args:
            castle_df (pd.DataFrame): DataFrame containing castle data
            castle_name_col (str): Column name containing castle names
            country_name_col (str): Column name containing country names
            output_col_prefix (str): Prefix for output columns
            max_images (int): Maximum number of images per castle
            
        Returns:  
            pd.DataFrame: DataFrame with added image URL columns
        """
        # Create a copy to avoid modifying the original
        result_df = castle_df.copy()
        
        # Add columns for image URLs
        for i in range(max_images):
            result_df[f"{output_col_prefix}{i+1}"] = ""
            result_df[f"{output_col_prefix}{i+1}_description_url"] = ""
        
        # Process each castle
        for idx, row in tqdm(result_df.iterrows(), total=len(result_df), desc="Processing castles"):
            
            # Construct search query with castle name and country
            search_query = f"{row[castle_name_col]} {row[country_name_col]}"
            
            # Search for images
            image_results = self.search_images(search_query, max_images=max_images)
            
            if image_results:
                # Get image titles
                image_titles = [result["title"] for result in image_results]
                
                # Get image URLs
                image_urls = self.get_image_urls(image_titles)
                
                # Add URLs to DataFrame
                for i, title in enumerate(image_titles[:max_images]):
                    if i < max_images and title in image_urls:
                        result_df.at[idx, f"{output_col_prefix}{i+1}"] = image_urls[title]["url"]
                        result_df.at[idx, f"{output_col_prefix}{i+1}_description_url"] = image_urls[title]["descriptionurl"]
            
            # Respect rate limits
            time.sleep(self.delay)
        
        return result_df


# Example usage
if __name__ == "__main__":
    # Load your castle data
    # Replace 'castle_data.csv' with your actual file and 'castle_name' with your column name
    castle_df = pd.read_csv('outputs/castle_list_rest.csv')
    
    # Initialize scraper with a 1-second delay between requests (adjust as needed)
    scraper = WikimediaImageScraper(delay=1)
    
    # Process the castle data
    result_df = scraper.process_castle_data(
        castle_df,
        castle_name_col='name',  # Replace with your castle name column
        max_images=5  # Get up to 5 images per castle
    )
    
    # Save the results
    result_df.to_csv('outputs/images/castle_data_with_images_rest.csv', index=False)
    print(f"Process complete. Results saved to 'castle_data_with_images.csv'")