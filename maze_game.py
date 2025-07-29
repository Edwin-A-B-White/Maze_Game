# maze_game.py

import os
import json
import random
import time
import PySimpleGUI as sg
import keyboard

# —— CONFIGURATION —— #
CELL_SIZE         = 20     # pixels per cell
MAX_FAILS_PER_MAP = 10
NUM_MAPS          = 5
MAZE_WIDTH        = 41     # must be odd
MAZE_HEIGHT       = 31     # must be odd

# —— MAZE GENERATOR (perfect maze via recursive backtracker) —— #
def generate_maze(w, h):
    grid = [[1]*w for _ in range(h)]
    def carve(r, c):
        grid[r][c] = 0
        dirs = [(0,2),(0,-2),(2,0),(-2,0)]
        random.shuffle(dirs)
        for dr, dc in dirs:
            nr, nc = r+dr, c+dc
            if 0 < nr < h-1 and 0 < nc < w-1 and grid[nr][nc] == 1:
                grid[r+dr//2][c+dc//2] = 0
                carve(nr, nc)
    carve(1,1)
    grid[h-2][w-2] = 0  # ensure exit open
    return grid

mazes   = [generate_maze(MAZE_WIDTH, MAZE_HEIGHT) for _ in range(NUM_MAPS)]
HEIGHT  = MAZE_HEIGHT
WIDTH   = MAZE_WIDTH
start_pos = (1,1)
exit_pos  = (HEIGHT-2, WIDTH-2)

# —— HELPERS —— #
def grid_to_pixel(r,c):
    x = c*CELL_SIZE + CELL_SIZE/2
    y = (HEIGHT-1-r)*CELL_SIZE + CELL_SIZE/2
    return x, y

def animate_move(graph, fig, old_xy, new_xy, steps=8, delay=0.02):
    """Smooth cell-to-cell move in steps with delay between frames."""
    dx = (new_xy[0]-old_xy[0])/steps
    dy = (new_xy[1]-old_xy[1])/steps
    for _ in range(steps):
        graph.MoveFigure(fig, dx, dy)
        window.refresh()
        time.sleep(delay)

def draw_map(graph, map_idx, failed_paths):
    graph.Erase()
    maze = mazes[map_idx]
    # walls
    for r in range(HEIGHT):
        for c in range(WIDTH):
            if maze[r][c] == 1:
                x1, y1 = c*CELL_SIZE, (HEIGHT-1-r)*CELL_SIZE
                graph.DrawRectangle((x1,y1),
                                    (x1+CELL_SIZE, y1+CELL_SIZE),
                                    fill_color='black',
                                    line_color='black')
    # past failed routes
    for path in failed_paths[map_idx]:
        pts = [grid_to_pixel(r,c) for r,c in path]
        for i in range(len(pts)-1):
            graph.DrawLine(pts[i], pts[i+1], color='red', width=2)
    # exit flag
    ex, ey = grid_to_pixel(*exit_pos)
    graph.DrawText('🏁', (ex,ey), font=('Any', int(CELL_SIZE*0.7)))
    # player start
    pr, pc = start_pos
    px, py = grid_to_pixel(pr,pc)
    player_fig = graph.DrawCircle((px,py), CELL_SIZE*0.3, fill_color='blue')
    return pr, pc, player_fig

# —— SETUP —— #
username = sg.popup_get_text('Enter your username:', 'Maze Game') or 'Anonymous'
sg.theme('DarkBlue3')
graph = sg.Graph(
    canvas_size=(WIDTH*CELL_SIZE, HEIGHT*CELL_SIZE),
    graph_bottom_left=(0,0),
    graph_top_right=(WIDTH*CELL_SIZE, HEIGHT*CELL_SIZE),
    key='-G-',
    enable_events=False
)
status = sg.Text('', key='-STATUS-')
layout = [[status],[graph]]
window = sg.Window('Maze Game', layout, return_keyboard_events=True, finalize=True)

# —— GAME STATE —— #
map_index      = 0
fail_counts    = [0]*NUM_MAPS
failed_paths   = [[] for _ in range(NUM_MAPS)]
total_attempts = 0

# draw first map
player_row, player_col, player_fig = draw_map(graph, map_index, failed_paths)
current_path = [start_pos]

# —— MAIN LOOP —— #
while True:
    window['-STATUS-'].update(
        f'Map {map_index+1}/{NUM_MAPS}   '
        f'Fails {fail_counts[map_index]}/{MAX_FAILS_PER_MAP}   '
        f'Total Attempts {total_attempts}'
    )

    event, _ = window.read(timeout=100)
    if event in (sg.WIN_CLOSED, 'Exit'):
        break

    # detect sprint
    sprint = keyboard.is_pressed('shift')

    # movement axes
    dr = dc = 0
    if keyboard.is_pressed('w'): dr = -1
    elif keyboard.is_pressed('s'): dr = +1
    elif keyboard.is_pressed('a'): dc = -1
    elif keyboard.is_pressed('d'): dc = +1

    if dr or dc:
        new_r = player_row + dr
        new_c = player_col + dc
        maze = mazes[map_index]

        # block backtracking
        if (new_r, new_c) in current_path:
            time.sleep(0.01 if sprint else 0.05)
            continue

        # valid floor?
        if 0<=new_r<HEIGHT and 0<=new_c<WIDTH and maze[new_r][new_c]==0:
            old_xy = grid_to_pixel(player_row, player_col)
            player_row, player_col = new_r, new_c
            new_xy = grid_to_pixel(player_row, player_col)

            # animate: faster if sprinting
            if sprint:
                animate_move(graph, player_fig, old_xy, new_xy, steps=4, delay=0.005)
            else:
                animate_move(graph, player_fig, old_xy, new_xy)

            current_path.append((player_row, player_col))

            # dead-end?
            nbrs = [(player_row-1,player_col),(player_row+1,player_col),
                    (player_row,player_col-1),(player_row,player_col+1)]
            free = [(r,c) for r,c in nbrs
                    if 0<=r<HEIGHT and 0<=c<WIDTH and maze[r][c]==0]
            if len(free)<=1 and (player_row,player_col)!=exit_pos:
                failed_paths[map_index].append(list(current_path))
                # draw it
                pts = [grid_to_pixel(r,c) for r,c in current_path]
                for i in range(len(pts)-1):
                    graph.DrawLine(pts[i], pts[i+1], color='red', width=2)

                sg.popup('You hit a dead end and were eaten by trolls!', title='Dead End')
                fail_counts[map_index] += 1
                total_attempts    += 1

                if fail_counts[map_index] >= MAX_FAILS_PER_MAP:
                    sg.popup('10 failures – restarting entire game!', title='Game Over')
                    map_index      = 0
                    fail_counts    = [0]*NUM_MAPS
                    failed_paths   = [[] for _ in range(NUM_MAPS)]
                    total_attempts = 0

                # reset
                graph.DeleteFigure(player_fig)
                player_row, player_col = start_pos
                current_path = [start_pos]
                player_row, player_col, player_fig = draw_map(graph, map_index, failed_paths)

        # exit?
        elif (player_row,player_col)==exit_pos:
            total_attempts += 1
            map_index     += 1

            if map_index>=NUM_MAPS:
                sg.popup(f'🏆 You Win! 🏆\nTotal attempts: {total_attempts}', title='Victory')
                # leaderboard
                LB_FILE='leaderboard.json'
                lb = json.load(open(LB_FILE)) if os.path.exists(LB_FILE) else {}
                if username not in lb or total_attempts<lb[username]:
                    lb[username]=total_attempts
                    json.dump(lb, open(LB_FILE,'w'), indent=2)
                top = sorted(lb.items(), key=lambda x:x[1])[:10]
                msg = '\n'.join(f'{i+1}. {u}: {s} attempts' for i,(u,s) in enumerate(top))
                sg.popup_scrolled(msg, title='🏅 Leaderboard')
                break

            # next map
            graph.DeleteFigure(player_fig)
            player_row, player_col = start_pos
            current_path = [start_pos]
            player_row, player_col, player_fig = draw_map(graph, map_index, failed_paths)

        # throttle: almost none if sprinting
        time.sleep(0.01 if sprint else 0.05)

window.close()
