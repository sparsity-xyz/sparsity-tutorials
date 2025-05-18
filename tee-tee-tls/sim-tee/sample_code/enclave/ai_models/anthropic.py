import time

from anthropic import Anthropic as An

from .open_ai import Platform


class Anthropic(Platform):
    name = "anthropic"

    def __init__(self, api_key):
        super().__init__()
        self.client = An(api_key=api_key)

    def call(self, model, message) -> (str, int):
        response = self.client.messages.create(
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
            model=model,
        )
        return response.content[0].text, int(time.time())
