from openai import OpenAI

# Initialize the client with your API key
client = OpenAI(api_key="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")

# Ask a question
response = client.chat.completions.create(
    model="gpt-4o-mini",   # you can also use "gpt-4.1", "gpt-3.5-turbo", etc.
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is AI in a sentence?"}
    ]
)

# Print the answer
print(response.choices[0].message.content)
