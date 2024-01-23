from telegram.ext import MessageFilter
from telegram import Message

from text_matchers import if_contains_word


class MentionBot(MessageFilter):
    """Filter to match mentions of the bot."""

    def filter(self, message: Message):
        return if_contains_word(message.bot.name)(message.text)


class BotReply(MessageFilter):
    """Filter to match replies to a bot message."""

    def filter(self, message: Message):
        if message.reply_to_message is not None:
            return message.bot.username == message.reply_to_message.from_user.username

        return False


class XiBotFilters:
    mentions_bot = MentionBot()
    reply_to_bot = BotReply()