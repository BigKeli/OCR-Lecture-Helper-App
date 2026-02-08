from app import create_app
import logging


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',
        'INFO': '\033[92m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'CRITICAL': '\033[95m',
    }
    RESET = '\033[0m'

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    host = app.config['HOST']
    port = app.config['PORT']
    debug = app.config['DEBUG']

    print(f"\n\033[1m\033[96mAssistive Classroom - Backend API\033[0m")
    print(f"\033[92mRunning on:\033[0m http://{host}:{port}")
    print(f"\033[94mHealth check:\033[0m http://localhost:{port}/health\n")

    logger.info(f"Starting Flask app on {host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)
