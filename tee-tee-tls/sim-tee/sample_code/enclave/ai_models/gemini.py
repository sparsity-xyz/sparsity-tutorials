
from google import genai

from .open_ai import Platform


class Gemini(Platform):
    name = "gemini"
    def __init__(self, api_key):
        super().__init__()
        self.client = genai.Client(api_key=api_key)

    def call(self, model, message) -> (str, int):
        response = self.client.models.generate_content(
            model=model, contents=message
        )
        return response.candidates[0].content.parts[0].text, int(response.create_time.timestamp())
