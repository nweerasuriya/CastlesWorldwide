"""
A script that processes a CSV file of castle data using OpenAI to classify each entry
as a castle, a different structure type (e.g. palace), or to be removed if invalid.
"""

__date__ = "2025-03-13"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.2"

# %% --------------------------------------------------------------------------
import pandas as pd
import asyncio
from typing import List, Callable
from openai import AsyncOpenAI
import nest_asyncio
import random
import os

# Ensure nested event loops are allowed
nest_asyncio.apply()

async def process_entry(entry, client):
    name, country, city = entry
    
    try:
        await asyncio.sleep(random.uniform(0.1, 0.5))
        response = await client.chat.completions.create(
            model="gpt-4o",  # Or another OpenAI model of your choice
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that determines if a structure is a castle, another type of structure (like a palace, fortress, etc.), or not a real structure at all."
                },
                {
                    "role": "user",
                    "content": f"Given this structure name: '{name}', located in {city}, {country}, determine if it is: \n1. If it is simply ruins, a motte or not a real structure or invalid entry (respond with 'to be Removed').\n 2. Not a castle but another type of structure like a palace, fortress, etc. (respond with the accurate type, e.g. 'palace', 'fortress')\n 3. A castle (respond with 'castle')\n Also in the case where the name is incorrect or is not the common name for this castle, then return the correct or more common name\n\nRespond with ONLY ONE WORD or the castle name."
                }
            ],
            max_tokens=50
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"Error processing entry {name}: {e}")
        return "error - to be Removed"  # Return error indicator if processing fails


async def process_batch(
    entries: List[tuple], process_func: Callable, client
) -> List[str]:
    """Process a batch of entries using the provided function"""
    tasks = [process_func(entry, client) for entry in entries]
    return await asyncio.gather(*tasks)


async def process_dataframe(
    df: pd.DataFrame, client, batch_size: int = 10
) -> pd.DataFrame:
    """Process the dataframe in batches"""
    results = []
    total_entries = len(df)
    
    for i in range(0, len(df), batch_size):
        batch = [(row['name'], row['country'], row['city']) 
                 for _, row in df.iloc[i:i+batch_size].iterrows()]
        
        processed_batch = await process_batch(batch, process_entry, client)
        results.extend(processed_batch)

        # Add a pause between batches to avoid rate limits
        if i + batch_size < total_entries:
            await asyncio.sleep(1)

    df["structure_type"] = results
    return df


async def main():
    # Create an instance of the OpenAI client
    client = AsyncOpenAI(api_key=os.getenv("ANTHROPIC_API_KEY"))    
    # Load the dataframe
    df = pd.read_csv("outputs/cleaned_castle_data.csv")

    
    # Process the dataframe
    df_processed = await process_dataframe(df[1001:], client, batch_size=3)
    
    # Optionally, save the result
    df_processed.to_csv("outputs/classified_castles_rest.csv", index=False)
    
    # Print summary of classifications
    type_counts = df_processed['structure_type'].value_counts()
    print("\nClassification summary:")
    print(type_counts)
    
    # Count entries to be removed
    to_remove = sum(df_processed['structure_type'] == 'to be removed')
    print(f"\nEntries marked for removal: {to_remove}")


if __name__ == "__main__":
    asyncio.run(main())
# %%