import os
import sys


interp   = str(sys.executable)
commands = [
    '-m pip install python-telegram-bot',
    '-m pip install textblob',
    '-m textblob.download_corpora'
]


for command in commands:
    os.system(interp + ' ' + command)

print('All done.')