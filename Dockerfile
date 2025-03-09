FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    supervisor \
    build-essential \
    python3-dev \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code (excluding .env files via .dockerignore)
COPY . .

# Generate self-signed SSL certificate
RUN mkdir -p /etc/nginx/ssl && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt \
    -subj "/C=US/ST=California/L=Berkeley/O=Flare/CN=localhost"

# Create nginx configuration
RUN mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled \
    && echo 'server { \
    listen 80; \
    server_name _; \
    return 301 https://$host$request_uri; \
} \
\
server { \
    listen 443 ssl; \
    server_name _; \
    \
    ssl_certificate /etc/nginx/ssl/nginx.crt; \
    ssl_certificate_key /etc/nginx/ssl/nginx.key; \
    ssl_protocols TLSv1.2 TLSv1.3; \
    ssl_prefer_server_ciphers on; \
    \
    location / { \
        proxy_pass http://127.0.0.1:8501; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_read_timeout 86400; \
    } \
}' > /etc/nginx/sites-available/default \
    && ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/ \
    && echo "daemon off;" >> /etc/nginx/nginx.conf

# Create Streamlit config
RUN mkdir -p /root/.streamlit \
    && echo '[server]\n\
headless = true\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
' > /root/.streamlit/config.toml

# Find the path to the streamlit executable
RUN STREAMLIT_PATH=$(which streamlit) && echo "Streamlit path: $STREAMLIT_PATH"

# Copy supervisord configuration instead of creating it inline
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose the ports nginx runs on
EXPOSE 80 443

# Add labels for Confidential VM compatibility
LABEL "tee.launch_policy.allow_env_override"="GEMINI_API_KEY,ETHEREUM_RPC_URL,BASE_RPC_URL,FLARE_RPC_URL,WALLET_ADDRESS,PRIVATE_KEY,REACT_APP_RAINBOW_PROJECT_ID,GITHUB_TOKEN,SIMULATE_ATTESTATION"
LABEL "tee.launch_policy.log_redirect"="always"

# Command to run supervisord which will start both nginx and streamlit
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 