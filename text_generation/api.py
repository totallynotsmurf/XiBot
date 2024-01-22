import os
import json
import copy
import requests
from typing import Union, overload


base_params = {
  "inputs": "",
  "parameters": {
    "best_of": 1,
    "decoder_input_details": True,
    "details": True,
    "do_sample": True,
    "max_new_tokens": 200,
    "repetition_penalty": 1.15,
    "return_full_text": False,
    "seed": None,
    "stop": [],
    "temperature": 0.7,
    "top_k": 20,
    "top_n_tokens": 1,
    "top_p": 0.95,
    "truncate": None,
    "typical_p": 0.95,
    "watermark": True,
    "ignore_eos": False
  }
}

class GenerationError(Exception):
    """Raised when generation fails."""
    pass

class GenerationBase:
    _params = copy.deepcopy(base_params)

    @overload
    def set_params(self, temperature:float=None, top_k:int=None, top_p:float=None, repitition_penalty:float=None, seed:int=None, ignore_eos:bool=False) -> None:
        """
        Change generation parameters.\n
        :param temperature: Higher value = more creative. Default: 0.7
        :param top_k: Top (value) words to choose from. Default: 20
        :param top_p: Higher value = more creative aswell (I think). Default: 0.95
        :param repitition_penalty: Higher value = less repetition. Default: 1.15
        :param seed: Generate using specific seed (Same seed will generate the same response). Default: None
        :param ignore_eos: Ignore 'End of sequence' token (Does not stop if eos token is generated). Default: False
        :return: None
        """

    def set_params(self, **kwargs):
        temp = kwargs.get("temperature")
        if temp != None:
            if temp > 1000:
                kwargs["temperature"] = 1000
            if temp <= 0:
                kwargs["temperature"] = 0.01
        for k, v in kwargs.items():
            if k in self._params["parameters"]:
                self._params["parameters"][k] = v

    def params_default(self):
        """
        Set generation parameters back to default.\n
        :return: None
        """
        self._params = copy.deepcopy(base_params)

class ChatBot(GenerationBase):
    def __init__(self, ai_name, context, url, headers, format="dolphin", messages=[], start_messages=[]):
        self.ai_name = ai_name
        self.context = context
        self.messages = messages
        self.start_messages = start_messages


        self._url = url
        self._generate_url = f"{url}/tgi/generate" if headers != None else f"{url}/generate"
        self._headers = headers
        self._format = format

    def send_message(self, username, message:str, max_new_tokens: int=200):
        """
        Send a message to the chatbot.\n
        :param username: Senders name
        :param message: Message you want to send to the chatbot
        :param max_new_tokens: Max tokens to generate (One word = 1 token, special characters also count as one token)
        :return: Returns generated response
        """
        self._append_message(username, message)

        params = copy.deepcopy(self._params)
        params["parameters"]["max_new_tokens"] = max_new_tokens
        while True:
            messages = self._format_messages(self.start_messages)
            messages.extend(self._format_messages(self.messages))

            prompt = self._make_prompt(messages)
            params["inputs"] = prompt
            result = requests.post(self._generate_url, json=params, headers=self._headers)
            result_json = result.json()
            error = result_json.get("error")
            if error:
                if error.startswith("Input validation error: `inputs`"):
                    self.messages.pop(0)
                else:
                    raise GenerationError(f"Generation Error: {error}")
            else:
                break
        result_text = result_json.get("generated_text")
        self._append_message(self.ai_name, result_text)
        return result_text

    def system_message(self, message:str):
        self.messages.append({"name": "system", "content": message})

    def reset(self):
        """
        Resets chat history\n
        :return: None
        """
        self.messages.clear()

    def _format_messages_dolphin(self, messages):
        formatted = []
        for message in messages:
            message_str = f"<|im_start|>{message['name']}\n{message['content']}<|im_end|>"
            formatted.append(message_str)
        return formatted

    def _format_messages_llama(self, messages):
        formatted = []
        for message in messages:
            message_str = f"<s>{message['name']}: {message['content']}</s>"
            formatted.append(message_str)
        return formatted

    def _format_messages_default(self, messages):
        formatted = []
        for message in messages:
            message_str = f"{message['name']}: {message['content']}"
            formatted.append(message_str)
        return formatted

    def _format_messages(self, messages):
        if self._format == "dolphin":
            format_func = self._format_messages_dolphin
        elif self._format == "llama":
            format_func = self._format_messages_llama
        else:
            format_func = self._format_messages_default
        return format_func(messages)

    def _append_message(self, name: str, content: str):
        self.messages.append({"name": name, "content": content})

    def _append_start_message(self, name: str, content: str):
        self.start_messages.append({"name": name, "content": content})

    def _make_prompt(self, messages: list):
        if self._format == "dolphin":
            ai_start = f"<|im_start|>{self.ai_name}\n"
        elif self._format == "llama":
            ai_start = f"<s>{self.ai_name}:"
        else:
            ai_start = f"{self.ai_name}:"
        message_history = "\n".join(messages)
        prompt = f"{self.context}\n{message_history}\n{ai_start}"
        return prompt

class API:
    def __init__(self, url, username, api_key):
        self._url = url
        self._headers = {"Username": username, "API-KEY": api_key} if username and api_key else None

    def create_chatbot(self, ai_name, context, format="dolphin", messages=[]):
        """
        Creates a chatbot object that you can send messages to.\n
        :param ai_name: Character name
        :param context: Character description
        :param format: Message formats, avialable: llama, dolphin
        :param messages: A list of messages
        :return: Chatbot object
        """
        return ChatBot(ai_name, context, self._url, self._headers, format, messages)

    def load_chatbot(self, file_path: str):
        """
        Loads saved chatbot from file.\n
        :param file_path: Path to saved chatbot
        :return: Chatbot object
        """
        if not file_path.endswith(".json"):
            file_path += ".json"

        bot_data = json.load(open(file_path, "r", encoding='utf-8'))
        return ChatBot(url=self._url, headers=self._headers, **bot_data)