import json
from file_manager import file_manager

from telegram import InputFile
from telegram.ext import CommandHandler

from os import path


def try_load_config(config_path, required_keys = ()):
    contents = json.load(open(config_path, 'r')) if path.exists(config_path) else None

    if contents is not None:
        for key in required_keys:
            if key not in contents:
                print(f'Configuration file {config_path} is missing required key {key} and will not be used.')
                return None

    return contents


asset_folder     = './assets/'
file_id_manager = file_manager(asset_folder)

config_path     = f"{asset_folder}/config.json"
api_auth_path   = f"{asset_folder}/api_auth.json"

config          = try_load_config(config_path, { 'enable_text_generation', 'temperature', 'max_new_tokens' })
api_auth_config = try_load_config(api_auth_path, { 'url' })

if not api_auth_config: config['enable_text_generation'] = False


def nth(n): return lambda arr: arr[n]


def clamp(x, lower, upper): max(min(x, upper), lower)


def display_user(user):
    if user.first_name is not None: return user.first_name
    if user.username is not None: return user.username
    return "user"


def read_text(filename):
    with open(path.join(asset_folder, filename), 'r', encoding = 'utf-8') as handle:
        return ''.join(handle.readlines()).replace('\r\n', '\n')


def send_reply(update, context, message):
    update.message.reply_text(message)


def send_message(update, context, message):
    context.bot.send_message(chat_id = update.effective_chat.id, text = message)


def send_image_reply(update, context, image_name):
    with open(path.join(asset_folder, image_name), 'rb') as image_file:
        update.message.reply_photo(image_file)


def send_image_message(updater, chat_id, image_name, caption = None):
    with open(path.join(asset_folder, image_name), 'rb') as image_file:
        updater.bot.send_photo(chat_id, image_file, caption = caption)


def send_image_message_with_context(update, context, image_name, caption = None):
    with open(path.join(asset_folder, image_name), 'rb') as image_file:
        context.bot.send_photo(update.effective_chat.id, image_file, caption = caption)


def send_reply_cached(update, context, file_name, send_fn, get_id_fn):
    # Attempt to send the file from the file id if it exists.
    if file_name in file_id_manager.id_map:
        try:
            # Throws an exception if Telegram decides it doesn't like the file ID anymore for some stupid reason.
            send_fn(update, context, file_id_manager.id_map[file_name])
            return
        except:
            print(f'Resending file {file_name} because Telegram decided it doesn\'t like the old ID anymore...')
            pass

    # If that fails, upload the file and store the file ID for later.
    with open(path.join(asset_folder, file_name), 'rb') as file:
        response = send_fn(update, context, file)
        file_id_manager.store(file_name, get_id_fn(response))


def send_video_reply(update, context, video_name):
    send_reply_cached(
        update,
        context,
        video_name,
        lambda u, c, f: u.message.reply_video(f),
        lambda m: m.video.file_id
    )


def send_audio_reply(update, context, audio_name):
    send_reply_cached(
        update,
        context,
        audio_name,
        lambda u, c, f: u.message.reply_audio(f),
        lambda m: m.audio.file_id
    )


def string_find_all(string, substring):
    result = []

    last_match = string.find(substring, 0)
    while last_match != -1:
        result.append(last_match)
        last_match = string.find(substring, last_match + 1)

    return result


def add_command(dispatcher, command, name):
    handler = CommandHandler(name, command)
    dispatcher.add_handler(handler)