import subprocess

from telegram.ext import Updater, MessageHandler, Filters

from responses import *
from revbot_notifier import *
from reputation import *
from common import *
from text_generation.api import GenerationError
from userid_map import *
from filters import XiBotFilters
from text_generation.chatbot_factory import get_xi_jinping_chatbot

import conversations.good_citizen_test as GCT
import os.path as path


with open(path.join(asset_folder, 'token.txt'), 'r') as token_file:
    token = token_file.read()

updater    = Updater(token = token, use_context = True)
dispatcher = updater.dispatcher

listener = revbot_listener(updater)
listener.add_handler('name_changed', on_server_name_changed)


def command_show_reputation(update, context):
    send_reply(update, context, f'Your current Social Credit Score is {get_reputation(update):.2f}.')


def command_reset_reputation(update, context):
    reset_reputation(update)


def command_show_version(update, context):
    result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output = True)
    send_reply(update, context, f'Currently deployed XiBot version: {result.stdout.decode("utf-8")}')


def command_show_patchnotes(update, context):
    commit_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True).stdout.decode("utf-8")
    patchnotes  = read_text('patchnotes.txt').replace('${COMMIT}', commit_hash)
    send_reply(update, context, patchnotes)


def command_clear_chatbot_history(update, context):
    get_xi_jinping_chatbot().clear_history()
    send_reply(update, context, 'Huh? Where am I? What year is it?')


def text_generation_reply(update, context):
    if not config['enable_text_generation']: return

    try:
        chatbot  = get_xi_jinping_chatbot()
        message  = update.message.text.replace(update.message.bot.name, 'Xi Jinping')
        response = chatbot.generate_response(update.message.from_user.full_name, message, update)

        send_reply(update, context, response)
    except GenerationError:
        send_reply(update, context, 'I am currently too busy running our glorious country to speak to the likes of you!')


def bind_updater(fn): return lambda u, c: fn(updater, u, c)
def bind_args(fn): return lambda u, c: fn(updater, (u.effective_chat.id, c.bot.getChat(u.effective_chat.id).title))


dispatcher.add_handler(GCT.make_handler())

dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_title, bind_args(on_server_name_changed)))
dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, lambda u, c: send_reply(u, c, 'Ni Hao!')))
dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.command & ~XiBotFilters.reply_to_bot & ~XiBotFilters.mentions_bot, bind_updater(respond)))
dispatcher.add_handler(MessageHandler(Filters.all, lambda u, c: set_id(u)), group = 1)
dispatcher.add_handler(MessageHandler(XiBotFilters.reply_to_bot | XiBotFilters.mentions_bot, text_generation_reply))

add_command(dispatcher, command_show_reputation,       'show_score')
add_command(dispatcher, command_reset_reputation,      'reset_score')
add_command(dispatcher, command_show_version,          'version')
add_command(dispatcher, command_show_patchnotes,       'patchnotes')
add_command(dispatcher, command_clear_chatbot_history, 'joe_biden_moment')

load_reputations()
load_ids()

updater.start_polling()