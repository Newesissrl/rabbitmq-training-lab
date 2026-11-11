FROM rabbitmq:4.3-management-alpine

# Pre-create the Erlang cookie owned by the rabbitmq user.
# Why: the setup scripts poll the node with "docker exec ... rabbitmqctl", which
# runs as root. If that happens before the server has written its cookie, the
# CLI creates /var/lib/rabbitmq/.erlang.cookie owned by root and the server
# then fails to start with "Error when reading .erlang.cookie: eacces".
# A fixed cookie is also required for all nodes of a cluster (exercise 2).
RUN mkdir -p /var/lib/rabbitmq && \
    echo "rabbitmq-cookie-single" > /var/lib/rabbitmq/.erlang.cookie && \
    chmod 400 /var/lib/rabbitmq/.erlang.cookie && \
    chown -R rabbitmq:rabbitmq /var/lib/rabbitmq