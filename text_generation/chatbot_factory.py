from reputation import update_reputation
from text_generation.api import ChatBotAPI

from responses import get_reputation
from common import asset_folder, config, api_auth_config, clamp


class ChatbotFactory:
    def __init__(self):
        if not api_auth_config:
            print(
                "Text generation is enabled in the configuration but no API configuration file was found. Text generation will not be enabled for this session.\n"
                "Please provide the file assets/api_auth.json with the following keys to enable text generation: api_key, url, username.\n"
                "The fields api_key and username may be omitted if the service at the provided URL does not require them."
            )

            return

        self.api       = ChatBotAPI(**api_auth_config)
        self.instances = {}


    def create_chatbot(self, personality, functions = (), message_headers = ()):
        if not hasattr(self, 'api'): raise RuntimeError('Text generation is not enabled.')

        bot = self.api.load_chatbot(f'{asset_folder}/personality.{personality}.json')
        bot.set_params(temperature = config['temperature'], max_new_tokens = config['max_new_tokens'])

        for pattern, handler in functions:
            bot.define_function(pattern, handler)

        for handler in message_headers:
            bot.define_message_header_function(handler)

        self.instances[personality] = bot
        return bot


    def create_or_get_chatbot(self, personality, functions = (), message_headers = ()):
        if personality in self.instances:
            return self.instances[personality]
        else:
            return self.create_chatbot(personality, functions, message_headers)


chatbot_factory = ChatbotFactory()


def get_xi_jinping_chatbot():
    def grant_social_credit(match, response, update):
        try: value = int(match.group(1))
        except: return

        update_reputation(+clamp(abs(value), 0, 100), update)

    def deduct_social_credit(match, response, update):
        try: value = int(match.group(1))
        except: return

        update_reputation(-clamp(abs(value), 0, 100), update)

    def describe_user(update):
        return f'{update.message.from_user.full_name} currently has {str(get_reputation(update))} social credits.'


    return chatbot_factory.create_or_get_chatbot(
        'xi_jinping',
        [
            ("{grant_social_credit:(.+)}", grant_social_credit),
            ("{deduct_social_credit:(.+)}", deduct_social_credit)
        ],
        [ describe_user ]
    )