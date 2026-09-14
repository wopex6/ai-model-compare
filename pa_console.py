"""Run a bash command on PythonAnywhere and print its output."""
import sys
import time

import requests

import deploy_anywhere as d

HEADERS = {'Authorization': f'Token {d.API_TOKEN}'}


def run(cmd, wait=20):
    consoles = requests.get(f'{d.API_BASE}/consoles/', headers=HEADERS, timeout=60).json()
    if not consoles:
        resp = requests.post(f'{d.API_BASE}/consoles/', headers=HEADERS, timeout=60,
                             data={'executable': 'bash', 'arguments': '',
                                   'working_directory': d.PROJECT_PATH})
        cid = resp.json()['id']
        time.sleep(8)
    else:
        cid = consoles[0]['id']

    requests.post(f'{d.API_BASE}/consoles/{cid}/send_input/', headers=HEADERS,
                  timeout=60, data={'input': cmd + '\n'})
    time.sleep(wait)
    out = requests.get(f'{d.API_BASE}/consoles/{cid}/get_latest_output/',
                       headers=HEADERS, timeout=60)
    return out.json().get('output', '')


if __name__ == '__main__':
    command = sys.argv[1]
    seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    print(run(command, seconds)[-5000:])
