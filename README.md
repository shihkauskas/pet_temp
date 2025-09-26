# Монитор температуры

Инструмент на Python для мониторинга температуры процессора на Linux с использованием `lm-sensors`. Логирует данные, отправляет уведомления в Telegram и предоставляет веб-интерфейс с графиками. Работает как два systemd-сервиса от пользователя `pet-temp`.

## Описание

Проект состоит из двух компонентов:
- **temp_monitor_core.py**: Отслеживает температуру процессора (ядро 0), записывает данные в лог-файл с ротацией и отправляет уведомления в Telegram:
  - При превышении порога (`65°C` по умолчанию) — алерт с 🚨.
  - При возврате к норме (≤ `60°C` по умолчанию) — сообщение о восстановлении с ✅.
- **temp_monitor_web.py**: Flask-сервер, который читает логи и отображает интерактивный график температуры за последние 30 дней (Chart.js, Tailwind CSS).

Логи хранятся в `/opt/pet_temp/logs/temp_monitor.log` с ротацией (макс. 10 МБ, 5 резервных копий).

## Возможности
- Периодическая проверка температуры через `lm-sensors`.
- Логирование в файл с ротацией.
- Уведомления в Telegram о превышении температуры и восстановлении.
- Веб-интерфейс с графиком температуры (зум, тултипы, без года в метках времени).
- Настраиваемые пороги и интервалы проверки.
- Запуск как systemd-сервисы от пользователя `pet-temp`.

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
sudo mv temperature-monitor/temp_monitor_web.py /opt/pet_temp/
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

### Шаг 5: Настройка скриптов
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

### Шаг 6: Тестирование скриптов
Запустите скрипты вручную от имени `pet-temp` для проверки:
```bash
sudo -u pet-temp /opt/pet_temp/venv/bin/python /opt/pet_temp/temp_monitor_core.py
```
```bash
sudo -u pet-temp /opt/pet_temp/venv/bin/python /opt/pet_temp/temp_monitor_web.py
```
Проверьте:
- Логи в `/opt/pet_temp/logs/temp_monitor.log`.
- Уведомления в Telegram при температуре > 33°C (🚨) и восстановлении ≤ 30°C (✅).
- Веб-интерфейс: http://localhost:8080 (график без года в метках).

### Шаг 7: Настройка systemd-сервисов
Создайте два systemd unit’а.

**Для мониторинга (`temp_monitor_core.py`)**:
```bash
sudo nano /etc/systemd/system/pet-temp-monitor.service
```
Добавьте:
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

**Для веб-интерфейса (`temp_monitor_web.py`)**:
```bash
sudo nano /etc/systemd/system/pet-temp-web.service
```
Добавьте:
```
[Unit]
Description=Веб-интерфейс мониторинга температуры Pet Temp
After=network.target

[Service]
User=pet-temp
Group=pet-temp
ExecStart=/opt/pet_temp/venv/bin/python /opt/pet_temp/temp_monitor_web.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Активируйте сервисы:
```bash
sudo systemctl daemon-reload
sudo systemctl start pet-temp-monitor
sudo systemctl start pet-temp-web
sudo systemctl enable pet-temp-monitor
sudo systemctl enable pet-temp-web
```
Проверьте логи:
```bash
journalctl -u pet-temp-monitor
journalctl -u pet-temp-web
```

## Логика работы приложения

### Мониторинг (temp_monitor_core.py)
1. **Чтение температуры**:
   - Выполняет команду `sensors` каждые `INTERVAL_SEC` секунд.
   - Парсит вывод для температуры `Core 0` (измените `get_temperature()` для других сенсоров).
2. **Логирование**:
   - Записывает температуру в `/opt/pet_temp/logs/temp_monitor.log` в формате: `ГГГГ-ММ-ДД ЧЧ:ММ:СС,mmm - Temperature: XX.X°C`.
   - Использует `RotatingFileHandler` (10 МБ, 5 резервных копий).
3. **Уведомления**:
   - Если температура > `THRESHOLD_TEMP` (33°C), отправляет алерт: `🚨 АЛЕРТ: Температура превысила 33°C! Текущая: XX.X°C`.
   - Если температура ≤ `RECOVERY_THRESHOLD` (30°C) после алерта, отправляет восстановление: `✅ ВОССТАНОВЛЕНИЕ: Температура вернулась к норме. Текущая: XX.X°C`.
   - Флаг `alert_triggered` предотвращает дублирование алертов.
4. **Обработка ошибок**:
   - Логирует ошибки `sensors` или Telegram API.
   - Продолжает работу при ошибках.

### Веб-интерфейс (temp_monitor_web.py)
1. Читает логи из `/opt/pet_temp/logs/temp_monitor.log` и ротационных файлов за последние 30 дней.
2. Отображает график температуры (Chart.js) с:
   - Метками времени в формате `день-месяц часы:минуты` (например, `26-09 09:24`).
   - Зумом (колесо мыши, щипок).
   - Тултипами (время и температура).
   - Стилями Tailwind CSS (изумрудная линия, тень, responsive).
3. Работает на порту 8080 (настройте `WEB_PORT` если нужно).

## Зависимости
Указаны в `/opt/pet_temp/requirements.txt`:
- `requests==2.32.3`: Для отправки уведомлений в Telegram.
- `python-dateutil==2.9.0`: Для парсинга временных меток логов.
- `flask==3.0.3`: Для веб-интерфейса.

Стандартные библиотеки Python:
- `subprocess`: Выполняет команду `sensors`.
- `logging`: Управляет созданием и ротацией логов.
- `time`: Контролирует интервалы проверки.

## Планы по развитию
- Поддержка нескольких сенсоров (GPU, другие ядра CPU).
- Интеграция с `shoutrrr` для других каналов уведомлений.
- Упаковка в DEB-пакет или Docker-контейнер (на базе Alpine).

## Как внести вклад
Открывайте issues или присылайте pull requests на GitHub. Приветствуются идеи по новым функциям и улучшениям!

## Лицензия
MIT License
