#!/usr/bin/env python3
"""
Minimal queue monitor based on the Management HTTP API (no extra libraries).

Every few seconds it prints, for each queue: messages ready, unacknowledged,
consumers and publish/deliver rates, and raises simple alerts:
  - BACKLOG      : more than --backlog messages ready
  - NO CONSUMERS : messages are waiting but nobody consumes
  - ALARM        : a memory or disk alarm blocks publishers

Usage: python queue_monitor.py [--interval 3] [--backlog 100]
"""
import argparse
import base64
import json
import time
import urllib.error
import urllib.request

API = 'http://localhost:15672/api'
AUTH = base64.b64encode(b'guest:guest').decode()


def get(path):
    """GET an HTTP API endpoint and return (status, decoded JSON)."""
    request = urllib.request.Request(API + path, headers={'Authorization': f'Basic {AUTH}'})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as e:      # health checks answer 503 when failing
        return e.code, json.load(e)


def rate(queue, key):
    return queue.get('message_stats', {}).get(f'{key}_details', {}).get('rate', 0.0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=float, default=3)
    parser.add_argument('--backlog', type=int, default=100)
    args = parser.parse_args()

    while True:
        _, overview = get('/overview')
        alarm_status, alarms = get('/health/checks/alarms')
        queues = get('/queues?columns=name,vhost,type,messages_ready,'
                     'messages_unacknowledged,consumers,message_stats')[1]

        totals = overview['queue_totals']
        print(f"\n{time.strftime('%H:%M:%S')}  node={overview['node']}  "
              f"ready={totals.get('messages_ready', 0)}  unacked={totals.get('messages_unacknowledged', 0)}  "
              f"connections={overview['object_totals']['connections']}")
        print(f"{'queue':<28}{'type':<9}{'ready':>8}{'unacked':>9}{'cons':>6}{'pub/s':>8}{'deliv/s':>9}  alerts")

        for q in sorted(queues, key=lambda q: q.get('messages_ready', 0), reverse=True)[:15]:
            ready = q.get('messages_ready', 0)
            alerts = []
            # Streams keep messages after consumption (retention-based): their
            # "ready" count is the size of the log, not a backlog
            if q.get('type') != 'stream' and ready > args.backlog:
                alerts.append('BACKLOG')
            if q.get('type') != 'stream' and ready > 0 and q.get('consumers', 0) == 0:
                alerts.append('NO CONSUMERS')
            print(f"{q['name'][:27]:<28}{q.get('type', ''):<9}{ready:>8}{q.get('messages_unacknowledged', 0):>9}"
                  f"{q.get('consumers', 0):>6}{rate(q, 'publish'):>8.1f}{rate(q, 'deliver_get'):>9.1f}  {' '.join(alerts)}")

        if alarm_status != 200:
            for alarm in alarms.get('alarms', []):
                print(f" !! ALARM: {alarm['resource']} alarm on {alarm['node']} - publishers are blocked")

        time.sleep(args.interval)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except urllib.error.URLError as e:
        print(f'Cannot reach the HTTP API at {API}: {e.reason}')
