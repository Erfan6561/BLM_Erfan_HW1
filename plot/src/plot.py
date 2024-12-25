import pandas as pd
import matplotlib.pyplot as plt
import time
import os

# Путь к файлу логов и к файлу с изображением
log_file = './logs/metric_log.csv'
output_image = './logs/error_distribution.png'

# Создаём папку logs, если её нет
os.makedirs(os.path.dirname(log_file), exist_ok=True)

print('Сервис plot запущен. Ожидание данных в metric_log.csv...')

while True:
    try:
        # Проверяем, существует ли файл log_file
        if os.path.exists(log_file):
            # Читаем данные из CSV
            data = pd.read_csv(log_file)

            if 'absolute_error' in data.columns and not data.empty:
                # Получаем данные абсолютных ошибок
                absolute_errors = data['absolute_error']

                # Создаём гистограмму
                plt.figure(figsize=(10, 6))
                plt.hist(absolute_errors, bins=20, color='blue', alpha=0.7, edgecolor='black')
                plt.title('Distribution of Absolute Errors', fontsize=16)
                plt.xlabel('Absolute Error', fontsize=14)
                plt.ylabel('Frequency', fontsize=14)
                plt.grid(axis='y', linestyle='--', alpha=0.7)

                # Сохраняем график в файл
                plt.savefig(output_image)
                plt.close()
                print(f'Гистограмма обновлена: {output_image}')
            else:
                print('Данные об абсолютных ошибках отсутствуют или файл пуст.')
        else:
            print('Файл metric_log.csv ещё не создан.')

    except Exception as e:
        print(f'Ошибка при обработке данных: {e}')

    # Задержка перед следующим циклом
    time.sleep(10)
