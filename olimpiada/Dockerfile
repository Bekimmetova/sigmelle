FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends g++ tzdata && rm -rf /var/lib/apt/lists/*
ENV TZ=Asia/Tashkent PYTHONUNBUFFERED=1
RUN useradd -m olimp
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data && chown -R olimp:olimp /app/data
USER olimp
EXPOSE 5000
CMD ["gunicorn", "-w", "1", "--threads", "16", "-b", "0.0.0.0:5000", "app:app"]
