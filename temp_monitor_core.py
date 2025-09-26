import subprocess
import time
import logging
from logging.handlers import RotatingFileHandler
import requests
import datetime
import os

# Интервал проверки
INTERVAL_SEC = 60
  # Порог для алерта в °C
THRESHOLD_TEMP = 65
# Порог для восстановления в °C
RECOVERY_THRESHOLD = 60  
LOG_FILE = '/opt/pet_temp/logs/temp_monitor.log'
# точные 10 MB, ротация
MAX_LOG_SIZE = 10 * 1024 * 1024
# Храним 5 ротаций
BACKUP_COUNT = 5
TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'
# Команда для получения данных температуры
SENSOR_COMMAND = 'sensors'

# Настройка логирования с ротацией
handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s - %(message)s')

# Флаг для отслеживания алерта
alert_triggered = False

def get_temperature():
    try:
        output = subprocess.check_output(SENSOR_COMMAND, shell=True).decode('utf-8')
        # Парсим пример: ищем строку вроде "Core 0: +45.0°C"
        for line in output.splitlines():
            if 'Core 0' in line:
                temp_str = line.split('+')[1].split('°')[0]
                return float(temp_str)
        return None
    except Exception as e:
        logging.error(f"Error getting temp: {e}")
        return None

def send_telegram_alert(temp, is_recovery=False):
    if is_recovery:
        message = f"✅ Температура вернулась к норме. Текущая: {temp}°C"
    else:
        message = f"🚨 Температура превысила {THRESHOLD_TEMP}°C! Текущая: {temp}°C"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={message}"
    try:
        requests.get(url)
        logging.info(f"Sent Telegram {'recovery' if is_recovery else 'alert'}: {message}")
    except Exception as e:
        logging.error(f"Error sending Telegram: {e}")

def main():
    global alert_triggered
    while True:
        temp = get_temperature()
        if temp is not None:
            logging.info(f"Temperature: {temp}°C")
            if temp > THRESHOLD_TEMP and not alert_triggered:
                send_telegram_alert(temp)
                alert_triggered = True
            elif temp <= RECOVERY_THRESHOLD and alert_triggered:
                send_telegram_alert(temp, is_recovery=True)
                alert_triggered = False
        time.sleep(INTERVAL_SEC)

if __name__ == '__main__':
    main()