#!/usr/bin/env python3
import json
import os
import socket
import time
from urllib.request import Request, urlopen

BASE_URL = os.environ.get('LPDISPLAY_BASE_URL', '').rstrip('/')
TOKEN = os.environ.get('LPDISPLAY_PLAYER_TOKEN', '')
AGENT_VERSION = 'raspi-agent-v0.1'


def post_json(url, data):
    payload = json.dumps(data).encode('utf-8')
    req = Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urlopen(req, timeout=10) as response:
        return response.read().decode('utf-8')


def main():
    if not BASE_URL or not TOKEN:
        raise SystemExit('LPDISPLAY_BASE_URL ou LPDISPLAY_PLAYER_TOKEN manquant')
    heartbeat_url = f'{BASE_URL}/api/player/{TOKEN}/heartbeat/'
    while True:
        try:
            post_json(heartbeat_url, {
                'agent_version': AGENT_VERSION,
                'hostname': socket.gethostname(),
            })
        except Exception as exc:
            print(f'heartbeat failed: {exc}', flush=True)
        time.sleep(30)


if __name__ == '__main__':
    main()
