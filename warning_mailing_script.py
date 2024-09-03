import smtplib
import socket
import os
import imaplib
import email
from email.utils import parsedate_to_datetime
from email.mime.text import MIMEText
from datetime import datetime, timezone

# Налаштування для ukr.net
SMTP_SERVER = 'smtp.ukr.net'
SMTP_PORT = 465
IMAP_SERVER = 'imap.ukr.net'
IMAP_PORT = 993
EMAIL_ADDRESS = 'evgenia_print24@ukr.net'
EMAIL_PASSWORD = '8goTEc4DeJunvNdK'  # пароль для ІМАР доступу

# Файли для збереження стану та логування
STATE_FILE = 'power_status.txt'
LOG_FILE = 'client_log.txt'
LAST_CHECK_FILE = 'last_check.txt'

# Перевірка і створення файлів, якщо вони відсутні
if not os.path.exists(STATE_FILE):
    open(STATE_FILE, 'w').close()  # Створити порожній файл

if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'w').close()  # Створити порожній файл

if not os.path.exists(LAST_CHECK_FILE):
    # Встановлюємо час останньої перевірки на поточний час в UTC
    with open(LAST_CHECK_FILE, 'w') as f:
        f.write(datetime(1970, 1, 1, tzinfo=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000'))

# Функція для перевірки наявності електроживлення
def is_power_on():
    try:
        print("Перевірка електроживлення...")
        socket.create_connection(("217.76.200.142", 53), timeout=10)
        print("Електроживлення в наявності.")
        return True
    except OSError as e:
        print(f"Відсутність електроживлення або проблеми з підключенням: {e}")
        return False

# Функція для надсилання повідомлення
def send_email(recipient_email, subject):
    print(f"Підготовка до відправки листа на {recipient_email} з темою '{subject}'...")

    # HTML повідомлення зі стилізацією
    html_body = """
    <html>
        <body style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
            <p>В даний момент електроживлення відсутнє.</p>
            <p>Ми обробимо ваше замовлення, як тільки це стане можливим.</p>
            <p>Орієнтовні години роботи відповідно до графіка відключень:</p>
            <pre>
                пн        10:00 11:00 12:00 13:00 14:00 15:00 16:00
                вт                          13:00 14:00 15:00 16:00 17:00 18:00
                ср   9:00 10:00 11:00 12:00 13:00                   16:00 17:00 18:00
                чт        10:00 11:00 12:00 13:00 14:00 15:00 16:00
                пт                          13:00 14:00 15:00 16:00 17:00 18:00       
            </pre>
            <p>Дякуємо за розуміння, з повагою, <strong>репро24</strong></p>
        </body>
    </html>
    """

    # Створюємо MIME-повідомлення з типом text/html
    msg = MIMEText(html_body, 'html')
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

def test_imap_connection():
    try:
        print("Перевірка підключення до IMAP сервера...")
        with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as mail:
            mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            print("Підключення успішне!")
    except imaplib.IMAP4.error as e:
        print(f"Помилка підключення: {e}")

# Виклик функції для тестування
test_imap_connection()

# Функція для перевірки нових листів і відправки повідомлення
def check_and_reply():
    print("Перевірка нових листів...")
    
    power_status = is_power_on()

    # Зчитування часу останньої перевірки
    with open(LAST_CHECK_FILE, 'r') as f:
        last_check_time = parsedate_to_datetime(f.read().strip())

    with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as mail:
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select('inbox')

        # Шукаємо всі непрочитані листи
        status, response = mail.search(None, '(UNSEEN)')
        email_ids = response[0].split()

        latest_msg_date = last_check_time  # Ініціалізуємо останній час перевірки

        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    from_email = msg['from']
                    to_email = msg['to']
                    cc_email = msg.get('cc', '')  # Може бути None, тому за замовчуванням порожній рядок

                    # Перевірка дати листа
                    msg_date = parsedate_to_datetime(msg['Date'])
                    if msg_date <= last_check_time:
                        continue  # Пропускаємо старі листи

                    # Оновлюємо latest_msg_date, якщо поточний лист новіший
                    if msg_date > latest_msg_date:
                        latest_msg_date = msg_date

                    # Перевірка, чи лист був переадресований
                    if to_email != EMAIL_ADDRESS and (EMAIL_ADDRESS in to_email or EMAIL_ADDRESS in cc_email):
                        print(f"Лист від {from_email} переадресовано вам. Підготовка автовідповіді...")
                        
                        if not power_status:
                            subject_reply = "Попередження: відсутність електроживлення"
                            send_email(from_email, subject_reply)
                            log_client(from_email)

                        mail.store(e_id, '+FLAGS', '\\Seen')

    # Оновлення часу останньої перевірки
    with open(LAST_CHECK_FILE, 'w') as f:
        f.write(latest_msg_date.strftime('%a, %d %b %Y %H:%M:%S +0000'))

    print("Перевірка завершена.")

# Виклик функції
check_and_reply()
