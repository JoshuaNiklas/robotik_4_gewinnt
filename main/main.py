from robot.kukaAPI import KukaAPI
from processing.xmlProcessor import XMLProcessor
from game.game import Game

# Constants
ROBOT_IP = "172.31.1.153"
ROBOT_PORT = 6101

SYNC_VAR = 0

if __name__ == "__main__":

    kuka_api = KukaAPI(ip=ROBOT_IP, port=ROBOT_PORT)
    game = Game()

    try:
        kuka_api.connect()

    except Exception as e:
        print(f"Error connecting to robot: {e}")

    assert kuka_api.is_connected(), "Failed to connect to the robot"

    while True:

        # Robot's turn
        move = game.play_robot()
        kuka_api.send(XMLProcessor.create_set_sync_var(SYNC_VAR))
        kuka_api.send(XMLProcessor.create_set_cell_sell(move))
        SYNC_VAR += 1

        # Player's turn
        move = game.play_player()
        kuka_api.send(XMLProcessor.create_set_sync_var(SYNC_VAR))
        SYNC_VAR += 1

        

    


        