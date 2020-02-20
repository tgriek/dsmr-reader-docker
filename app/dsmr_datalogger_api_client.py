"""
    https://dsmr-reader.readthedocs.io/en/latest/installation/datalogger.html

    Installation:
        pip3 install pyserial==3.4 requests==2.22.0
"""
import datetime
import logging
import time

import serial
import requests


"""
    These settings are only used when using this script as a dedicated remote datalogger.
"""
DSMR_SERIALPORT = os.environ.get('DSMR_SERIALPORT', '/dev/ttyUSB0')
DSMR_HOST = os.environ.get('DSMR_HOST', '127.0.0.1')
DSMR_APIKEY = os.environ.get('DSMR_APIKEY', 'APIKEY-BLABLABLA-ABCDEFGHI')
DSMR_DSMVERSION = os.environ.get('DSMR_DSMVER', '4')

# Default v4+
SERIAL_BAUDRATE = 115200
SERIAL_BYTESIZE = serial.EIGHTBITS
SERIAL_PARITY = serial.PARITY_EVEN

if DSMR_DSMVERSION == '2':
    SERIAL_BAUDRATE = 9600
    SERIAL_BYTESIZE = serial.SEVENBITS
    SERIAL_PARITY = serial.STOPBITS_ONE

SERIAL_SETTINGS = dict(
    port=DSMR_SERIALPORT,
    baudrate=SERIAL_BAUDRATE,
    bytesize=SERIAL_BYTESIZE,
    parity=SERIAL_PARITY,
    stopbits=serial.STOPBITS_ONE,
    xonxoff=1,
    rtscts=0,
    timeout=20,
)
API_SERVERS = (
    # You can add multiple hosts here... just uncomment the line below.
    ('http://{}/api/v1/datalogger/dsmrreading'.format(DSMR_HOST), '{}'.format(DSMR_APIKEY)),
    # ('http://HOST-OR-IP-2/api/v1/datalogger/dsmrreading', 'APIKEY-2'),
)


def read_serial_port(port, baudrate, bytesize, parity, stopbits, xonxoff, rtscts, timeout):
    """
    Opens the serial port, keeps reading until we have a full telegram and yields the result to preserve the connection.
    """
    logging.info('[%s] Opening serial port: %s', datetime.datetime.now(), port)
    serial_handle = serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=bytesize,
        parity=parity,
        stopbits=stopbits,
        xonxoff=xonxoff,
        rtscts=rtscts,
        timeout=timeout
    )

    telegram_start_seen = False
    buffer = ''

    while True:
        try:
            # Wwe use an infinite datalogger loop and signals to break out of it. Serial
            # operations however do not work well with interrupts, so we'll have to check for E-INTR error.
            data = serial_handle.readline()
        except serial.SerialException as error:
            if str(error) == 'read failed: [Errno 4] Interrupted system call':
                # If we were signaled to stop, we still have to finish our loop.
                continue

            # Something else and unexpected failed.
            raise

        try:
            # Make sure weird characters are converted properly.
            data = str(data, 'utf-8')
        except TypeError:
            pass

        if data.startswith('/'):
            telegram_start_seen = True
            buffer = ''

        if telegram_start_seen:
            buffer += data

        if data.startswith('!') and telegram_start_seen:
            # Keep connection open.
            yield buffer


def send_telegram_to_remote_dsmrreader(telegram, api_url, api_key):
    """ Registers a telegram by simply sending it to the application with a POST request. """
    response = requests.post(
        api_url,
        headers={'Authorization': 'Token {}'.format(api_key)},
        data={'telegram': telegram},
        timeout=60,  # Prevents this script from hanging indefinitely when the server or network is unavailable.
    )

    if response.status_code != 201:
        logging.error('[%s] API error: HTTP %d - %s', datetime.datetime.now(), response.status_code, response.text)


def main():
    """ Entrypoint for command line execution. """
    logging.getLogger().setLevel(logging.INFO)
    logging.info('[%s] Starting...', datetime.datetime.now())

    for telegram in read_serial_port(**SERIAL_SETTINGS):
        logging.info('[%s] Telegram read', datetime.datetime.now())

        for current_server in API_SERVERS:
            current_api_url, current_api_key = current_server
            logging.info('[%s] Sending telegram to: %s', datetime.datetime.now(), current_api_url)

            try:
                send_telegram_to_remote_dsmrreader(
                    telegram=telegram,
                    api_url=current_api_url,
                    api_key=current_api_key
                )
            except Exception as error:
                logging.exception(error)

        time.sleep(SLEEP)


if __name__ == '__main__':  # pragma: no cover
    main()
