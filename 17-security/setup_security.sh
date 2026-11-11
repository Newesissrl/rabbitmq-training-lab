#!/bin/bash
# Creates the "shop" virtual host and three users with least-privilege permissions.
# Training passwords only - in real environments use a secret store, never
# commit passwords and avoid typing them in shell history.
set -e
R="docker exec rabbitmq rabbitmqctl"

echo "== Virtual host"
$R add_vhost shop

echo "== order_service: may create and use only resources named orders.*"
$R add_user order_service order-pass
#                 vhost  user           configure     write         read
$R set_permissions -p shop order_service '^orders\..*' '^orders\..*' '^orders\..*'

echo "== reporting: read-only on orders.* (consume), no configure, no write"
$R add_user reporting report-pass
$R set_permissions -p shop reporting '' '' '^orders\..*'

echo "== shop_ops: Management UI access restricted to the shop vhost"
$R add_user shop_ops ops-pass
$R set_user_tags shop_ops monitoring
$R set_permissions -p shop shop_ops '' '' '.*'

echo
$R list_permissions -p shop
