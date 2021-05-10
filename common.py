from telegram import InputFile

from os import path

from telegram.ext import CommandHandler

asset_folder = './assets/'


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