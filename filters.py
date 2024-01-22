from telegram.ext import MessageFilter, BaseFilter
from telegram import MessageEntity, Message
from telegram import User as TGUser
from typing import Union, Iterable, Collection, TypeVar


RT = TypeVar("RT")
SCT = Union[RT, Collection[RT]]

# Copy-paste from the latest release of python-telegram-bot package
class _Mention(MessageFilter):
    """Messages containing mentions of specified users or chats.

    Examples:
        .. code-block:: python

            MessageHandler(filters.Mention("username"), callback)
            MessageHandler(filters.Mention(["@username", 123456]), callback)

    .. versionadded:: 20.7

    Args:
        mentions (:obj:`int` | :obj:`str` | :class:`telegram.User` | Collection[:obj:`int` | \
            :obj:`str` | :class:`telegram.User`]):
            Specifies the users and chats to filter for. Messages that do not mention at least one
            of the specified users or chats will not be handled. Leading ``'@'`` s in usernames
            will be discarded.
    """

    __slots__ = ("_mentions",)

    def __init__(self, mentions: SCT[Union[int, str, TGUser]]):
        super().__init__()
        if isinstance(mentions, Iterable) and not isinstance(mentions, str):
            self._mentions = {self._fix_mention_username(mention) for mention in mentions}
        else:
            self._mentions = {self._fix_mention_username(mentions)}

    @staticmethod
    def _fix_mention_username(mention: Union[int, str, TGUser]) -> Union[int, str, TGUser]:
        if not isinstance(mention, str):
            return mention
        return mention.lstrip("@")

    @classmethod
    def _check_mention(cls, message: Message, mention: Union[int, str, TGUser]) -> bool:
        if not message.entities:
            return False

        entity_texts = message.parse_entities(
            types=[MessageEntity.MENTION, MessageEntity.TEXT_MENTION]
        )

        if isinstance(mention, TGUser):
            return any(
                mention.id == entity.user.id
                or mention.username == entity.user.username
                or mention.username == cls._fix_mention_username(entity_texts[entity])
                for entity in message.entities
                if entity.user
            ) or any(
                mention.username == cls._fix_mention_username(entity_text)
                for entity_text in entity_texts.values()
            )
        if isinstance(mention, int):
            return bool(
                any(mention == entity.user.id for entity in message.entities if entity.user)
            )
        return any(
            mention == cls._fix_mention_username(entity_text)
            for entity_text in entity_texts.values()
        )

    def filter(self, message: Message) -> bool:
        return any(self._check_mention(message, mention) for mention in self._mentions)


class _BotReply(MessageFilter):

    def filter(self, message: Message):
        if message.reply_to_message != None:
            return bool(message.bot.username == message.reply_to_message.from_user.username)
        return False


def mention(mentions):
    return _Mention(mentions)

def botreply():
    return _BotReply()