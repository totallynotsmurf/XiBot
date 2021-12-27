import numbers
import types
from typing import Union, Callable, List, Tuple

from common import *
from text_matchers import *
from reputation import *

import re
import random
import time


# Select a random response from a list of responses ((fn, weight) pairs).
# Weight may be a float or a callable that accepts the update as its parameter.
def random_response(responses : List[Tuple[Callable, Union[float, Callable]]]):
    return lambda update: random.choices(
        list(map(nth(0), responses)),
        list(map(lambda w: w if isinstance(w, numbers.Number) else w(update), map(nth(1), responses)))
    )[0](update)


def maybe_respond(response, probability):
    def fn(update):
        if random.random() < probability: return response(update)
        else: return '<noresponse>'

    return fn


# Changes the score of the person who sent a message by the given amount.
def score_changed_message(amount):
    return lambda update: \
        f'Your Social Credit Score has been {"raised" if amount > 0 else "lowered"} by {str(abs(amount))} points.'


# Changes the score of the person who sent a message by the given amount and sends the given response.
def change_score(a, b, wrapped = None):
    def fn(update):
        amount = random.randint(min(a, b), max(a, b))
        update_reputation(amount, update)

        if wrapped is not None: return wrapped(update)
        else: return score_changed_message(amount)(update)

    return fn


# Not really important enough to serialize.
last_zedong_of_the_day = dict()


def may_post_daily_zedong(update):
    # May trigger at most once per day per chat.
    id = update.effective_chat.id
    return not (id in last_zedong_of_the_day and time.time() - last_zedong_of_the_day[id] < (24 * 60 * 60))


def zedong_of_the_day(update):
    if not may_post_daily_zedong(update): return '<noresponse>'
    last_zedong_of_the_day[update.effective_chat.id] = time.time()

    image_name = random.choice(os.listdir(path.join(asset_folder, 'mao')))
    return '<captioned=Today\'s Featured Mao Zedong Image>mao/' + image_name



def change_score_on_sentiment(a, b, threshold, wrapped = None):
    def fn(update):
        text = normalize_message(update.message.text)

        if sentiment_more_than(threshold)(text):
            return change_score(a, b, wrapped)(update)
        if sentiment_less_than(-threshold)(text):
            return change_score(-a, -b, wrapped)(update)
        else:
            if wrapped is not None: return wrapped(update)
            else: return '<noresponse>'

    return fn


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


response_map = [
    # Messages containing the phrase 'Taiwan number one'.
    (
        if_matches(r'taiwan numb[a|e]r? [(one)|1]'),
        change_score(-250, -500, wrapped = lambda update: 'This is by far the most disgusting thing I\'ve read all day.')
    ),
    # Messages that mention Mao Zedong or the CCP.
    (
        logical_or(
            if_contains_word('mao', 'ccp'),
            if_contains('zedong', 'communist party')
        ),
        change_score(25, 50, wrapped = random_response([
            (lambda update: '<audio>Red Sun in the Sky.mp3', 0.50),
            (lambda update: '<video>mao_cat.mp4', 0.50),
            (zedong_of_the_day, lambda update: 10.0 if may_post_daily_zedong(update) else 0.0)
        ]))
    ),
    # Messages mentioning the Social Credit system.
    (
        if_contains_word('credit', 'social score'),
        change_score(-10, -25, wrapped = lambda update: '<image>social_credit.jpg')
    ),
    # Messages mentioning Winnie the Pooh.
    (
        if_contains_word('pooh', 'poohbear', 'winnie'),
        change_score(-100, -250, wrapped = random_response([
            (lambda update: '<image>punishment.jpg', 0.6),
            (lambda update: '<image>dinnertime.jpg', 0.3),
            (lambda update: 'Choose your next words very carefully, capitalist scum...', 0.3)
        ]))
    ),
    # Mentions of the Uyghurs.
    (
        logical_or(
            if_contains_word('uyghur', 'uygur', 'uyguhr', 'uighur', 'uigur', 'uiguhr'),
            if_contains_word('xinjiang', 'xinjang')
        ),
        change_score(-100, -250, wrapped = random_response([
            (lambda update: 'There is no war in B̶a̶ ̶S̶i̶n̶g̶ ̶S̶e̶ The Xinjiang Autonomous Area.', 0.7),
            (lambda update: '<image>punishment.jpg', 0.3)
        ]))
    ),
    # Mentions of Tibet or Hong Kong.
    (
        if_contains_word('tibet', 'dalai', 'hongkong', 'hong kong'),
        change_score(-100, -250, wrapped = random_response([
            (lambda update: 'Rightful Chinese clay.', 0.7),
            (lambda update: 'Choose your next words very carefully, capitalist scum...', 0.3),
            (lambda update: '<image>punishment.jpg', 0.3)
        ]))
    ),
    # Mentions of Tiananmen Square.
    (
        logical_or(
            if_contains('tianman', 'tianmen', 'tiananman', 'tiananmen', 'tianenman', 'tianenmen'),
            if_contains_word('1989', 'student protest', 'student protests')
        ),
        change_score(-250, -500, wrapped = random_response([
            (lambda update: 'I don\'t know what you\'re talking about.', 0.7),
            (lambda update: '<image>punishment.jpg', 0.3)
        ]))
    ),
    # Mentions of common electronic brands.
    (
        logical_or(
            if_contains('iphone', 'ipad', 'ipod', 'imac', 'macbook', 'foxconn', 'samsung', 'huawei', 'xiaomi', 'oneplus'),
            if_contains_word('i phone', 'i pad', 'i pod', 'i mac')
        ),
        lambda _: '<image>iphone_factory.jpg'
    ),
    # Mentions of disputed waters.
    (
        if_contains('china sea', 'chinese sea'),
        lambda _: 'Rightful Chinese territory! It\'s in the name!'
    ),
    # Mentions of tech companies with Chinese alternatives.
    (
        if_contains_word('twitter', 'facebook', 'instagram', 'snapchat', 'whatsapp', 'telegram', 'discord'),
        lambda _: 'Did you mean WeChat?'
    ),
    (
        if_contains_word('amazon'),
        lambda _: 'Did you mean Aliexpress?'
    ),
    # Mentions of the coronavirus.
    (
        if_contains('corona', 'covid', 'wuhan', 'bat soup', 'bat soop', 'vaccin'),
        change_score(-100, -200, wrapped = random_response([
            (lambda score: 'There is nothing going on in Wuhan. Please mind your own business.', 0.6),
            (lambda score: 'I could go for some bat soup right about now...', 0.2),
            (lambda score: '🦇🥣', 0.2)
        ]))
    ),
    # Mentions of human rights.
    (
        if_contains_word('human right', 'human rights', 'freedom', 'independence', 'independance', 'free the', 'autonomy', 'autonomous'),
        change_score(-100, -250, wrapped = lambda update: '<image>punishment.jpg')
    ),
    # Mentions of Xi Jinping and the word 'dictator'.
    (
        logical_and(
            if_contains_word('xi', 'jinpin', 'jinping'),
            if_contains_word('dictator', 'dictatorship')
        ),
        change_score(-100, -250, wrapped = lambda update: '<video>life_of_xi.mp4')
    ),
    # Other mentions of Xi Jinping.
    (
        if_contains_word('xi', 'jinpin', 'jinping'),
        change_score(25, 50, wrapped = random_response([
            (lambda update: 'Ni Hao!', 0.8),
            (lambda update: '<video>life_of_xi.mp4', 0.1),
            (lambda update: '<image>happy_xi.jpg', 0.1)
        ]))
    ),
    # Messages that mention the PRC positively.
    (
        logical_and(
            logical_or(
                if_matches(r'people\s?s?\s?repu?b?l?i?c? of china'),
                if_contains_word('prc')
            ),
            sentiment_more_than(0.15)
        ),
        change_score(25, 50, wrapped = lambda update: 'Long live the Communist Party, long live our Glorious Homeland')
    ),
    # Messages that mention the PRC negatively.
    (
        logical_and(
            logical_or(
                if_matches(r'people\s?s?\s?repu?b?l?i?c? of china'),
                if_contains_word('prc')
            ),
            sentiment_less_than(-0.15)
        ),
        change_score(-100, -200, wrapped = lambda update: 'This is simply unacceptable.')
    ),
    # Messages that mention the ROC.
    (
        logical_or(
            if_matches(r'repu?b?l?i?c? of china'),
            if_contains('taiwan'),
            if_contains_word('roc')
        ),
        change_score(-50, -100, wrapped = lambda update: 'There is only one China. Always has been.')
    ),
    # Other mentions of China.
    (
        if_contains_word('china', 'chinese'),
        change_score(25, 50, wrapped = lambda update: '🇨🇳🇨🇳🇨🇳🇨🇳🇨🇳')
    ),
    # Messages containing derogatory terms.
    (
        logical_or(
            if_contains_word('chink', 'ching', 'chong'),
            if_contains('chingchang', 'chingchong', 'changchong', 'ping pong', 'gook', 'chinaman')
        ),
        change_score(-250, -500, wrapped = random_response([
            (lambda update: '<image>punishment.jpg', 0.5),
            (lambda update: 'Cease disrespecting Chinese culture immediately.', 0.5)
        ]))
    ),

    # Messages containing the word 'LMAO'.
    (
        if_contains_word('lmao'),
        maybe_respond(lambda update: '<image>le_mao.jpg', 0.25)
    ),
    # Messages mentioning otters.
    (
        if_contains_word('otta', 'otter', 'ottas', 'otters'),
        change_score(5, 10, wrapped = random_response([
            (lambda update: '<image>commie.jpg', 0.7),
            (lambda update: read_text('otta_time.txt'), 0.3)
        ]))
    ),
    # Mentions of capitalism.
    (
        if_contains('capitalis'),
        change_score_on_sentiment(-50, -100, 0.15, wrapped = lambda update: 'Capitalism Bad.')
    ),
    # Mentions of communism.
    (
        if_contains('communis', 'socialis'),
        change_score_on_sentiment(25, 50, 0.15, wrapped = lambda update: 'Communism Good.')
    ),
    # Randomly send images of mao zedong.
    (
        lambda _: True,
        random_response([
            (lambda update: '<noresponse>', 0.95),
            (zedong_of_the_day, 0.05)
        ])
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
        elif response.startswith('<captioned='):
            caption    = response[len('<captioned=') : response.find('>')]
            image_name = response[response.find('>') + 1 :]

            send_image_message(updater, update.effective_chat.id, image_name, caption = caption)
        elif response.startswith('<video>'):
            send_video_reply(update, context, response[len('<video>'):])
        elif response.startswith('<audio>'):
            send_audio_reply(update, context, response[len('<audio>'):])
        elif response.startswith('<noresponse>'):
            return
        else:
            send_reply(update, context, response)