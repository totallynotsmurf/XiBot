import os
import sys


interp   = str(sys.executable)
commands = [
    '-m pip install python-telegram-bot==13.11',
    '-m pip install textblob',
    '-m textblob.download_corpora'
]


for command in commands:
    os.system(interp + ' ' + command)

print('All done.')
