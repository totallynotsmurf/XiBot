import collections

from common import *

import json
import os


reputation = dict()

reputation_messages = collections.OrderedDict({
    1000: [
        lambda user: f'Xi Jinping is disappointed in {user}\'s recent actions.',
        lambda user: f'Xi Jinping personally commends {user} for his excellent behaviour.'
    ],
    750: [
        lambda user: f'{user} has been stripped of his 两弹一星功勋奖章 medal.',
        lambda user: f'{user} has been awarded a 两弹一星功勋奖章 medal for his excellent behaviour.'
    ],
    500: [
        lambda user: f'{user} has been removed from his position as Officer of the Chinese Communist Party.',
        lambda user: f'{user} has been promoted to Honorary Officer of the Chinese Communist Party.'
    ],
    300: [
        lambda user: f'{user} has been removed from his position within the Communist Party.',
        lambda user: f'{user} has been accepted into the Communist Party.'
    ],
    200: [
        lambda user: f'{user} is no longer exempt from the one-child policy.',
        lambda user: f'{user} is now exempt from the one-child policy.'
    ],
    100: [
        lambda user: f'{user} is no longer eligible to procreate.',
        lambda user: f'{user} has gained procreation rights.'
    ],
    -150: [
        lambda user: f'{user} has lost e621 privileges.',
        lambda user: f'{user} has regained e621 privileges.'
    ],
    -250: [
        lambda user: f'{user} has lost the ability to travel on international flights.',
        lambda user: f'{user} has regained the ability to travel on international flights.'
    ],
    -500: [
        lambda user: f'{user} has lost the ability to use public transportation.',
        lambda user: f'{user} has regained the ability to use public transportation.'
    ],
    -750: [
        lambda user: f'{user} is no longer allowed to travel more than 25km from his residence.',
        lambda user: f'{user} is once again allowed to travel more than 25km from his residence.'
    ],
    -1000: [
        lambda user: f'{user} is no longer allowed to travel more than 5km from his residence.',
        lambda user: f'{user} is once again allowed to travel more than 5km from his residence.'
    ],
    -1250: [
        lambda user: f'{user} is now scheduled for transportation to the 习近平光荣 re-education camp.',
        lambda user: f'{user} is no longer scheduled for transportation to the 习近平光荣 re-education camp.'
    ],
    -1500: [
        lambda user: f'{user} has mysteriously disappeared.',
        lambda user: f'{user} has re-appeared with renewed respect for the Glorious Chinese Communist Party.'
    ]
})


def get_reputation(update):
    global reputation

    username = update.message.from_user.username
    return reputation[username] if username in reputation else 0.0


def update_reputation(delta, update):
    global reputation, reputation_messages

    display_name = update.message.from_user.full_name
    username     = update.message.from_user.username

    if username not in reputation: reputation[username] = 0.0

    old_reputation = reputation[username]
    reputation[username] += delta

    reply = []
    for value, actions in reputation_messages.items():
        lower = min(old_reputation, reputation[username])
        upper = max(old_reputation, reputation[username])

        if lower <= value <= upper:
            message = actions[0] if delta < 0 else actions[1]
            reply.append(message(display_name))

    if len(reply) > 0: send_reply(update, None, '\n'.join(reply))
    save_reputations()


def reset_reputation(update):
    global reputation

    display_name = update.message.from_user.full_name
    username     = update.message.from_user.username
    reputation[username] = 0

    send_reply(update, None, f'Xi Jinping has purged all memories of {display_name}.')
    save_reputations()


def load_reputations():
    global reputation

    with open(os.path.join(asset_folder, 'reputation.json'), 'r') as handle:
        reputation = collections.OrderedDict(map(
            lambda kv: (str(kv[0]), float(kv[1])),
            json.load(handle).items()
        ))


def save_reputations():
    global reputation

    with open(os.path.join(asset_folder, 'reputation.json'), 'w') as handle:
        json.dump(reputation, handle, indent = 4)