import os
import traceback
import pytest
from openai import OpenAI

KEY = os.getenv("OPENAI_API_KEY")


@pytest.mark.skipif(
    not KEY, reason="OPENAI_API_KEY not set; skipping external API test"
)
def test_openai_chat_minimal():
    client = OpenAI(api_key=KEY)
    try:
        r = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": "Say hi in 3 words."}],
            max_tokens=10,
        )
        assert r.choices and r.choices[0].message.content
    except Exception:
        traceback.print_exc()
        pytest.fail("OpenAI API call failed unexpectedly")
