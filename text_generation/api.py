import json
import copy
import re

import requests

from common import clamp


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
    pass


class GenerationBase:
    def __init__(self):
        self.params = copy.deepcopy(base_params)


    def set_params(self, **kwargs):
        if "temperature" in kwargs:
            kwargs["temperature"] = clamp(kwargs["temperature"], 0.01, 1000.0)

        self.params["parameters"].update(kwargs)


    def reset_params(self):
        self.params = copy.deepcopy(base_params)


class ChatBot(GenerationBase):
    def __init__(self, bot_name, context, url, headers = None, format = "dolphin", messages = None, start_messages = None):
        super().__init__()

        self.bot_name        = bot_name
        self.context         = context
        self.messages        = messages if messages is not None else []
        self.start_messages  = start_messages if start_messages is not None else []
        self.url             = url
        self.generate_url    = f"{url}/tgi/generate" if headers is not None else f"{url}/generate"
        self.headers         = headers
        self.format          = format
        self.functions       = []
        self.message_headers = []


    def define_function(self, match, handler):
        """
        Defines a function that can be invoked by the bot when it produces text matching the given regex.
        Handler should be invocable as f(match, response_text, telegram_update) -> None
        """
        self.functions.append((match, handler))


    def define_message_header_function(self, handler):
        """
        Defines a generator for a piece of text that will be inserted into the message history before calling generate_response.
        Handler should be invocable as f(telegram_update) -> str
        """
        self.message_headers.append(handler)


    def generate_response(self, username, message, update, max_new_tokens = None, can_run_functions = True):
        for handler in self.message_headers:
            self.send_system_message(handler(update))

        self._append_message(username, message)


        request_params = copy.deepcopy(self.params)
        if max_new_tokens is not None: request_params["parameters"]["max_new_tokens"] = max_new_tokens


        while True:
            formatted_messages = self._format_messages(self.start_messages)
            formatted_messages.extend(self._format_messages(self.messages))

            request_params["inputs"] = self._make_prompt(formatted_messages)
            result_json              = requests.post(self.generate_url, json = request_params, headers = self.headers).json()
            error                    = result_json.get("error")


            if not error:
                result_text = result_json.get("generated_text")
                self._append_message(self.bot_name, result_text)

                if can_run_functions:
                    # Run twice so we can call handlers with unprocessed text.
                    for pattern, handler in self.functions:
                        matches = re.findall(pattern, result_text)
                        for match in matches: handler(match, result_text, update)

                    for pattern, handler in self.functions:
                        result_text = re.sub(pattern, '', result_text)

                return result_text
            else:
                # Input validation error is returned if the input contains too many tokens
                # so just forget the least recent item in our history.
                if error.startswith("Input validation error: `inputs`"): self.messages.pop(0)
                else: raise GenerationError(f"Generation Error: {error}")


    def send_system_message(self, message:str):
        self.messages.append({"name": "system", "content": message})


    def clear_history(self):
        self.messages.clear()


    def _format_messages(self, messages):
        message_formats = {
            'dolphin': '<|im_start|>{name}\n{content}<|im_end|>',
            'llama':   '<s>{name}: {content}</s>',
            'default': '{name}: {content}'
        }

        format_string = message_formats[self.format] if self.format in message_formats else message_formats['default']


        return list(map(
            lambda message: format_string.format(name = message['name'], content = message['content']),
            messages
        ))


    def _append_message(self, name: str, content: str):
        self.messages.append({"name": name, "content": content})


    def _append_start_message(self, name: str, content: str):
        self.start_messages.append({"name": name, "content": content})


    def _make_prompt(self, messages: list):
        message_prepend = {
            'dolphin': '<|im_start|>',
            'llama':   '<s>',
            'default': ''
        }

        prepend = message_prepend[self.format] if self.format in message_prepend else message_prepend['default']
        history = '\n'.join(messages)

        return f'{self.context}\n{history}\n{prepend}{self.bot_name}\n'


class ChatBotAPI:
    def __init__(self, url, username = None, api_key = None):
        self.url     = url
        self.headers = {}

        if username is not None: self.headers["Username"] = username
        if api_key  is not None: self.headers["API-KEY"]  = api_key


    def create_chatbot(self, bot_name, context, format = "dolphin", messages = None):
        return ChatBot(bot_name, context, self.url, self.headers, format, messages)


    def load_chatbot(self, file_path: str):
        if not file_path.endswith(".json"): file_path += ".json"

        bot_data = json.load(open(file_path, "r"))
        return ChatBot(url=self.url, headers=self.headers, **bot_data)