from app import create_app
from flask import send_from_directory
import os
import socket
import logging
import netifaces
import qrcode
from io import StringIO


# Custom colored logging formatter
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',    # Blue
        'INFO': '\033[92m',     # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


# Configure logging with colors
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

app = create_app()

# Get absolute path to static directory
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static')

# Serve phone camera HTML
@app.route('/phone')
def phone_camera():
    logger.info("Phone camera page accessed")
    return send_from_directory(STATIC_DIR, 'phone_camera.html')


def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"


def get_all_network_ips():
    """Get IPs for all network interfaces"""
    ips = []
    try:
        for interface in netifaces.interfaces():
            try:
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        ip = addr_info.get('addr')
                        if ip and not ip.startswith('127.'):
                            ips.append((interface, ip))
            except:
                pass
    except:
        pass
    return ips


def generate_qr_code_ascii(url):
    """Generate ASCII art QR code"""
    try:
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make()

        # Use ASCII art rendering
        output = StringIO()
        qr.print_ascii(out=output, invert=True)
        return output.getvalue()
    except Exception as e:
        logger.error(f"Failed to generate QR code: {e}")
        return "[QR code generation failed]"


if __name__ == '__main__':
    # ANSI color codes
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    host = app.config['HOST']
    port = app.config['PORT']
    debug = app.config['DEBUG']
    local_ip = get_local_ip()
    all_ips = get_all_network_ips()

    phone_url = f"http://{local_ip}:{port}/phone"
    qr_code = generate_qr_code_ascii(phone_url)

    print(f"\n{BOLD}{CYAN}🚀 ASSISTIVE CLASSROOM - BACKEND{RESET}")
    print(f"{GREEN}Local:{RESET}   http://localhost:{port}")
    print(f"{GREEN}Network:{RESET} http://{local_ip}:{port}")

    if all_ips and len(all_ips) > 1:
        print(f"{BLUE}Other IPs:{RESET}")
        for interface, ip in all_ips:
            if ip != local_ip:
                print(f"  {interface}: http://{ip}:{port}")

    print(f"\n{MAGENTA}📱 Phone Camera:{RESET} http://{local_ip}:{port}/phone")
    print(f"\n{YELLOW}📷 QR Code:{RESET}")
    print(qr_code)

    print(f"{BLUE}💡 Phone must be on same WiFi • URL changes with network{RESET}\n")

    logger.info(f"Starting Flask app on {host}:{port}")

    app.run(host=host, port=port, debug=debug, threaded=True)
