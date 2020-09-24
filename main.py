from telegram.ext import Updater, MessageHandler, Filters

from common import *
from responses import *

import os
import os.path as path


with open(path.join(asset_folder, 'token.txt'), 'r') as token_file:
    token = token_file.read()

updater    = Updater(token = token, use_context = True)
dispatcher = updater.dispatcher


def bind_updater(fn): return lambda u, c: fn(updater, u, c)

dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_title, bind_updater(on_chat_name_changed)))
dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, lambda u, c: send_reply(u, c, 'Ni Hao!')))
dispatcher.add_handler(MessageHandler(Filters.all, bind_updater(respond)))

updater.start_polling()