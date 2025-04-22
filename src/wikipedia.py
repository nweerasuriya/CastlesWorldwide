import requests
import pandas as pd
from tqdm import tqdm
import time
import json

class WikipediaImageFinder:
    def __init__(self, default_language="en", delay=1):
        """
        Initialize the Wikipedia image finder with country-based language support.
        
        Args:
            default_language (str): Default Wikipedia language code
            delay (float): Delay between API requests in seconds
        """
        self.default_language = default_language
        self.delay = delay
        self.session = requests.Session()
        
        # Map countries to their primary Wikipedia language codes
        self.country_language_map = json.loads(open("data/country_lang_map.json").read())

    def get_language_for_country(self, country):
        """
        Get the appropriate Wikipedia language code for a country.
        Defaults to the default language if not found.
        
        Args:
            country (str): Country name
            
        Returns:
            str: Wikipedia language code
        """
        return self.country_language_map.get(country, self.default_language)
        

    
    def get_base_url(self, language):
        """
        Get the base URL for a specific language Wikipedia.
        
        Args:
            language (str): Wikipedia language code
            
        Returns:
            str: Base URL for the Wikipedia API
        """
        return f"https://{language}.wikipedia.org/w/api.php"
    
    def find_castle_article(self, castle_name, country=None, region=None):
        """
        Find the Wikipedia article for a castle using country and region info.
        
        Args:
            castle_name (str): Name of the castle
            country (str, optional): Country where the castle is located
            region (str, optional): Region/state where the castle is located
            
        Returns:
            dict: Dictionary with article info and language used
        """
        # Try language based on country after trying english
        primary_language = self.get_language_for_country(country)
    
        # First try the country's primary language
        article = self._search_article(castle_name, "en")
        
        # If not found and primary language isn't English, try secondary language
        if not article and primary_language != "en":
            article = self._search_article(castle_name, primary_language)

        # Return what we found, including which language succeeded
        if article:
            return {
                "title": article,
                "language": primary_language if article["language"] != "en" else "en"
            }
        else:
            return None
    
    def _search_article(self, query, language):
        """
        Helper method to search for an article on a specific language Wikipedia.
        
        Args:
            query (str): Search query
            language (str): Wikipedia language code
            
        Returns:
            dict: Article info if found, None otherwise
        """
        base_url = self.get_base_url(language)
        
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": 1
        }
        
        try:
            response = self.session.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("query", {}).get("search"):
                # Return the article title and note which language succeeded
                return {
                    "title": data["query"]["search"][0]["title"],
                    "language": language
                }
            return None
            
        except Exception as e:
            print(f"Error searching in {language} Wikipedia for {query}: {e}")
            return None
    
    def get_article_images(self, article_title, language, max_images=5):
        """
        Get images from a Wikipedia article.
        
        Args:
            article_title (str): Title of the Wikipedia article
            language (str): Wikipedia language code
            max_images (int): Maximum number of images to return
            
        Returns:
            list: List of image titles
        """
        base_url = self.get_base_url(language)
        
        params = {
            "action": "query",
            "format": "json",
            "titles": article_title,
            "prop": "images",
            "imlimit": max_images * 2  # Get more to filter later
        }
        
        try:
            response = self.session.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            
            if not pages:
                return []
                
            # Get the first (and only) page
            page_id = list(pages.keys())[0]
            page_data = pages[page_id]
            
            # Extract image titles
            image_titles = []
            for image in page_data.get("images", []):
                image_title = image.get("title")
                # Filter out non-image files and icons
                if (image_title and 
                    any(image_title.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif')) and
                    not any(keyword in image_title.lower() for keyword in ('icon', 'logo', 'map', 'plan'))):
                    image_titles.append(image_title)
            
            return image_titles[:max_images]
            
        except Exception as e:
            print(f"Error getting images for {article_title} in {language} Wikipedia: {e}")
            return []
    
    def get_image_info(self, image_titles, language):
        """
        Get information about images.
        
        Args:
            image_titles (list): List of image titles
            language (str): Wikipedia language code
            
        Returns:
            list: List of image info dictionaries
        """
        if not image_titles:
            return []
            
        # For images, we need to use the Commons API or the specific language Wikipedia
        base_url = self.get_base_url(language)
        
        params = {
            "action": "query",
            "format": "json",
            "titles": "|".join(image_titles),
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|size"
        }
        
        try:
            response = self.session.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            pages = data.get("query", {}).get("pages", {})
            
            for page_id, page_data in pages.items():
                image_info = page_data.get("imageinfo", [{}])[0]
                
                if image_info:
                    ext_metadata = image_info.get("extmetadata", {})
                    license_data = ext_metadata.get("License", {}).get("value", "Unknown")
                    
                    # Get image dimensions for quality filtering
                    width = image_info.get("width", 0)
                    height = image_info.get("height", 0)
                    
                    # Skip low-resolution images
                    if width < 400 or height < 400:
                        continue
                    
                    results.append({
                        "title": page_data.get("title", ""),
                        "url": image_info.get("url", ""),
                        "license": license_data,
                        "description_url": image_info.get("descriptionurl", ""),
                        "width": width,
                        "height": height
                    })
            
            # Sort by image dimensions (approximate quality indicator)
            results.sort(key=lambda x: x["width"] * x["height"], reverse=True)
            
            return results
            
        except Exception as e:
            print(f"Error getting image info: {e}")
            return []
    
    def process_castle_data(self, castle_df, castle_name_col, country_col=None, region_col=None, output_col_prefix="wiki_image_", max_images=5):
        """
        Process a DataFrame of castle data to find Wikipedia images.
        
        Args:
            castle_df (pd.DataFrame): DataFrame containing castle data
            castle_name_col (str): Column name containing castle names
            country_col (str, optional): Column name containing country information
            region_col (str, optional): Column name containing region/state information
            output_col_prefix (str): Prefix for output columns
            max_images (int): Maximum number of images per castle
            
        Returns:
            pd.DataFrame: DataFrame with added image URL columns
        """
        # Create a copy to avoid modifying the original
        result_df = castle_df.copy()
        
        # Add columns for image URLs and metadata
        for i in range(max_images):
            result_df[f"{output_col_prefix}{i+1}_url"] = ""
        
        # Also add a column for the Wikipedia article
        result_df[f"wikipedia_article_url"] = ""
        result_df[f"wikipedia_language"] = ""
        
        # Process each castle
        for idx, row in tqdm(result_df.iterrows(), total=len(result_df), desc="Processing castles"):
            castle_name = row[castle_name_col]
            country = row[country_col] if country_col and country_col in row else None
            region = row[region_col] if region_col and region_col in row else None
            
            # Find Wikipedia article using country info
            article_info = self.find_castle_article(castle_name, country, region)
            
            if article_info:
                article_title = article_info["title"]['title']
                language = article_info["language"]
                
                # Store the article URL and language
                wiki_url = f"https://{language}.wikipedia.org/wiki/{article_title.replace(' ', '_')}"
                result_df.at[idx, f"wikipedia_article_url"] = wiki_url
                result_df.at[idx, f"wikipedia_language"] = language
                
                # Get images from the article
                image_titles = self.get_article_images(article_title, language, max_images=max_images)
                
                if image_titles:
                    # Get image information
                    image_info = self.get_image_info(image_titles, language)
                    
                    # Add to DataFrame
                    for i, info in enumerate(image_info):
                        if i < max_images:
                            result_df.at[idx, f"{output_col_prefix}{i+1}_url"] = info["url"]
            
            # Respect rate limits
            time.sleep(self.delay)
        
        return result_df