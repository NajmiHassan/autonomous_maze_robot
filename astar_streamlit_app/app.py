import streamlit as st
from streamlit_drawable_canvas import st_canvas
import numpy as np
import matplotlib.pyplot as plt
from heapq import heappush, heappop
import time

# ---------- Page Configuration ----------
st.set_page_config(layout="wide", page_title="A* Pathfinding Visualizer")

# ---------- Helper Functions ----------
def plot_grid(grid, start, goal, path=None, open_set=None, closed_set=None):
    """
    Plot the grid with start, goal, walls, and optionally path and search progress
    """
    # Create figure with tight layout to reduce whitespace
    fig, ax = plt.subplots(figsize=(5, 5), tight_layout=True)
    
    # Create a colored grid
    colored_grid = np.zeros((grid.shape[0], grid.shape[1], 3))
    
    # White background (empty cells)
    colored_grid[:, :] = [1, 1, 1]
    
    # Black walls
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            if grid[i, j] == 1:
                colored_grid[i, j] = [0, 0, 0]
    
    # Add closed set (red)
    if closed_set:
        for y, x in closed_set:
            if (y, x) != start and (y, x) != goal:
                colored_grid[y, x] = [0.7, 0.3, 0.3]
    
    # Add open set (green)
    if open_set:
        for y, x in open_set:
            if (y, x) != start and (y, x) != goal:
                colored_grid[y, x] = [0.3, 0.7, 0.3]
    
    # Add path (blue)
    if path:
        for y, x in path:
            if (y, x) != start and (y, x) != goal:
                colored_grid[y, x] = [0.3, 0.3, 0.9]
    
    # Plot grid
    ax.imshow(colored_grid, origin="upper")
    
    # Plot start and goal with distinctive markers
    circle_start = plt.Circle((start[1], start[0]), 0.4, color='lime', fill=True)
    circle_goal = plt.Circle((goal[1], goal[0]), 0.4, color='red', fill=True)
    ax.add_patch(circle_start)
    ax.add_patch(circle_goal)
    
    # Remove ticks
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add grid lines
    for i in range(grid.shape[0] + 1):
        ax.axhline(i - 0.5, color='gray', linewidth=0.5)
    for j in range(grid.shape[1] + 1):
        ax.axvline(j - 0.5, color='gray', linewidth=0.5)
    
    return fig

def astar(grid, start, goal, animate=False, animation_speed=0.1):
    """
    A* Pathfinding algorithm with animation support
    Returns: (path, animation_frames) where animation_frames is a list of (path, open_set, closed_set) tuples
    """
    neighbors = [(0, 1), (1, 0), (-1, 0), (0, -1)]  # 4-connectivity
    close_set = set()
    came_from = {}
    gscore = {start: 0}
    fscore = {start: abs(start[0] - goal[0]) + abs(start[1] - goal[1])}
    oheap = []
    heappush(oheap, (fscore[start], start))
    open_set = {start}  # Keep track of what's in the open set
    
    # For animation
    frames = []
    
    while oheap:
        current = heappop(oheap)[1]
        
        # Remove from open set
        open_set.remove(current)
        
        if current == goal:
            data = []
            while current in came_from:
                data.append(current)
                current = came_from[current]
            path = data[::-1]
            
            # Final frame
            if animate:
                frames.append((path, list(open_set), list(close_set)))
            
            return path, frames
            
        close_set.add(current)
        
        for i, j in neighbors:
            neighbor = current[0] + i, current[1] + j
            
            # Check boundaries
            if not (0 <= neighbor[0] < grid.shape[0] and 0 <= neighbor[1] < grid.shape[1]):
                continue
                
            # Check if wall
            if grid[neighbor[0]][neighbor[1]] == 1:
                continue
                
            tentative_g_score = gscore[current] + 1
            
            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, float('inf')):
                continue
                
            if tentative_g_score < gscore.get(neighbor, float('inf')) or neighbor not in open_set:
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g_score
                fscore[neighbor] = tentative_g_score + abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                
                if neighbor not in open_set:
                    heappush(oheap, (fscore[neighbor], neighbor))
                    open_set.add(neighbor)
        
        # Add animation frame
        if animate:
            # Get current partial path for visualization
            partial_path = []
            if current != start:
                temp = current
                partial_path.append(temp)
                while temp in came_from:
                    temp = came_from[temp]
                    partial_path.append(temp)
                partial_path = partial_path[::-1]
            
            frames.append((partial_path, list(open_set), list(close_set)))
            
    # No path found
    return [], frames

# ---------- Main App ----------
def main():
    st.title("🧭 A* Pathfinding Visualizer")
    
    # Two-column layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Grid size slider
        size = st.slider("Grid size", 5, 50, 20)
        cell_size = 20
        canvas_height = cell_size * size
        canvas_width = cell_size * size
        
        # Click mode
        mode = st.radio("Click mode", ["Wall", "Start", "Goal"], horizontal=True)
        
        # Animation controls
        animate = st.checkbox("Animate algorithm", value=True)
        animation_speed = st.slider("Animation speed (delay in seconds)", 0.0, 2.0, 0.1, 0.1)
        
    # Initialize session state
    if "grid" not in st.session_state:
        st.session_state.grid = np.zeros((size, size), dtype=int)
        st.session_state.start = (0, 0)
        st.session_state.goal = (size - 1, size - 1)
        st.session_state.path = []
        st.session_state.frames = []
        st.session_state.current_frame = 0
        st.session_state.animating = False
    
    # Resize grid if size changes
    if st.session_state.grid.shape[0] != size:
        new_grid = np.zeros((size, size), dtype=int)
        # Copy existing grid data to the extent possible
        min_rows = min(st.session_state.grid.shape[0], size)
        min_cols = min(st.session_state.grid.shape[1], size)
        new_grid[:min_rows, :min_cols] = st.session_state.grid[:min_rows, :min_cols]
        
        st.session_state.grid = new_grid
        st.session_state.goal = (size - 1, size - 1)
    
    grid = st.session_state.grid
    start = st.session_state.start
    goal = st.session_state.goal
    
    with col1:
        # Draw canvas
        canvas = st_canvas(
            fill_color="rgba(0, 0, 0, 1)",
            stroke_width=cell_size // 2,
            background_color="#ffffff",
            update_streamlit=True,
            height=canvas_height,
            width=canvas_width,
            drawing_mode="freedraw",
            key="canvas",
        )
        
        # Update grid based on canvas input
        if canvas.json_data is not None:
            if "objects" in canvas.json_data:
                for obj in canvas.json_data["objects"]:
                    cx = int(obj["left"] // cell_size)
                    cy = int(obj["top"] // cell_size)
                    if 0 <= cy < size and 0 <= cx < size:
                        if mode == "Wall":
                            grid[cy][cx] = 1
                        elif mode == "Start":
                            st.session_state.start = (cy, cx)
                        elif mode == "Goal":
                            st.session_state.goal = (cy, cx)
    
    with col2:
        # Controls
        solve_col, clear_col = st.columns(2)
        
        with solve_col:
            if st.button("🔍 Solve A*"):
                st.session_state.animating = False
                path, frames = astar(grid, start, goal, animate=animate, animation_speed=animation_speed)
                st.session_state.path = path
                st.session_state.frames = frames
                st.session_state.current_frame = 0
                
                if path:
                    st.success(f"Path found with length {len(path)}.")
                    if animate and frames:
                        st.session_state.animating = True
                else:
                    st.warning("No path found.")
        
        with clear_col:
            if st.button("🧹 Clear Grid"):
                st.session_state.grid = np.zeros((size, size), dtype=int)
                st.session_state.path = []
                st.session_state.frames = []
                st.session_state.animating = False
                st.rerun()
        
        # Show plot
        if st.session_state.animating and st.session_state.frames:
            # Show animation
            frame_num = st.session_state.current_frame
            if frame_num < len(st.session_state.frames):
                path, open_set, closed_set = st.session_state.frames[frame_num]
                fig = plot_grid(grid, start, goal, path, open_set, closed_set)
                st.pyplot(fig)
                
                # Animation progress
                progress_text = f"Frame {frame_num + 1}/{len(st.session_state.frames)}"
                st.progress(min(1.0, (frame_num + 1) / len(st.session_state.frames)))
                st.text(progress_text)
                
                # Increment frame counter for next iteration
                st.session_state.current_frame += 1
                
                # Use st.empty to create a placeholder for the next frame
                if frame_num + 1 < len(st.session_state.frames):
                    time.sleep(animation_speed)
                    st.rerun()
                else:
                    st.session_state.animating = False
        else:
            # Show final result or empty grid
            fig = plot_grid(grid, start, goal, st.session_state.path)
            st.pyplot(fig)
        
        # Legend
        st.write("### Legend")
        legend_col1, legend_col2, legend_col3, legend_col4 = st.columns(4)
        with legend_col1:
            st.markdown("🟢 **Start**")
        with legend_col2:
            st.markdown("🔴 **Goal**")
        with legend_col3:
            st.markdown("⬛ **Wall**")
        with legend_col4:
            st.markdown("🔵 **Path**")
        
        # Algorithm explanation
        with st.expander("About A* Algorithm"):
            st.markdown("""
                ### How A* Works
                
                The A* algorithm combines the benefits of Dijkstra's algorithm (which guarantees the shortest path) 
                and greedy best-first search (which uses heuristics to speed up the search).
                
                1. **F-score = G-score + H-score**
                   - G-score: Cost from start to current node
                   - H-score: Estimated cost from current node to goal (Manhattan distance)
                
                2. **Open Set**: Nodes to be evaluated (green)
                3. **Closed Set**: Nodes already evaluated (red)
                4. **Path**: The optimal route found (blue)
            """)

if __name__ == "__main__":
    main()