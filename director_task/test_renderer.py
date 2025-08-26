#!/usr/bin/env python3
"""
Test script for the 2D grid renderer
"""

from director_task.grid import Grid
from director_task.renderer_2d import GridRenderer2D
from director_task.item import Item
from PIL import Image


def main():
    # Create a 4x4 grid with some blocked cells
    grid = Grid(4, 4)
    
    # Add some blocked cells to test the rendering
    grid.set_blocked(1, 2, True)
    grid.set_blocked(2, 1, True)
    grid.set_blocked(0, 3, True)
    grid.set_blocked(3, 0, True)
    
    print("Created grid with blocked cells at: (1,2), (2,1), (0,3), (3,0)")
    
    # Load items from JSON
    items = Item.load_from_json("director_task/items.json")
    red_star = items[0]  # Should be the red star
    print(f"Loaded item: {red_star.name}")
    grid.item_grid[2][0] = red_star
    
    # Create renderer and render the grid
    renderer = GridRenderer2D()
    print("Rendering grid...")
    
    img = renderer.render_grid(grid)
    
    
    # Save the test image
    output_path = "test_grid_rectangular.png"
    img.save(output_path)
    print(f"Saved rendered grid to: {output_path}")
    
    # Test item positioning and sizing
    print(f"\nItem size for scaling: {renderer.get_item_size()} pixels")
    print("\nTesting item positioning:")
    for row in range(2):
        for col in range(2):
            x, y = renderer.get_item_position(row, col)
            print(f"Grid position ({row},{col}) -> Image position ({x},{y})")


if __name__ == "__main__":
    main()