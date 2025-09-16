import os, traceback
from openai import OpenAI

print("KEY_PRESENT:", bool(os.getenv("OPENAI_API_KEY")))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    r = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
        messages=[{"role":"user","content":"Say hi in 3 words."}],
        max_tokens=10,
    )
    print("RESULT:", r.choices[0].message.content)
except Exception as e:
    traceback.print_exc()
