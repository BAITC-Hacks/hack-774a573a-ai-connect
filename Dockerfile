FROM python:3.11-slim

# Отключаем буферизацию вывода
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Устанавливаем минимальные системные утилиты
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта (включая датасеты Beeline и agent.py)
COPY . .

# Открываем порт для Streamlit
EXPOSE 8000

# Запускаем Streamlit вместо обычного Python
CMD ["streamlit", "run", "main.py", "--server.port=8000", "--server.address=0.0.0.0"]