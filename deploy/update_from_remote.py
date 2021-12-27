import os
import subprocess

service_name = 'xibot.service'
install_dir  = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)


def runcmd(*args):
    result = subprocess.run([*args], capture_output = True, check = True)
    return result.stdout.splitlines()


def main():
    # Check if updates are available.
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
    runcmd('git', 'pull', 'origin/master')

    print('Restarting service...')
    runcmd('sudo', 'systemctl', 'start', service_name)


    print(f'Update to version {remote_version} completed.')


if __name__ == '__main__': main()