from telegram.ext import MessageFilter
from telegram import Message

from text_matchers import if_contains_word


class _Mention(MessageFilter):

    def filter(self, message: Message):
        return if_contains_word(message.bot.name)(message.text)


class _BotReply(MessageFilter):

    def filter(self, message: Message):
        if message.reply_to_message != None:
            return message.bot.username == message.reply_to_message.from_user.username
        return False


def mention():
    return _Mention()

def botreply():
    return _BotReply()