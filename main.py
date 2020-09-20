from telegram.ext import Updater, MessageHandler, Filters

from common import *
from responses import *

import os
import os.path as path


with open(path.join(asset_folder, 'token.txt'), 'r') as token_file:
    token = token_file.read()

updater    = Updater(token = token, use_context = True)
dispatcher = updater.dispatcher


def on_chat_name_changed(update, context):
    name = updater.bot.getChat(update.effective_chat.id).title.lower()

    def any_in_name(*strings):
        return any([s in name for s in list(strings)])


    if any_in_name('communis', 'marx', 'lenin', 'stalin', 'jinping'):
        send_image_reply(update, context, 'happy_xi.jpg')
    elif any_in_name('uyghur', 'capitalis'):
        send_image_reply(update, context, 'sad_xi.jpg')



dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_title, on_chat_name_changed))
dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, lambda u, c: send_reply(u, c, 'Ni Hao!')))
dispatcher.add_handler(MessageHandler(Filters.all, respond))

updater.start_polling()