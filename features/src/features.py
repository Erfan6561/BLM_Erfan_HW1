import pika
import numpy as np
import json
import time
from datetime import datetime
from sklearn.datasets import load_diabetes
 
# Создаём бесконечный цикл для отправки сообщений в очередь
while True:
    try:
        # Загружаем датасет о диабете
        X, y = load_diabetes(return_X_y=True)
        # Формируем случайный индекс строки
        random_row = np.random.randint(0, X.shape[0])  
        # Формируем уникальный идентификатор по метке времени
        message_id = datetime.timestamp(datetime.now())

        # Создаём сообщения
        message_y_true = {
            'id': message_id,
            'body': float(y[random_row])  # Преобразуем значение в float
        }
        message_features = {
            'id': message_id,
            'body': X[random_row].tolist()  # Преобразуем массив в список
        }
 
        # Создаём подключение к RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        channel = connection.channel()
 
        # Создаём очереди, если они не существуют
        channel.queue_declare(queue='y_true', durable=True)  # Добавлено durable=True для сохранения сообщений
        channel.queue_declare(queue='features', durable=True)  # Добавлено durable=True для сохранения сообщений
 
        # Публикуем сообщение в очередь y_true
        channel.basic_publish(
            exchange='',
            routing_key='y_true',
            body=json.dumps(message_y_true),  # Конвертация сообщения в JSON
            properties=pika.BasicProperties(delivery_mode=2)  # Делая сообщение постоянным
        )
        print('Сообщение с правильным ответом отправлено в очередь')
 
        # Публикуем сообщение в очередь features
        channel.basic_publish(
            exchange='',
            routing_key='features',
            body=json.dumps(message_features),
            properties=pika.BasicProperties(delivery_mode=2)  # Делая сообщение постоянным
        )
        print('Сообщение с вектором признаков отправлено в очередь')

        # Задержка перед следующей итерацией
        time.sleep(10)
 
        # Закрываем подключение
        connection.close()
    except Exception as e:  # Уточнение исключения
        print(f'Не удалось подключиться к очереди: {e}')  # Вывод ошибки для упрощения отладки
