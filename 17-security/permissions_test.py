#!/usr/bin/env python3
"""
Checks what each user created by setup_security.sh can and cannot do.
Every line prints the expected outcome and the real one.
"""
import pika
import pika.exceptions

USERS = {
    'order_service': 'order-pass',
    'reporting': 'report-pass',
    'guest': 'guest',
}

results = []


def check(description, expected_ok, action, user, vhost='shop', password=None):
    """Run action(channel) as user and compare the outcome with the expectation."""
    password = password or USERS[user]
    params = pika.ConnectionParameters(
        host='localhost', virtual_host=vhost,
        credentials=pika.PlainCredentials(user, password),
    )
    try:
        connection = pika.BlockingConnection(params)
        try:
            action(connection.channel())
            outcome, detail = True, 'allowed'
        except pika.exceptions.ChannelClosedByBroker as e:
            outcome, detail = False, e.reply_text.split(' - ')[0] + ' - ' + e.reply_text.split(' - ', 1)[-1][:70]
        finally:
            if connection.is_open:
                connection.close()
    except pika.exceptions.ProbableAuthenticationError:
        outcome, detail = False, 'authentication failed'
    except pika.exceptions.ProbableAccessDeniedError:
        outcome, detail = False, f'access to vhost {vhost!r} refused'
    except pika.exceptions.AMQPConnectionError as e:
        outcome, detail = False, f'connection refused ({type(e).__name__})'

    ok = outcome == expected_ok
    results.append(ok)
    print(f" [{'PASS' if ok else 'FAIL'}] {user:<13} {description:<45} -> {detail}")


def setup_orders(ch):
    ch.exchange_declare('orders.events', 'topic', durable=True)
    ch.queue_declare('orders.created', durable=True)
    ch.queue_bind('orders.created', 'orders.events', 'order.created')


def publish_order(ch):
    ch.confirm_delivery()
    ch.basic_publish('orders.events', 'order.created', b'{"order": 1001}')


def consume_one(ch):
    ch.basic_get('orders.created', auto_ack=True)


def publish_default_exchange(ch):
    ch.confirm_delivery()   # wait for the broker answer, so a refusal is reported here
    ch.basic_publish('', 'orders.created', b'x')


print('Expected behaviour of the least-privilege setup:\n')
check('declare orders.events / orders.created', True, setup_orders, 'order_service')
check('publish to orders.events', True, publish_order, 'order_service')
check('declare queue payments.queue', False, lambda ch: ch.queue_declare('payments.queue', durable=True), 'order_service')
check('publish to amq.default (default exchange)', False, publish_default_exchange, 'order_service')
check('connect to vhost "/"', False, lambda ch: None, 'order_service', vhost='/')
check('consume from orders.created', True, consume_one, 'reporting')
check('publish to orders.events', False, publish_order, 'reporting')
check('delete queue orders.created', False, lambda ch: ch.queue_delete('orders.created'), 'reporting')
check('connect to vhost "shop"', False, lambda ch: None, 'guest')
check('login with a wrong password', False, lambda ch: None, 'order_service', password='wrong')

print(f'\n {sum(results)}/{len(results)} checks behaved as expected')
