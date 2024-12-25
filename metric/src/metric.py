import pika
import json
import csv
import os

# Убедимся, что папка для логов существует
log_dir = './logs'
os.makedirs(log_dir, exist_ok=True)  # Создаем папку, если её нет

# Путь к файлу лога
log_file = os.path.join(log_dir, 'metric_log.csv')  

# Проверяем, существует ли файл, и создаём его с заголовками, если это не так
if not os.path.exists(log_file) or os.stat(log_file).st_size == 0:
    with open(log_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'y_true', 'y_pred', 'absolute_error'])  # Заголовки

# Инициализируем структуру для хранения сообщений
messages = {}

try:
    # Создаём подключение к серверу RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    # Объявляем очереди
    channel.queue_declare(queue='y_true', durable=True)  # Добавлено durable=True для сохранения очереди
    channel.queue_declare(queue='y_pred', durable=True)  # Добавлено durable=True для сохранения очереди

    # Функция для записи данных в CSV
    def log_to_csv(message_id, y_true, y_pred):
        try:
            absolute_error = abs(y_true - y_pred)
            with open(log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([message_id, y_true, y_pred, absolute_error])
            print(f'Записано в лог: id={message_id}, y_true={y_true}, y_pred={y_pred}, error={absolute_error}')
        except Exception as e:
            print(f'Ошибка записи в CSV: {e}')

    # Callback для обработки сообщений из очередей
    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
            message_id = data.get('id')
            
            # Обработка сообщений y_true
            if method.routing_key == 'y_true':
                value = data.get('body') 
                messages.setdefault(message_id, {})['y_true'] = value
            # Обработка сообщений y_pred
            elif method.routing_key == 'y_pred':
                value = data.get('y_pred') 
                messages.setdefault(message_id, {})['y_pred'] = value

            # Проверяем наличие и y_true, и y_pred для логирования
            if 'y_true' in messages[message_id] and 'y_pred' in messages[message_id]:
                log_to_csv(
                    message_id,
                    messages[message_id]['y_true'],
                    messages[message_id]['y_pred']
                )
                # Удаляем запись после логирования
                del messages[message_id]

        except Exception as e:
            print(f'Ошибка обработки сообщения: {e}')

    # Подписываемся на очереди
    channel.basic_consume(queue='y_true', on_message_callback=callback, auto_ack=True)
    channel.basic_consume(queue='y_pred', on_message_callback=callback, auto_ack=True)

    # Запускаем режим ожидания сообщений
    print('...Ожидание сообщений, для выхода нажмите CTRL+C')
    channel.start_consuming()

except Exception as e:
    print(f'Ошибка подключения или обработки: {e}')

finally:
    # Закрываем соединение при завершении
    if 'connection' in locals() and connection.is_open:
        connection.close()
