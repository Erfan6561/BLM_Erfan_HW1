import pika
import pickle
import numpy as np
import json

# Читаем файл с сериализованной моделью
try:
    with open('myfile.pkl', 'rb') as pkl_file:
        regressor = pickle.load(pkl_file)
    print('Модель успешно загружена')
except Exception as e:
    print(f'Ошибка при загрузке модели: {e}')
    exit(1)

try:
    # Создаём подключение к RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    # Объявляем необходимые очереди
    channel.queue_declare(queue='features', durable=True)  # Установлено durable для сохранения очереди
    channel.queue_declare(queue='y_pred', durable=True)

    # Функция callback для обработки данных из очереди
    def callback(ch, method, properties, body):
        try:
            print(f'Получен вектор признаков: {body}')
            # Распаковываем сообщение
            message = json.loads(body)
            features = message.get('body')
            message_id = message.get('id')

            # Проверяем корректность данных
            if features is None or message_id is None:
                raise ValueError('Сообщение не содержит необходимых данных (id или body)')

            # Преобразуем данные и делаем предсказание
            features_array = np.array(features).reshape(1, -1)
            pred = regressor.predict(features_array)

            # Формируем сообщение с предсказанием
            prediction_message = {
                'id': message_id,
                'y_pred': float(pred[0])  # Преобразуем в float для сериализации
            }

            # Публикуем предсказание в очередь y_pred
            channel.basic_publish(
                exchange='',
                routing_key='y_pred',
                body=json.dumps(prediction_message)
            )
            print(f'Предсказание {prediction_message} отправлено в очередь y_pred')

        except Exception as e:
            print(f'Ошибка в callback: {e}')

    # Подписываемся на очередь features
    channel.basic_consume(
        queue='features',
        on_message_callback=callback,
        auto_ack=True  # Авто подтверждение получения сообщения
    )

    print('...Ожидание сообщений, для выхода нажмите CTRL+C')
    # Запускаем режим ожидания сообщений
    channel.start_consuming()

except Exception as e:
    print(f'Ошибка подключения к RabbitMQ: {e}')

finally:
    # Закрываем соединение при завершении
    if 'connection' in locals() and connection.is_open:
        connection.close()
