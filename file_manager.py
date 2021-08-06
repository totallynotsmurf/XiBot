import json
from os import path


class file_manager:
    # Provide asset folder as parameter to prevent circular dependency.
    def __init__(self, asset_folder):
        self.asset_folder = asset_folder
        self.id_map = dict()
        self.load_from_file()


    def store(self, file_name, file_id):
        self.id_map[file_name] = file_id
        self.save_to_file()


    def save_to_file(self):
        with open(path.join(self.asset_folder, 'file_ids.json'), 'w') as handle:
            json.dump(self.id_map, handle, indent = 4)


    def load_from_file(self):
        p = path.join(self.asset_folder, 'file_ids.json')

        if path.exists(p):
            with open(p, 'r') as handle:
                self.id_map = json.load(handle)

