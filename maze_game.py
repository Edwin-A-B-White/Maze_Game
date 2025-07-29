# maze_game.py

import os  # For file and path operations (leaderboard storage)
import json  # For reading and writing JSON leaderboard data
import random  # For randomizing maze generation
import time  # For animation timing and delays
import PySimpleGUI as sg  # GUI library for drawing and events
import keyboard  # For detecting real-time keyboard input

#CONFIGURATION
CELL_SIZE         = 20     # Size of each maze cell in pixels
MAX_FAILS_PER_MAP = 10     # Maximum number of failed attempts allowed per maze
NUM_MAPS          = 5      # Total number of different mazes to play through
MAZE_WIDTH        = 41     # Maze width in cells (must be odd for proper generation)
MAZE_HEIGHT       = 31     # Maze height in cells (must be odd for proper generation)

#MAZE GENERATOR (perfect maze via recursive backtracker)
def generate_maze(w, h):
    # Initialize grid full of walls (1 represents wall, 0 will represent path)
    grid = [[1] * w for _ in range(h)]

    def carve(r, c):
        # Mark current cell as a path
        grid[r][c] = 0
        # Define possible carve directions: two cells at a time
        dirs = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        random.shuffle(dirs)  # Randomize direction order for unpredictability
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc  # Coordinates two cells away
            # Check if the target is inside bounds and still a wall
            if 0 < nr < h-1 and 0 < nc < w-1 and grid[nr][nc] == 1:
                # Carve the intermediate cell (one step in direction)
                grid[r + dr // 2][c + dc // 2] = 0
                # Recurse into the next cell to continue carving
                carve(nr, nc)

    # Start carving from the entrance at (1,1)
    carve(1, 1)
    # Ensure the exit cell is open
    grid[h-2][w-2] = 0
    return grid

# Pre-generate all mazes for the game
mazes   = [generate_maze(MAZE_WIDTH, MAZE_HEIGHT) for _ in range(NUM_MAPS)]
HEIGHT  = MAZE_HEIGHT  # Alias for easier reference
WIDTH   = MAZE_WIDTH
start_pos = (1, 1)  # Starting cell in maze coordinates (row, col)
exit_pos  = (HEIGHT - 2, WIDTH - 2)  # Exit cell near bottom-right

#HELPER FUNCTIONS
def grid_to_pixel(r, c):
    # Convert maze grid coordinates to pixel coordinates for drawing
    x = c * CELL_SIZE + CELL_SIZE / 2
    y = (HEIGHT - 1 - r) * CELL_SIZE + CELL_SIZE / 2
    return x, y


def animate_move(graph, fig, old_xy, new_xy, steps=8, delay=0.02):
    """Smoothly animate a move from old_xy to new_xy in given steps."""
    dx = (new_xy[0] - old_xy[0]) / steps  # Delta x per step
    dy = (new_xy[1] - old_xy[1]) / steps  # Delta y per step
    for _ in range(steps):
        graph.MoveFigure(fig, dx, dy)  # Move the drawn figure
        window.refresh()               # Refresh GUI to show movement
        time.sleep(delay)              # Pause briefly for animation effect


def draw_map(graph, map_idx, failed_paths):
    # Clear previous drawings
    graph.Erase()
    maze = mazes[map_idx]  # Select the current maze

    # Draw walls as black rectangles
    for r in range(HEIGHT):
        for c in range(WIDTH):
            if maze[r][c] == 1:  # If cell is a wall
                x1, y1 = c * CELL_SIZE, (HEIGHT - 1 - r) * CELL_SIZE
                graph.DrawRectangle(
                    (x1, y1),
                    (x1 + CELL_SIZE, y1 + CELL_SIZE),
                    fill_color='black',
                    line_color='black'
                )

    # Overlay any previously failed paths in red
    for path in failed_paths[map_idx]:
        pts = [grid_to_pixel(r, c) for r, c in path]
        for i in range(len(pts) - 1):
            graph.DrawLine(pts[i], pts[i+1], color='red', width=2)

    # Draw exit flag at exit position
    ex, ey = grid_to_pixel(*exit_pos)
    graph.DrawText('🏁', (ex, ey), font=('Any', int(CELL_SIZE * 0.7)))

    # Draw player start as a blue circle
    pr, pc = start_pos
    px, py = grid_to_pixel(pr, pc)
    player_fig = graph.DrawCircle((px, py), CELL_SIZE * 0.3, fill_color='blue')

    # Return initial player position and the figure for animation
    return pr, pc, player_fig

#SETUP GUI
username = sg.popup_get_text('Enter your username:', 'Maze Game') or 'Anonymous'
sg.theme('DarkBlue3')  # Set window theme

graph = sg.Graph(
    canvas_size=(WIDTH * CELL_SIZE, HEIGHT * CELL_SIZE),
    graph_bottom_left=(0, 0),
    graph_top_right=(WIDTH * CELL_SIZE, HEIGHT * CELL_SIZE),
    key='-G-',
    enable_events=False
)
status = sg.Text('', key='-STATUS-')  # Text element for status updates
layout = [[status], [graph]]
window = sg.Window('Maze Game', layout, return_keyboard_events=True, finalize=True)

#INITIAL GAME STATE
map_index      = 0                             # Current maze index
fail_counts    = [0] * NUM_MAPS                # Fail count per maze
failed_paths   = [[] for _ in range(NUM_MAPS)] # Store paths that led to dead ends
total_attempts = 0                             # Total move attempts across game

# Draw the first maze and place the player
player_row, player_col, player_fig = draw_map(graph, map_index, failed_paths)
current_path = [start_pos]  # Track current path for dead-end detection

#MAIN EVENT LOOP
while True:
    # Update status bar with current progress
    window['-STATUS-'].update(
        f'Map {map_index+1}/{NUM_MAPS}   '
        f'Fails {fail_counts[map_index]}/{MAX_FAILS_PER_MAP}   '
        f'Total Attempts {total_attempts}'
    )

    event, _ = window.read(timeout=100)
    if event in (sg.WIN_CLOSED, 'Exit'):
        break  # Exit the game loop if window is closed or "Exit" pressed

    # Detect sprint (shift key)
    sprint = keyboard.is_pressed('shift')

    # Handle movement keys (WASD)
    dr = dc = 0  # Row and column deltas
    if keyboard.is_pressed('w'): dr = -1
    elif keyboard.is_pressed('s'): dr = +1
    elif keyboard.is_pressed('a'): dc = -1
    elif keyboard.is_pressed('d'): dc = +1

    if dr or dc:
        new_r = player_row + dr
        new_c = player_col + dc
        maze = mazes[map_index]

        # Prevent backtracking onto the immediate previous cell
        if (new_r, new_c) in current_path:
            time.sleep(0.01 if sprint else 0.05)
            continue

        # Check if new position is within bounds and on a path
        if 0 <= new_r < HEIGHT and 0 <= new_c < WIDTH and maze[new_r][new_c] == 0:
            old_xy = grid_to_pixel(player_row, player_col)
            player_row, player_col = new_r, new_c
            new_xy = grid_to_pixel(player_row, player_col)

            # Animate movement (faster if sprinting)
            if sprint:
                animate_move(graph, player_fig, old_xy, new_xy, steps=4, delay=0.005)
            else:
                animate_move(graph, player_fig, old_xy, new_xy)

            # Record this step in the current path
            current_path.append((player_row, player_col))

            # Check for dead-end: count open neighbors
            nbrs = [
                (player_row-1, player_col),
                (player_row+1, player_col),
                (player_row, player_col-1),
                (player_row, player_col+1)
            ]
            free = [
                (r, c) for r, c in nbrs
                if 0 <= r < HEIGHT and 0 <= c < WIDTH and maze[r][c] == 0
            ]
            # Dead-end if no more than one open neighbor and not at exit
            if len(free) <= 1 and (player_row, player_col) != exit_pos:
                # Save the failed path for display
                failed_paths[map_index].append(list(current_path))
                pts = [grid_to_pixel(r, c) for r, c in current_path]
                for i in range(len(pts) - 1):
                    graph.DrawLine(pts[i], pts[i+1], color='red', width=2)

                sg.popup('You hit a dead end and were eaten by trolls!', title='Dead End')
                fail_counts[map_index] += 1
                total_attempts    += 1

                # Check for overall game over condition
                if fail_counts[map_index] >= MAX_FAILS_PER_MAP:
                    sg.popup('10 failures – restarting entire game!', title='Game Over')
                    # Reset all game state
                    map_index      = 0
                    fail_counts    = [0] * NUM_MAPS
                    failed_paths   = [[] for _ in range(NUM_MAPS)]
                    total_attempts = 0

                # Reset player to start of current map
                graph.DeleteFigure(player_fig)
                player_row, player_col = start_pos
                current_path = [start_pos]
                player_row, player_col, player_fig = draw_map(graph, map_index, failed_paths)

        # Check if player reached exit
        elif (player_row, player_col) == exit_pos:
            total_attempts += 1
            map_index     += 1

            # All mazes completed: victory
            if map_index >= NUM_MAPS:
                sg.popup(f'🏆 You Win! 🏆\nTotal attempts: {total_attempts}', title='Victory')
                # Load or initialize leaderboard file
                LB_FILE = 'leaderboard.json'
                lb = json.load(open(LB_FILE)) if os.path.exists(LB_FILE) else {}
                # Update leaderboard if new high score
                if username not in lb or total_attempts < lb[username]:
                    lb[username] = total_attempts
                    json.dump(lb, open(LB_FILE, 'w'), indent=2)
                # Display top 10 scores
                top = sorted(lb.items(), key=lambda x: x[1])[:10]
                msg = '\n'.join(f'{i+1}. {u}: {s} attempts' for i, (u, s) in enumerate(top))
                sg.popup_scrolled(msg, title='🏅 Leaderboard')
                break

            # Otherwise, move to next map
            graph.DeleteFigure(player_fig)
            player_row, player_col = start_pos
            current_path = [start_pos]
            player_row, player_col, player_fig = draw_map(graph, map_index, failed_paths)

        # Add a small delay to control movement speed
        time.sleep(0.01 if sprint else 0.05)

# Close the window and exit cleanly
window.close()
