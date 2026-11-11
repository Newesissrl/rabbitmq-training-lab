# Exercise 17: Security - Users, Virtual Hosts and Permissions

## Concept
Apply **least privilege** to messaging:
- **Virtual hosts** isolate applications (separate exchanges, queues, permissions)
- **Permissions** (configure / write / read) are regular expressions on resource names
- **User tags** control access to the Management UI and HTTP API
- **guest** is a convenience user for development only

| Permission | Needed to... |
|------------|--------------|
| configure | declare / delete exchanges and queues |
| write | publish to an exchange, bind a queue *to* it (as destination) |
| read | consume from a queue, bind *from* an exchange (as source) |

## Learning Objectives
- Create a virtual host and users from the CLI
- Write permission regexes and predict their effect
- Understand why the default exchange is also subject to permissions
- Review the security defaults of the RabbitMQ Docker image

## Setup
1. Start RabbitMQ from the repository root: `docker compose up -d`
2. Create the vhost and users:
   ```bash
   ./setup_security.sh
   ```
   (Windows: run the `docker exec rabbitmq rabbitmqctl ...` lines of the script one by one.)

| User | Tags | configure | write | read | Purpose |
|------|------|-----------|-------|------|---------|
| `order_service` | - | `^orders\..*` | `^orders\..*` | `^orders\..*` | Application: owns the `orders.*` resources |
| `reporting` | - | *(none)* | *(none)* | `^orders\..*` | Read-only consumer |
| `shop_ops` | `monitoring` | *(none)* | *(none)* | `.*` | Operator: UI access to the `shop` vhost only |

## Exercise 1: Predict, Then Verify
Before running the test, write down for each line whether it should be allowed:
```bash
python permissions_test.py
```
Expected: `10/10 checks behaved as expected`. Look closely at:
- **Default exchange:** `order_service` cannot publish with `exchange=''` because
  it is the exchange `amq.default` and does not match `^orders\..*`
- **Virtual host:** a user without permissions on a vhost cannot even connect to it
- **guest** has no permissions on `shop`

## Exercise 2: Management UI Access
Log in to http://localhost:15672 as `shop_ops` / `ops-pass`:
- Only the `shop` vhost and its queues are visible
- The **Admin** tab is not available (`monitoring` is not `administrator`)

Try `reporting` / `report-pass`: the login fails, because users without tags have
no access to the Management UI or the HTTP API:
```bash
curl -u reporting:report-pass http://localhost:15672/api/overview     # 401
curl -u shop_ops:ops-pass http://localhost:15672/api/queues/shop      # 200
```

## Exercise 3: Fix a Permission
`order_service` now also needs to publish to the existing `amq.topic` exchange.
Change **only** what is needed (hint: which permission does publishing require?):
```bash
docker exec rabbitmq rabbitmqctl set_permissions -p shop order_service \
  '^orders\..*' '^(orders\..*|amq\.topic)$' '^orders\..*'
```
Run `python permissions_test.py` again: did any other result change?

## Exercise 4: Review the guest User
```bash
docker exec rabbitmq cat /etc/rabbitmq/conf.d/10-defaults.conf
```
The official Docker image sets `loopback_users.guest = false`, which lets `guest`
log in from **any** host (by default RabbitMQ only accepts `guest` from localhost).
That is why the exercises can use `guest/guest` through Docker port mappings.

**Discuss:** in a real deployment you would:
- create named users per application (as above) and delete `guest`
  (`rabbitmqctl delete_user guest`; do not do it here, the other exercises use it)
- set `RABBITMQ_DEFAULT_USER` / `RABBITMQ_DEFAULT_PASS` from a secret store
  (see the Kubernetes exercise `00-installation/ex03`)
- enable TLS for client connections (port 5671) and the Management UI
- limit resources per vhost: `rabbitmqctl set_vhost_limits -p shop '{"max-connections": 50, "max-queues": 20}'`

## Cleanup
```bash
./cleanup_security.sh
```

## Key Takeaways
- One vhost per application or tenant; one user per application
- Permissions are regexes on **names**: a naming convention (`orders.*`) makes least privilege easy
- Publishing to the default exchange requires write on `amq.default`
- Tags (`management`, `monitoring`, `policymaker`, `administrator`) only affect UI/HTTP API access
