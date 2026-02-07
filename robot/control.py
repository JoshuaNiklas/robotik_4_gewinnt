import time
import signal
import socket
import logging
import argparse
import xml.etree.ElementTree as ET

# Constants
ROBOT_IP = "172.31.1.153"
ROBOT_PORT = 6101

MAX_RETRIES = 10
RETRYING_TIME = 3

def setup_logging(verbose_level):
    """Function to setup logging"""
    if verbose_level == 1:  # Show only INFO and higher messages
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.info("Logging level set to: INFO")
    elif verbose_level == 2:  # TODO Show DEBUG and higher messages
        pass
    else:  # Default to INFO
        logging.error("Invalid verbose level, using default INFO.")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

class KukaEKI:
    def __init__(self, ip, port):
        """Initialize the connection parameters"""
        self.ip = ip
        self.port = port
        self.sock = None

    def connect(self):
        """Establish a connection to the robot"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip, self.port))
            logging.info(f"Connected to interface at {self.ip}:{self.port}")
        except socket.error as e:
            logging.error(f"Connection failed: {e}")
            raise

    def close(self):
        """Close the socket connection"""
        if self.sock:
            self.sock.close()
            logging.info("Connection closed")
        else:
            logging.warning("No connection to close")

    def send_xml(self, xml_string):
        """Send an XML string to the robot"""
        try:
            msg = xml_string.encode("utf-8")
            self.sock.sendall(msg)
        except Exception as e:
            logging.error(f"Failed to send message: {e}")
            raise

    def receive_xml(self):
        """Receive an XML string from the robot"""
        try:
            data = self.sock.recv(4096)
            return data.decode("utf-8")
        except Exception as e:
            logging.error(f"Failed to receive message: {e}")
            raise

    def write_variable(self, var_name, value):
        """Write a value to a robot variable"""
        xml = f'<SetVar Name="{var_name}" Value="{value}"/>'
        self.send_xml(xml)
        reply = self.receive_xml()
        logging.info(f"[WRITE VARIABLE] {reply}")
        return reply

    def read_variable(self, var_name):
        """Read a value from a robot variable"""
        xml = f'<ShowVar Name="{var_name}"/>'
        self.send_xml(xml)
        reply = self.receive_xml()
        logging.info(f"[READ VARIABLE] {reply}")
        return xml_to_dict(reply)

def xml_to_dict(xml_string):
    """Convert an XML string to a dictionary of attributes, including the tag name"""
    try:
        root = ET.fromstring(xml_string)
        ret_dict = {**root.attrib, 'Tag': root.tag}
        logging.info(f"[INFO] Converted XML to dict: {ret_dict}")
        return ret_dict
    except ET.ParseError as e:
        logging.error(f"XML Parsing error: {e}")
        raise

def parse_args():
    """Parse cli arguments"""
    parser = argparse.ArgumentParser(description="Kuka Robot Interface")
    parser.add_argument('--verbose', default=1, type=int, choices=[1, 2],
                        help="Set verbosity level (1: INFO, 2: DEBUG, default: 1).")
    parser.add_argument('--no-ui', action='store_true', 
                        help="Run the program without terminal UI (for background execution).")
    return parser.parse_args()

def minimal_terminal_ui(): # TODO
    """Displays the minimal terminal UI using cursor"""
    pass

def attempt_connection(eki):
    """Try to connect to the robot"""
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            eki.connect()
            logging.info("Successfully connected!")
            return True
        except Exception as e:
            logging.error(f"Retry {retry_count + 1} failed: {e}")
            retry_count += 1
            if retry_count < MAX_RETRIES:
                logging.info(f"Retrying in {RETRYING_TIME} seconds... (Attempt {retry_count + 1}/{MAX_RETRIES})")
                time.sleep(RETRYING_TIME)
            else:
                logging.error(f"Maximum retries reached ({MAX_RETRIES}). Exiting.")
                return False
    return False

def handle_exit(signum, frame):
    """Handle exit on Ctrl+C"""
    logging.info("User canceled the operation (Ctrl+C). Exiting...")
    exit(0)

if __name__ == "__main__":
    # Parse the verbosity level and the UI flag from cli
    args = parse_args()
    setup_logging(args.verbose)

    # Register the signal handler
    signal.signal(signal.SIGINT, handle_exit)

    try:
        eki = KukaEKI(ROBOT_IP, ROBOT_PORT)
        
        # Attempt to connect to the robot
        if not attempt_connection(eki):
            logging.error("Failed to connect after multiple attempts, Exiting...")
            exit(1)

        logging.info("Running without Terminal UI...")
        
        SYNC_VAR = int(eki.read_variable("SYNC_VAR").get('Value', 0))
        CELL_SEL = int(eki.read_variable("CELL_SEL").get('Value', -1))

        logging.info(f"SYNC_VAR: {SYNC_VAR}, CELL_SEL: {CELL_SEL}")
        
        # while True:
            # SYNC_VAR = int(eki.read_variable("SYNC_VAR").get('Value', 0))
            # CELL_SEL = int(eki.read_variable("CELL_SEL").get('Value', -1))

            # logging.info(f"SYNC_VAR: {SYNC_VAR}, CELL_SEL: {CELL_SEL}")

            # time.sleep(2000)
            # if (SYNC_VAR % 2 != 0) and (CELL_SEL == -1):
            #     logging.info("Computer Operation detected")
            #     SYNC_VAR += 1
            #     time.sleep(1)
            #     eki.write_variable("CELL_SEL", 0)
            #     eki.write_variable("SYNC_VAR", SYNC_VAR)
            #     time.sleep(1)

    except Exception as e:
        logging.error(f"An error occurred: {e}")

    finally:
        eki.close()
