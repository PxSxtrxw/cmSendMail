import smtplib
import json
from flask import Flask, request, jsonify
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from logging.handlers import RotatingFileHandler
import logging
from dotenv import load_dotenv
import os
import re

# Cargar variables de entorno desde el archivo .env
load_dotenv()

MAIL_USER = os.getenv('MAIL_USER')
MAIL_PASS = os.getenv('MAIL_PASS')
MAIL_HOST = os.getenv('MAIL_HOST')
MAIL_PORT = int(os.getenv('MAIL_PORT'))
PORT = int(os.getenv('PORT'))

# Configurar el logger
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)
info_handler = RotatingFileHandler(os.path.join(log_dir, 'infoLogger.log'), maxBytes=10000000, backupCount=5)
info_formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
info_handler.setFormatter(info_formatter)
info_logger.addHandler(info_handler)

error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
error_handler = RotatingFileHandler(os.path.join(log_dir, 'errorLogger.log'), maxBytes=10000000, backupCount=5)
error_formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)

# Configurar Flask para evitar mensajes de servidor en la consola
class NoPrintingFlask(Flask):
    def run(self, host=None, port=None, debug=None, load_dotenv=True, **options):
        options['use_evalex'] = False
        super(NoPrintingFlask, self).run(host=host, port=port, debug=debug, load_dotenv=load_dotenv, **options)

app = NoPrintingFlask(__name__)

def send_mail(json_data):
    msg = MIMEMultipart()
    msg['From'] = MAIL_USER
    msg['To'] = ', '.join(json_data['to'])
    msg['Subject'] = json_data['subject']

    if 'html' in json_data:
        msg.attach(MIMEText(json_data['html'], 'html'))
    elif 'text' in json_data:
        msg.attach(MIMEText(json_data['text'], 'plain'))

    if 'cc' in json_data and json_data['cc']:
        msg['Cc'] = ', '.join(json_data['cc'])

    if 'bcc' in json_data and json_data['bcc']:
        msg['Bcc'] = ', '.join(json_data['bcc'])

    if 'attachments' in json_data and json_data['attachments']:
        for file_path in json_data['attachments']:
            if os.path.exists(file_path):
                part = MIMEBase('application', 'octet-stream')
                with open(file_path, 'rb') as attachment:
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file_path)}")
                msg.attach(part)
            else:
                error_logger.error(f'Archivo no encontrado: {file_path}')
                return {'error': f'Archivo no encontrado: {file_path}'}, 400

    try:
        server = smtplib.SMTP_SSL(MAIL_HOST, MAIL_PORT)
        server.login(MAIL_USER, MAIL_PASS)
        server.send_message(msg)
        server.quit()
        print(f'Correo enviado correctamente a: {msg["To"]}')
        return {'message': 'Correo enviado correctamente'}, 200
    except Exception as e:
        error_logger.error(f'Error al enviar el correo: {str(e)}')
        return {'error': 'Error al enviar el correo', 'details': str(e)}, 500

@app.route('/', methods=['POST'])
def index():
    if request.is_json:
        json_data = request.get_json()
        info_logger.info(f'Recibido: {json.dumps(json_data)}')

        required_fields = ['to', 'subject']
        if not all(field in json_data for field in required_fields) or not any(k in json_data for k in ['text', 'html']):
            error_message = 'Faltan campos requeridos en el JSON'
            error_logger.error(error_message)
            return jsonify({'error': error_message}), 400

        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        all_emails_valid = all(
            re.match(email_regex, email) for email in json_data['to']
        ) and all(
            re.match(email_regex, email) for email in json_data.get('cc', [])
        ) and all(
            re.match(email_regex, email) for email in json_data.get('bcc', [])
        )

        if not all_emails_valid:
            error_message = 'Formato de correo electrónico inválido'
            error_logger.error(error_message)
            return jsonify({'error': error_message}), 400

        return send_mail(json_data)
    else:
        error_message = 'Método no permitido'
        error_logger.error(error_message)
        return jsonify({'error': error_message}), 405

if __name__ == '__main__':
    print(f'Servidor corriendo en http://localhost:{PORT}')
    print(f'Cuenta utilizada para enviar el correo: {MAIL_USER}')
    app.run(host='0.0.0.0', port=PORT)
