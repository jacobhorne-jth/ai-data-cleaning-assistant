import openai
import os
from dotenv import load_dotenv

# Load your OpenAI key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_cleaning_advice(column_name, stats):
    # Build GPT prompt
    system_msg = "You are a data cleaning assistant. Given a column's stats and sample values, suggest how to clean it."

    user_msg = f"""Here is a column called '{column_name}'.

Stats:
- Type: {stats.get("dtype")}
- Missing values: {stats.get("missing_values")}
- Duplicates: {stats.get("num_duplicates")}
- Unique values: {stats.get("num_unique")}

Sample values: {stats.get("sample_values")}

What kind of data is this, and how would you clean it? Be specific and explain each step."""

    # Send to GPT
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
    )

    reply = response["choices"][0]["message"]["content"]
    return reply

# Example test (delete this in final version)
if __name__ == "__main__":
    sample = {
        "dtype": "object",
        "missing_values": 1,
        "num_duplicates": 2,
        "num_unique": 5,
        "sample_values": ["alice@example.com", "bob[at]email.com", "charlie@email.com"]
    }

    print(get_cleaning_advice("email", sample))