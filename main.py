import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You're a helpful assistant for fixing dirty data."},
        {"role": "user", "content": "The 'age' column has some missing values and negative numbers. How should I clean it?"}
    ]
)

print("\nGPT Suggestion:")
print(response['choices'][0]['message']['content'])