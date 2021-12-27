import os
import subprocess


service_name = 'xibot.service'


def runcmd(*args):
    result = subprocess.run([*args], capture_output = True)

    if result.returncode != 0:
        raise RuntimeError(f'Subprocess {" ".join(args)} failed with error code {result.returncode}: {result.stderr}')

    return result.stdout.splitlines()


def main():
    # Check if updates are available.
    runcmd('git', 'fetch', 'origin')
    local_version,  = runcmd('git', 'rev-parse', 'HEAD')
    remote_version, = runcmd('git', 'rev-parse', 'origin/master')

    if local_version == remote_version:
        print(f'Current version {local_version} is up-to-date.')
        return
    else:
        print(f'Current version {local_version} does not match remote version {remote_version}.')


    # Stop the bot service, update from the remote, and restart the bot.
    print('Stopping service...')
    runcmd('sudo', 'systemctl', 'stop', service_name)

    print('Pulling updates from remote...')
    runcmd('git', 'reset', '--hard', 'origin/master')
    runcmd('sudo', 'chmod', 'g+rwx', './')

    print('Restarting service...')
    runcmd('sudo', 'systemctl', 'start', service_name)


    print(f'Update to version {remote_version} completed.')


if __name__ == '__main__': main()