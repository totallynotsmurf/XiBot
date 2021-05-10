import types
from typing import Union, Callable

from common import *
from text_matchers import *
from reputation import *

import re
import random
import time


# Make the message lower case, remove special characters and repeated whitespace and transform all whitespace
# characters to a single space.
def normalize_message(message):
    message = message.lower()

    transformed_message = []
    for i, char in enumerate(message):
        # Keep all alphanumeric characters as is.
        if char.isalnum():
            transformed_message.append(char)
            continue

        # Remove excess whitespace.
        if char.isspace():
            # Keep whitespace (transforming it to ' ') if the next character isn't a space.
            if i + 1 >= len(message) or not message[i + 1].isspace():
                transformed_message.append(' ')

    return ''.join(transformed_message)


prc_regex = r'people\s?s?\s?repu?b?l?i?c? of china'
roc_regex = r'repu?b?l?i?c? of china'

# TODO: Optimize this.
# Note: this only checks if the string has 'Republic of China' and not 'People's Republic of China'
# Taiwan, ROC, etc. should be checked separately.
def mentions_roc(string):
    # If the message mentions 'republic of china' and not 'people's republic of china' it is talking about the ROC.
    # If the message mentions both, figure out if the ROC mention is a substring of the PRC mention.
    if if_matches(roc_regex)(string):
        if not mentions_prc(string): return True
        else: return len(re.findall(prc_regex, string)) != len(re.findall(roc_regex, string))



def mentions_prc(string):
    return if_matches(prc_regex)(string)


def score_changed_message(amount):
    return f'Your Social Credit Score has been {"raised" if amount > 0 else "lowered"} by {str(abs(amount))} points.'

def update_score(update, a, b, message: Union[str, Callable] = score_changed_message):
    amount = random.randint(min(a, b), max(a, b))
    update_reputation(amount, update)

    if isinstance(message, str): return message
    else: return message(amount)


response_map = [
    (
        logical_and(
            if_contains('uyghur', 'uygur', 'uyguhr'),
            if_contains('autonomous', 'autonomy', 'rebel', 'independence', 'freedom', 'free the')
        ),
        lambda _: 'There is no war in B̶a̶ ̶S̶i̶n̶g̶ ̶S̶e̶ The Xinjiang Autonomous Area.'
    ),
    (
        logical_or(
            if_contains(
                'tianman', 'tianmen', 'tiananman', 'tiananmen', 'tibet', 'hong kong', 'hongkong',
                'uyghur', 'uygur', 'uyguhr', 'human right', 'xinjiang', 'xiaobo'
            ),
            if_contains_word(
                '1989', 'dalai', 'pooh'
            )
        ),
        lambda update: update_score(update, -25, -100)
    ),
    (
        logical_and(
            logical_or(
                if_contains('communis', 'jinping'),
                if_contains_word('mao', 'ccp')
            ),
            logical_not(if_contains('capitalis')),
            sentiment_more_than(0.2)
        ),
        lambda update: update_score(update, 25, 50)
    ),
    (
        logical_and(
            logical_or(
                if_contains('communis', 'jinping'),
                if_contains_word('mao', 'ccp')
            ),
            logical_not(if_contains('capitalis')),
            sentiment_less_than(-0.2)
        ),
        lambda update: update_score(update, -25, -100)
    ),
    (
        # Takes priority over other ROC mentions.
        if_matches(r'taiwan numb[a|e]r? [(one)|1]'),
        lambda update: update_score(update, -250, -500, 'This is by far the most disgusting thing I\'ve read all day.')
    ),
    (
        logical_or(
            if_contains('mad dog', 'xiaodong'),
            if_contains_word('ching', 'chong', 'chink')
        ),
        lambda update: update_score(update, -25, -50, 'Please cease disrespecting Chinese culture immediately.')
    ),
    (
        logical_or(if_contains('taiwan'), if_contains_word('roc'), mentions_roc),
        lambda update: update_score(update, -25, -50, 'There is only one China. Always has been.')
    ),
    (
        if_contains('jinping'),
        lambda update: update_score(update, 5, 10, 'Ni Hao!')
    ),
    (
        logical_or(
            if_contains('iphone', 'ipad', 'ipod', 'imac', 'macbook', 'foxconn', 'samsung', 'huawei', 'xiaomi', 'oneplus'),
            if_contains_word('i phone', 'i pad', 'i pod', 'i mac')
        ),
        lambda _: '<image>iphone_factory.jpg'
    ),
    (
        mentions_prc,
        lambda update: update_score(update, 50, 100, 'Long live the Communist Party, long live our Glorious Homeland!')
    ),
    (
        if_contains('china sea', 'chinese sea'),
        lambda _: 'Rightful Chinese territory! It\'s in the name!'
    ),
    (
        if_contains_word('twitter', 'facebook', 'instagram', 'snapchat', 'whatsapp', 'telegram', 'discord'),
        lambda _: 'Did you mean WeChat?'
    ),
    (
        if_contains('amazon'),
        lambda _: 'Did you mean Alibaba?'
    ),
    (
        if_contains('corona', 'covid', 'wuhan', 'bat soup', 'bat soop'),
        lambda update: update_score(update, -100, -200, 'There is nothing going on in Wuhan. Please mind your own business.')
    ),
    (
        if_contains('capitalis'),
        lambda update: update_score(update, -20, -50, 'Capitalism bad.')
    ),
    (
        logical_or(if_contains('otter'), if_contains_word('otta', 'ottas')),
        lambda update: update_score(update, 5, 10, '<image>commie.jpg')
    )
]

def process_message(update):
    message = normalize_message(update.message.text)

    for matcher, response in response_map:
        if matcher(message): return response(update)

    return None



def respond(updater, update, context):
    text = update.message.text
    if text is None: return


    response = process_message(update)
    if response is not None:
        if response.startswith('<image>'):
            send_image_reply(update, context, response[len('<image>'):])
        else:
            send_reply(update, context, response)

