FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       libz1 \
       libtinfo6 \
       procps \
       psmisc \
       net-tools \
       iproute2 \
       lsof \
       curl \
       vim \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash agentuser

WORKDIR /opt/b1-2
COPY agent-app-leak /opt/b1-2/agent-app-leak

RUN chmod +x /opt/b1-2/agent-app-leak \
    && mkdir -p /home/agentuser/agent-home/upload_files \
               /home/agentuser/agent-home/api_keys \
               /home/agentuser/agent-home/logs \
    && echo 'agent_api_key_test' > /home/agentuser/agent-home/api_keys/secret.key \
    && chown -R agentuser:agentuser /home/agentuser /opt/b1-2

ENV AGENT_HOME=/home/agentuser/agent-home \
    AGENT_PORT=15034 \
    AGENT_UPLOAD_DIR=/home/agentuser/agent-home/upload_files \
    AGENT_KEY_PATH=/home/agentuser/agent-home/api_keys \
    AGENT_LOG_DIR=/home/agentuser/agent-home/logs \
    MEMORY_LIMIT=100 \
    CPU_MAX_OCCUPY=70 \
    MULTI_THREAD_ENABLE=true

EXPOSE 15034
USER agentuser

CMD ["/opt/b1-2/agent-app-leak"]
