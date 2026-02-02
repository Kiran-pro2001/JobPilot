FROM python:3.12-slim

# install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    unzip \
    curl \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libxdamage1 \
    libxfixes3 \
    xdg-utils \
    --no-install-recommends

# install google chrome (2026 safe)
RUN mkdir -p /etc/apt/keyrings \
    && wget -qO- https://dl.google.com/linux/linux_signing_key.pub \
    | gpg --dearmor \
    > /etc/apt/keyrings/google-linux-signing-key.gpg

RUN echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-linux-signing-key.gpg] \
http://dl.google.com/linux/chrome/deb/ stable main" \
> /etc/apt/sources.list.d/google-chrome.list

RUN apt-get update && apt-get install -y google-chrome-stable

# set workdir
WORKDIR /app

# copy requirements
COPY requirements.txt .

# install python deps
RUN pip install --no-cache-dir -r requirements.txt

# copy all files
COPY . .

EXPOSE 3000

CMD ["python", "app.py"]
