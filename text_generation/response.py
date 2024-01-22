import os

from telegram import Update
from text_generation.api import API

from responses import change_score, get_reputation
from common import asset_folder, config


api_key_file = f"{asset_folder}/api_key.txt"

if os.path.isfile(api_key_file):
    api_key = open(api_key_file, "r", encoding='utf-8').read()
else:
    api_key = ""

personality_file = f"{asset_folder}/gpt_personality.json"

api_config = {"url": config["tgi_url"], "username": config["api_username"], "api_key": api_key}
api = API(**api_config)
xi_bot = api.load_chatbot(personality_file)
xi_bot.set_params(temperature=config["temperature"])


# Convert string to negative value
def deduct(value):
    value = -int(value)
    if value < -100:
        value = -100
    return value


# Convert string to value
def grant(value):
    value = int(value)
    if value > 100:
        value = 100
    return value


available_functions = {"grant_social_credit": grant, "deduct_social_credit": deduct}


# Run social credit functions
def run_function(function, update):
    function = function.replace("{", "").replace("}", "")
    if ":" in function:
        name, value = function.split(":", 1)
        name = name.strip()
        value = value.strip()
        if name in available_functions and value.isdigit():
            amount = available_functions[name](value)
            change_score(amount, amount)(update)


# Find functions in response
def find_functions(response, update):
    for func in available_functions:
        func_string = "{" + func
        if func_string in response:
            start = response.find(func_string)
            stop = response[start:].find("}") + len(response[:start]) + 1 if "}" in response else len(response)
            func_data = response[start:stop]
            run_function(func_data, update)
            response = response.replace(func_data, "")
    return response.strip()


# Generate text response
def generate_response(update: Update, context):
    message = update.message
    username = message.from_user.username
    if username:
        username = username.replace("@", "")
    else:
        username = message.from_user.full_name
    try:
        social_credits = get_reputation(update)
        social_credit_message = f"{username} has {str(social_credits)} social credits."
        text = message.text.replace(message.bot.name, f"Xi Jinping")
        xi_bot.system_message(social_credit_message)
        result = xi_bot.send_message(username, text, max_new_tokens=config["max_new_tokens"])
        cleaned = find_functions(result, update)
        message.reply_text(cleaned)
    except:
        pass