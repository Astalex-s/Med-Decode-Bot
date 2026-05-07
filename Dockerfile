FROM python:3.11-slim

# Системные зависимости для OpenCV и EasyOCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаём папку для временных файлов
RUN mkdir -p temp

CMD ["python", "-m", "presentation.bot.main"]
