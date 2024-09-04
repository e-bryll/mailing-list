import smtplib
import socket
import os
from email.mime.text import MIMEText

# Налаштування для ukr.net
SMTP_SERVER = 'smtp.ukr.net'
SMTP_PORT = 465
EMAIL_ADDRESS = 'evgenia_print24@ukr.net'
EMAIL_PASSWORD = 'yJRLZt0zjFYAz7jJ'  # пароль для ІМАР доступу

# Файл для збереження стану та логування
STATE_FILE = 'power_status.txt'
LOG_FILE = 'client_log.txt'

# Перевірка і створення файлів, якщо вони відсутні
if not os.path.exists(STATE_FILE):
    with open(STATE_FILE, 'w') as f:
        f.write('on')  # Ініціалізація початкового стану як 'on'

if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'w').close()  # Створити порожній файл


# Функція для перевірки наявності електроживлення
def is_power_on():
    try:
        print("Перевірка електроживлення...")
        # Спроба підключитися до вашого комп'ютера через публічну IP-адресу
        socket.create_connection(("217.76.200.142", 53), timeout=10)
        print("Електроживлення в наявності.")
        return True
    except OSError as e:
        print(f"Відсутність електроживлення або проблеми з підключенням: {e}")
        return False

# Функція для надсилання повідомлення
def send_email(recipient_email, subject, body):
    print(f"Підготовка до відправки листа на {recipient_email} з темою '{subject}'...")
    msg = MIMEText(body)
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient_email
    msg['Subject'] = subject

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            print("Підключення до SMTP-сервера...")
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())
        print("Лист успішно відправлено.")
    except Exception as e:
        print(f"Помилка при відправці листа: {e}")

# Функція для логування клієнтів
def log_client(email):
    try:
        print(f"Логування клієнта: {email}")
        with open(LOG_FILE, 'a') as f:
            f.write(f'{email}\n')
        print("Логування завершено.")
    except Exception as e:
        print(f"Помилка при логуванні клієнта: {e}")

# Функція для перевірки і відправки повідомлення
def auto_reply(client_email):
    print("Розпочато роботу автовідповідача...")
    power_status = is_power_on()
    
    # Збереження стану електроживлення
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            last_status = f.read().strip()
            print(f"Попередній стан електроживлення: {last_status}")
    else:
        last_status = None
        print("Файл стану не знайдено, вважається, що попереднього стану немає.")
    
    if not power_status and last_status != 'off':
        print("Відправлення попередження про відсутність електроживлення...")
        subject = "Попередження: відсутність електроживлення"
        body = "В даний момент ми не можемо відповісти на ваш лист через відсутність електроживлення. Ми зв'яжемося з вами, як тільки це стане можливим."
        send_email(client_email, subject, body)
        log_client(client_email)
        
    # Оновлення стану електроживлення
    try:
        with open(STATE_FILE, 'w') as f:
            f.write('off' if not power_status else 'on')
        print(f"Стан електроживлення оновлено: {'off' if not power_status else 'on'}")
    except Exception as e:
        print(f"Помилка при оновленні стану електроживлення: {e}")

# Виклик функції
client_email = 'evgenia_print24@ukr.net'  # Замість цього використовуйте реальну адресу клієнта
auto_reply(client_email)
