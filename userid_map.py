import collections
import json
import os

from common import asset_folder


# Keep track of username => ID mapping because there is no way to perform this conversion in the TG API.
user_ids = dict()


def get_id(username):
    global user_ids
    return user_ids[username] if username in user_ids else None


def set_id(update):
    global user_ids

    user = update.effective_user
    if not user: return

    user_ids[user.username] = user.id
    save_ids()


def load_ids():
    global user_ids

    json_path = os.path.join(asset_folder, 'user_ids.json')

    if not os.path.exists(json_path):
        with open(json_path, 'w') as handle:
            handle.write('{}')

    with open(json_path, 'r') as handle:
        user_ids = collections.OrderedDict(map(
            lambda kv: (str(kv[0]), float(kv[1])),
            json.load(handle).items()
        ))


def save_ids():
    global user_ids

    with open(os.path.join(asset_folder, 'user_ids.json'), 'w') as handle:
        json.dump(user_ids, handle, indent = 4)