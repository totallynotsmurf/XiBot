from telegram import InputFile

from os import path

from telegram.ext import CommandHandler

asset_folder = './assets/'


def nth(n): return lambda arr: arr[n]


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


def send_image_message(updater, chat_id, image_name):
    with open(path.join(asset_folder, image_name), 'rb') as image_file:
        updater.bot.send_photo(chat_id, image_file)


def send_video_reply(update, context, video_name):
    with open(path.join(asset_folder, video_name), 'rb') as video_file:
        update.message.reply_video(video_file)


def send_audio_reply(update, context, audio_name):
    with open(path.join(asset_folder, audio_name), 'rb') as audio_file:
        update.message.reply_audio(audio_file)


def send_video_reply_from_id(update, context, video_id):
    update.message.reply_video(video_id)


def send_audio_reply_from_id(update, context, audio_id):
    update.message.reply_audio(audio_id)


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