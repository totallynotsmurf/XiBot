from telegram.ext import Updater, MessageHandler, Filters

from responses import *
from revbot_notifier import *

import os
import os.path as path


with open(path.join(asset_folder, 'token.txt'), 'r') as token_file:
    token = token_file.read()

updater    = Updater(token = token, use_context = True)
dispatcher = updater.dispatcher

listener = revbot_listener(updater)
listener.add_handler('name_changed', on_server_name_changed)


def bind_updater(fn): return lambda u, c: fn(updater, u, c)
def bind_args(fn): return lambda u, c: fn(updater, (u.effective_chat.id, c.bot.getChat(u.effective_chat.id).title))


dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_title, bind_args(on_server_name_changed)))
dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, lambda u, c: send_reply(u, c, 'Ni Hao!')))
dispatcher.add_handler(MessageHandler(Filters.all, bind_updater(respond)))

updater.start_polling()