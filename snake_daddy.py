import random
import typing
from pathfinding.astarpath import Location
from pathfinding.astarpath import AStarFinder
import json
from pathlib import Path
import time
import logging

def info_daddy():
    return {
        "apiversion": "1",
        "author": "Daddy",  # TODO: Your Battlesnake Username
        "color": "#0066ff",  # TODO: Choose color
        "head": "bendr",  # TODO: Choose head
        "tail": "curled",  # TODO: Choose tail
    }

def get_next_move(current, next_loc):
    if next_loc.x > current.x:
        return "right"
    elif next_loc.x < current.x:
        return "left"
    elif next_loc.y > current.y:
        return "up"
    else: 
        return "down"
    
def get_longest_destination():
    global startLoc, board_width, board_height
    # Get longest destination if there is no food
    destinations = [ 
        Location(0, 0),
        Location(board_width - 1, 0),
        Location(board_width - 1, board_height - 1),
        Location(0, board_height - 1) ]

    longest_index = 0
    for i in range(len(destinations)):
        if startLoc.get_distance(destinations[i]) > startLoc.get_distance(destinations[shortest_index]):
            longest_index = i

    return destinations[longest_index]

def get_distance(dict_loc1, dict_loc2):
    return abs(dict_loc1['x'] - dict_loc2['x']) + abs(dict_loc1['y'] - dict_loc2['y'])

# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move_daddy(game_state: typing.Dict) -> typing.Dict:
    start_time = time.time()
    logFileName = "logs/turn_" + str(game_state["turn"]) + ".json"
    logFilePath = Path(__file__).parent / logFileName
    json_file = open(logFilePath, "w", indent=4)
    json.dump(game_state, json_file)
    json_file.close()

    global my_head, startLoc
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_snake_name = game_state["you"]["name"]
    startLoc = Location(my_head["x"],my_head["y"])
    global board_width, board_height
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    my_body = game_state['you']['body']
    opponents = game_state['board']['snakes']

    # Calculate obstacles   
    is_move_safe = {"up": True, "down": True, "left": True, "right": True} 
    obstacles = []
    my_snake = []
    for snake in opponents:
        # Only add the other snakes as Obstacles
        if snake["name"] != my_snake_name:
            for position in snake["body"]:
                obstacles.append(Location(position["x"],position["y"]))
    
    for part in my_body:
        my_snake.append(Location(part["x"], part["y"]))
    
    print("obstacles: ", obstacles)
    
    print("elapsed time: ", (time.time() - start_time) * 1000)

    # Find a possible path
    print("Start path finding ...")
    next_move = "unknown"

    # First try to make a run to the nearest food
    foods = game_state['board']['food']
    destinations = []
    if (len(foods) > 0):
        nearest_food = foods[0]
        for food in foods:
            if (get_distance(food, my_head) < get_distance(nearest_food, my_head)):
                nearest_food = food

    food_destination = Location(nearest_food['x'], nearest_food['y'])
    food_finder = AStarFinder(my_snake, food_destination, obstacles, board_width, board_height, 2)
    food_path = food_finder.findthepath()
    elapsed_time = (time.time() - start_time) * 1000
    print("elapsed time: ", elapsed_time)
    if (food_path != None and len(food_path) > 1):
        print("Found food path: ", food_path)   
        # Build a future snake 
        future_snake = []
        for i in range (1, len(food_path)):
            future_snake.append(food_path[len(food_path) - i])
        # remainder needs to add 1 because the snake just ate a food
        remainder = len(my_snake) - len(future_snake) + 1
        for i in range(0, remainder):
            future_snake.append(my_snake[i])
        logging.debug("Current snake: %s", my_snake)
        logging.debug("Future snake: %s", future_snake)
        future_tail_finder = AStarFinder(future_snake, future_snake[len(future_snake)-1], obstacles, board_width, board_height, 2)
        future_tail_path = future_tail_finder.findthepath()
        if (future_tail_path != None and len(future_tail_path) > 1):
            print("New path can chase tail")
            # only set next_move when the found path can chase tail
            next_move = get_next_move(food_path[0], food_path[1])
            
    if next_move == "unknown":
        # if we cannot get to a nearest food, then we will chase our tail
        tail_destination = my_snake[len(my_snake)-1]
        tail_finder = AStarFinder(my_snake, tail_destination, obstacles, board_width, board_height, 2)
        tail_path = tail_finder.findthepath()
        if (tail_path != None and len(tail_path) > 1):
            print("Found tail path: ", tail_path)
            next_move = get_next_move(tail_path[0], tail_path[1])  

    # if no path is found then we fall back to a random safe move
    if (next_move == "unknown"):
        if (my_head['x'] == 0):
            is_move_safe["left"] = False
        if (my_head['x'] == board_width-1):
            is_move_safe["right"] = False
        if (my_head['y'] == 0):
            is_move_safe["down"] = False
        if (my_head['y'] == board_height-1):
            is_move_safe["up"] = False
        up_location = Location(startLoc.x, startLoc.y + 1)
        down_location = Location(startLoc.x, startLoc.y - 1)
        left_location = Location(startLoc.x - 1, startLoc.y)
        right_location = Location(startLoc.x + 1, startLoc.y)
        for part in my_snake:
            obstacles.append(part)
        for obs in obstacles:
            if (obs == up_location):
                is_move_safe["up"] = False
            if (obs == down_location):
                is_move_safe["down"] = False
            if (obs == left_location):
                is_move_safe["left"] = False
            if (obs == right_location):
                is_move_safe["right"] = False
        safe_moves = []
        for move, isSafe in is_move_safe.items():
            if isSafe:
                safe_moves.append(move)
        # Initialize next_move with a random move from the safe ones
        next_move = random.choice(safe_moves)
        print("Set random safe move")

    print("elapsed time: ", (time.time() - start_time) * 1000)
    return {"move": next_move}

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    dataFilePath = Path(__file__).parent / "snake_daddy.json"
    rhandle = open(dataFilePath, "r")

    gamestate = json.load(rhandle)
    rhandle.close()
    print(move_daddy(gamestate))