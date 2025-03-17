"""
Enter script name

Enter short description of the script
"""

__date__ = "2025-03-11"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"



# %% --------------------------------------------------------------------------
import pandas as pd
import asyncio
from typing import List, Callable
import anthropic
import nest_asyncio
import os

# Ensure nested event loops are allowed
nest_asyncio.apply()

async def process_entry(entry, client):
    try:
        message = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"I need descriptions of castles worldwide, give me a 500-1000 word summary of this castle: {entry}. Start with the city and country where the castle is located, in the format City: 'city_name', Country: 'country:name'.",
                }
            ],
        )
        return message.content[0].text
    except Exception as e:
        print(f"Error processing entry: {e}")
        return entry  # Return original text if cleaning fails


async def process_batch(
    texts: List[str], clean_func: Callable, client: str
) -> List[str]:
    """Process a batch of texts using the provided cleaning function"""
    tasks = [clean_func(text, client) for text in texts]
    return await asyncio.gather(*tasks)


async def process_dataframe(
    df: pd.DataFrame, column: str, client: str, batch_size: int = 10
) -> pd.DataFrame:
    """Process the specified column of the dataframe in batches"""
    results = []
    for i in range(0, len(df), batch_size):
        batch = df[column].iloc[i : i + batch_size].tolist()
        cleaned_batch = await process_batch(batch, process_entry, client)
        results.extend(cleaned_batch)

        # add pause between batches to avoid rate limiting
        if i < len(df) - batch_size:
            await asyncio.sleep(1)

    df["description"] = results
    return df


async def main():
    # Create an instance of the API client
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    # Create a sample dataframe
    df = pd.read_csv("outputs/missing_castles.csv")
    # combine the name and country columns
    #df['name_country'] = df['name'] + ', ' + df['country']

    # Process the dataframe
    df_cleaned = await process_dataframe(df, "name", client, batch_size=2)

    # Optionally, save the result
    df_cleaned.to_csv("outputs/llm_descriptions_missing.csv", index=False)

if __name__ == "__main__":
    asyncio.run(main())
# %%
