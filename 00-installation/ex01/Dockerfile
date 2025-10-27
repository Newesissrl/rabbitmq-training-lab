FROM rabbitmq:4.1.4-management-alpine

# Create .erlang.cookie with proper permissions to avoid permission issues
RUN mkdir -p /var/lib/rabbitmq && \
    echo "rabbitmq-cookie-single" > /var/lib/rabbitmq/.erlang.cookie && \
    chmod 400 /var/lib/rabbitmq/.erlang.cookie && \
    chown -R rabbitmq:rabbitmq /var/lib/rabbitmq