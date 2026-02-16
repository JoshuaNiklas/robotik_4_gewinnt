import socket
import logging

#Name = Agilus / BA KR AGILUS six V10
# Constants
ROBOT_IP = "172.31.1.153"
ROBOT_PORT = 6101

MAX_RETRIES = 10
RETRYING_TIME = 3

class KukaAPI:

    def __init__(self, ip=ROBOT_IP, port=ROBOT_PORT):
        """Initialize the connection parameters"""
        self.ip = ip
        self.port = port
        self.socket = None

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

    def send(self, message):
        """Send a message (string) to the robot"""
        try:
            msg = message.encode("utf-8")
            self.sock.sendall(msg)
        except Exception as e:
            logging.error(f"Failed to send message: {e}")
            raise

    def receive(self):
        """Receive a message (string) from the robot"""
        try:
            message = self.sock.recv(4096)
            return message.decode("utf-8")
        except Exception as e:
            logging.error(f"Failed to receive message: {e}")
            raise

    def is_connected(self):
        """Check if the socket is connected"""
        return self.sock is not None
