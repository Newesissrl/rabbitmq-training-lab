#!/bin/bash
# Removes everything created by setup_security.sh (deleting the vhost also
# deletes its exchanges, queues and permissions).
R="docker exec rabbitmq rabbitmqctl"
$R delete_vhost shop
$R delete_user order_service
$R delete_user reporting
$R delete_user shop_ops
