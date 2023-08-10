# my_package/ping_check.py
import subprocess


def check_ping(host):
    try:
        subprocess.run(['ping', '-c', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
