from flask import Flask, render_template_string, jsonify
from dateutil.parser import parse as parse_date
import datetime
import os

# Конфиг
LOG_FILE = '/opt/pet_temp/logs/temp_monitor.log'
# Количество ротационных файлов
BACKUP_COUNT = 5
# Порт для Flask
WEB_PORT = 8080  

app = Flask(__name__)

def read_logs_last_30_days():
    logs = []
    thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
    files_to_read = [LOG_FILE] + [f"{LOG_FILE}.{i}" for i in range(1, BACKUP_COUNT + 1) if os.path.exists(f"{LOG_FILE}.{i}")]
    for file in files_to_read:
        if os.path.exists(file):
            with open(file, 'r') as f:
                for line in f:
                    try:
                        timestamp_str, message = line.strip().split(' - ', 1)
                        if 'Temperature:' in message:
                            temp = float(message.split(': ')[1].split('°')[0])
                            timestamp = parse_date(timestamp_str)
                            if timestamp >= thirty_days_ago:
                                logs.append({'timestamp': timestamp.strftime('%d-%m %H:%M'), 'temp': temp})
                    except:
                        pass
    # Сортируем по времени (ascending для графика)
    return sorted(logs, key=lambda x: x['timestamp'])

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Монитор температуры</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 font-sans">
    <div class="container mx-auto p-6">
        <h1 class="text-3xl font-bold text-gray-800 mb-8 text-center">Монитор температуры (последние 30 дней)</h1>
        <div class="bg-white p-8 rounded-lg shadow-lg">
            <canvas id="tempChart" class="w-full h-[500px]"></canvas>
        </div>
    </div>
    <script>
        // Регистрируем плагин для тени
        Chart.register({
            id: 'dropshadow',
            beforeDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
                ctx.shadowBlur = 8;
                ctx.shadowOffsetX = 2;
                ctx.shadowOffsetY = 2;
            }
        });

        fetch('/data')
            .then(response => response.json())
            .then(data => {
                const ctx = document.getElementById('tempChart').getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.map(d => d.timestamp),
                        datasets: [{
                            label: 'Температура (°C)',
                            data: data.map(d => d.temp),
                            borderColor: '#10B981',
                            backgroundColor: 'rgba(16, 185, 129, 0.2)',
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#047857',
                            pointBorderColor: '#FFFFFF',
                            pointBorderWidth: 2,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        }]
                    },
                    options: {
                        plugins: {
                            tooltip: {
                                enabled: true,
                                mode: 'nearest',
                                intersect: false,
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleFont: { family: 'Arial', size: 14, weight: 'bold' },
                                bodyFont: { family: 'Arial', size: 12 },
                                padding: 10,
                                callbacks: {
                                    label: function(context) {
                                        return `Температура: ${context.parsed.y}°C`;
                                    },
                                    title: function(context) {
                                        return context[0].label;
                                    }
                                }
                            },
                            zoom: {
                                zoom: {
                                    wheel: { enabled: true },
                                    pinch: { enabled: true },
                                    mode: 'xy'
                                },
                                pan: {
                                    enabled: true,
                                    mode: 'xy'
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: { 
                                    display: true, 
                                    text: 'Время (день-месяц часы:минуты)', 
                                    font: { family: 'Arial', size: 14, weight: 'bold' },
                                    color: '#1F2937'
                                },
                                grid: { display: false },
                                ticks: { font: { family: 'Arial', size: 12 }, color: '#1F2937' }
                            },
                            y: {
                                title: { 
                                    display: true, 
                                    text: 'Температура (°C)', 
                                    font: { family: 'Arial', size: 14, weight: 'bold' },
                                    color: '#1F2937'
                                },
                                grid: { color: '#E5E7EB' },
                                ticks: { font: { family: 'Arial', size: 12 }, color: '#1F2937' },
                                beginAtZero: false
                            }
                        },
                        animation: {
                            duration: 1000,
                            easing: 'easeInOutQuad'
                        },
                        maintainAspectRatio: false
                    }
                });
            });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/data')
def data():
    logs = read_logs_last_30_days()
    return jsonify(logs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=WEB_PORT)
