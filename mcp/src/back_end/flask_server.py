from api.routes import app
from util import settings
import logging
import logging.config


if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logging.getLogger().handlers = gunicorn_logger.handlers
    logging.getLogger().setLevel(gunicorn_logger.level)
    logging.info('Running application NOT as main ...')


if __name__ == '__main__':
    config_json = settings.get_logging_config(settings.LOG_SETTING_FILE)
    logging.config.dictConfig(config_json)
    logging.info('Running application as main ...')
    app.run(host='0.0.0.0', port='5000', debug=True)
