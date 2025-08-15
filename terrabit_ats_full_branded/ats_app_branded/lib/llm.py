import openai, time

class LLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o", temperature: float = 0):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def chat(self, prompt: str, retries: int = 1):
        err = None
        for _ in range(retries+1):
            try:
                r = self.client.chat.completions.create(
                    model=self.model, messages=[{"role":"user","content":prompt}], temperature=self.temperature
                )
                return r.choices[0].message.content.strip()
            except Exception as e:
                err = e; time.sleep(0.6)
        raise RuntimeError(err)

    def chat_with_usage(self, prompt: str, retries: int = 1):
        err = None
        for _ in range(retries+1):
            try:
                r = self.client.chat.completions.create(
                    model=self.model, messages=[{"role":"user","content":prompt}], temperature=self.temperature
                )
                text = r.choices[0].message.content.strip()
                usage = getattr(r, "usage", None)
                if usage:
                    try:
                        return text, {"input_tokens": usage.prompt_tokens, "output_tokens": usage.completion_tokens}
                    except Exception:
                        return text, None
                return text, None
            except Exception as e:
                err = e; time.sleep(0.6)
        raise RuntimeError(err)
