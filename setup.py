import os


commands = [
    'pip install python-telegram-bot',
    'pip install textblob',
    'python -m textblob.download_corpora'
]


for command in commands:
    os.system(command)

print('All done.')