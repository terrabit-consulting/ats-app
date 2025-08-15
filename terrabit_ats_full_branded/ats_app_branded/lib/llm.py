# lib/llm.py
import time

# Support both OpenAI SDK v1.x and older 0.x
try:
    from openai import OpenAI  # v1.x
    _SDK = "v1"
except Exception:
    _SDK = "v0"
    import openai as _oai  # v0.x

class LLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o", temperature: float = 0):
        self.model = model
        self.temperature = temperature
        self.sdk = _SDK
        if self.sdk == "v1":
            # v1.x client
            self.client = OpenAI(api_key=api_key)
        else:
            # v0.x fallback
            _oai.api_key = api_key
            self.client = _oai

    def chat(self, prompt: str, retries: int = 1):
        text, _ = self.chat_with_usage(prompt, retries=retries)
        return text

    def chat_with_usage(self, prompt: str, retries: int = 1):
        err = None
        for _ in range(retries + 1):
            try:
                if self.sdk == "v1":
                    r = self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=self.temperature,
                    )
                    text = r.choices[0].message.content.strip()
                    usage = getattr(r, "usage", None)
                    if usage:
                        return text, {
                            "input_tokens": getattr(usage, "prompt_tokens", 0),
                            "output_tokens": getattr(usage, "completion_tokens", 0),
                        }
                    return text, None
                else:
                    r = self.client.ChatCompletion.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=self.temperature,
                    )
                    text = r["choices"][0]["message"]["content"].strip()
                    usage = r.get("usage", None)
                    if usage:
                        return text, {
                            "input_tokens": usage.get("prompt_tokens", 0),
                            "output_tokens": usage.get("completion_tokens", 0),
                        }
                    return text, None
            except Exception as e:
                err = e
                time.sleep(0.6)
        raise RuntimeError(err)
