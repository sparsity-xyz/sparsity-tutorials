import abc

from openai import OpenAI as OA

from .support_platform_models import Platform_Model


class Platform(abc.ABC):
    name: str

    def __init__(self):
        self.support_models = Platform_Model[self.name]

    def check_support_model(self, model) -> bool:
        return model in self.support_models

    @abc.abstractmethod
    def call(self, model, message) -> (str, int):
        raise NotImplementedError


class OpenAI(Platform):
    name = "open_ai"

    def __init__(self, api_key, base_url=None):
        super().__init__()
        self.client = OA(api_key=api_key, base_url=base_url)

    def call(self, model, message) -> (str, int):
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": message},
            ],
            stream=False
        )
        return response.choices[0].message.content, response.created
