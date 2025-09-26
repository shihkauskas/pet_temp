# Монитор температуры

Инструмент на Python для мониторинга температуры процессора на Linux с использованием `lm-sensors`. Логирует данные и отправляет уведомления в Telegram при превышении температуры и возврате к норме. Работает как systemd-сервис от пользователя `pet-temp`.

## Описание

Этот проект отслеживает температуру процессора (ядро 0) на Linux-хосте, записывает данные в лог-файл с ротацией и отправляет уведомления в Telegram:
- При превышении порога (`65°C` по умолчанию) — алерт с 🚨.
- При возврате к норме (≤ `60°C` по умолчанию) — сообщение о восстановлении с ✅.

Логи хранятся в `/opt/pet_temp/logs/temp_monitor.log` с ротацией (макс. 10 МБ, 5 резервных копий). Данные можно использовать для визуализации (например, в веб-интерфейсе).

## Возможности
- Периодическая проверка температуры через `lm-sensors`.
- Логирование в файл с ротацией для экономии места.
- Уведомления в Telegram о превышении температуры и восстановлении.
- Настраиваемые пороги и интервалы проверки.
- Запуск как systemd-сервис от пользователя `pet-temp`.

## Требования
- Linux-система (протестировано на Ubuntu/Debian).
- Python 3.6+.
- `lm-sensors` для чтения температуры.
- Токен Telegram-бота и ID чата для уведомлений.

## Установка

### Шаг 1: Установка lm-sensors
Установите `lm-sensors` для получения данных о температуре:
```bash
sudo apt update
sudo apt install lm-sensors
```
Проверьте, что команда работает:
```bash
sensors
```
Найдите строку с температурой (например, `Core 0: +45.0°C`). Если нужен другой сенсор, измените функцию `get_temperature()` в `/opt/pet_temp/temp_monitor_core.py`.

### Шаг 2: Создание пользователя pet-temp
Создайте системного пользователя `pet-temp` без возможности логина:
```bash
sudo useradd -r -s /bin/false pet-temp
```

### Шаг 3: Клонирование репозитория и настройка структуры
Клонируйте репозиторий и создайте директории:
```bash
git clone https://github.com/yourusername/temperature-monitor.git
sudo mkdir -p /opt/pet_temp/logs
sudo mv temperature-monitor/temp_monitor_core.py /opt/pet_temp/
sudo mv temperature-monitor/requirements.txt /opt/pet_temp/
```
Настройте права доступа:
```bash
sudo chown -R pet-temp:pet-temp /opt/pet_temp
sudo chmod -R 755 /opt/pet_temp
sudo chmod -R 775 /opt/pet_temp/logs
```

### Шаг 4: Настройка виртуального окружения
Создайте и активируйте виртуальное окружение в `/opt/pet_temp`:
```bash
sudo python3 -m venv /opt/pet_temp/venv
sudo /opt/pet_temp/venv/bin/pip install -r /opt/pet_temp/requirements.txt
```
Настройте права для `pet-temp`:
```bash
sudo chown -R pet-temp:pet-temp /opt/pet_temp/venv
```

### Шаг 5: Настройка скрипта
Отредактируйте `/opt/pet_temp/temp_monitor_core.py`, указав токен Telegram-бота и ID чата:
```python
TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN'  # Получите через @BotFather
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'  # ID вашего чата
```
Дополнительные настройки (по желанию):
- `THRESHOLD_TEMP`: Порог для алерта (по умолчанию: 33°C).
- `RECOVERY_THRESHOLD`: Порог для восстановления (по умолчанию: 30°C).
- `INTERVAL_SEC`: Интервал проверки (по умолчанию: 60 секунд).
- `SENSOR_COMMAND`: Команда для получения температуры (по умолчанию: `sensors`).

### Шаг 6: Тестирование скрипта
Запустите скрипт вручную от имени `pet-temp` для проверки:
```bash
sudo -u pet-temp /opt/pet_temp/venv/bin/python /opt/pet_temp/temp_monitor_core.py
```
Проверьте:
- Логи в `/opt/pet_temp/logs/temp_monitor.log`.
- Уведомления в Telegram при температуре > 33°C (🚨) и восстановлении ≤ 30°C (✅).

### Шаг 7: Настройка systemd-сервиса
Создайте systemd unit для запуска скрипта от `pet-temp`:
```bash
sudo nano /etc/systemd/system/pet-temp-monitor.service
```
Добавьте содержимое:
```
[Unit]
Description=Сервис мониторинга температуры Pet Temp
After=network.target

[Service]
User=pet-temp
Group=pet-temp
ExecStart=/opt/pet_temp/venv/bin/python /opt/pet_temp/temp_monitor_core.py
Restart=always

[Install]
WantedBy=multi-user.target
```
Сохраните и активируйте сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl start pet-temp-monitor
sudo systemctl enable pet-temp-monitor
```
Проверьте логи:
```bash
journalctl -u pet-temp-monitor
```

## Логика работы приложения
1. **Чтение температуры**:
   - Выполняет команду `sensors` каждые `INTERVAL_SEC` секунд.
   - Парсит вывод для температуры `Core 0` (измените `get_temperature()` для других сенсоров).
2. **Логирование**:
   - Записывает температуру в `/opt/pet_temp/logs/temp_monitor.log` в формате: `ГГГГ-ММ-ДД ЧЧ:ММ:СС,mmm - Temperature: XX.X°C`.
   - Использует `RotatingFileHandler` для ограничения размера лога (10 МБ, 5 резервных копий).
3. **Уведомления**:
   - Если температура > `THRESHOLD_TEMP` (33°C), отправляет алерт: `🚨 АЛЕРТ: Температура превысила 33°C! Текущая: XX.X°C`.
   - Если температура ≤ `RECOVERY_THRESHOLD` (30°C) после алерта, отправляет восстановление: `✅ ВОССТАНОВЛЕНИЕ: Температура вернулась к норме. Текущая: XX.X°C`.
   - Флаг `alert_triggered` предотвращает дублирование алертов.
4. **Обработка ошибок**:
   - Логирует ошибки при сбоях `sensors` или Telegram API.
   - Продолжает работу даже при ошибках.

## Зависимости
Указаны в `/opt/pet_temp/requirements.txt`:
- `requests==2.32.3`: Для отправки уведомлений в Telegram.
- `python-dateutil==2.9.0`: Для парсинга временных меток логов.

Стандартные библиотеки Python:
- `subprocess`: Выполняет команду `sensors`.
- `logging`: Управляет созданием и ротацией логов.
- `time`: Контролирует интервалы проверки.

## Планы по развитию
- Добавить веб-интерфейс на Flask с графиками Chart.js.
- Поддержка нескольких сенсоров (например, GPU, другие ядра CPU).
- Интеграция с `shoutrrr` для других каналов уведомлений.
- Упаковка в DEB-пакет или Docker-контейнер (на базе Alpine).

## Как внести вклад
Открывайте issues или присылайте pull requests на GitHub. Приветствуются идеи по новым функциям и улучшениям!

## Лицензия
MIT License