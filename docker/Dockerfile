FROM python:3.9-slim

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    lm-sensors \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя pet-temp
RUN useradd -r -s /bin/false pet-temp

# Создание директорий
RUN mkdir -p /opt/pet_temp/logs && \
    chown -R pet-temp:pet-temp /opt/pet_temp && \
    chmod -R 755 /opt/pet_temp && \
    chmod -R 775 /opt/pet_temp/logs

# Копирование файлов приложения
COPY temp_monitor_core.py /opt/pet_temp/
COPY temp_monitor_web.py /opt/pet_temp/
COPY requirements.txt /opt/pet_temp/

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r /opt/pet_temp/requirements.txt

# Настройка supervisord
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Запуск supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
