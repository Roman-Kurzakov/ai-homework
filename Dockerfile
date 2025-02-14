FROM python:3.11-slim

WORKDIR /app

COPY . /app

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r ./requirements.txt

# RUN apt-get update && \
#     apt-get install -y --no-install-recommends wireguard && \
#     rm -rf /var/lib/apt/lists/*

CMD ["python3", "main_assistants.py", "&&", "python3", "consumer.py"]
