import os
import csv
import random
import math
from PIL import Image

# === Seed for reproducibility ===
SEED = 42
random.seed(SEED)

# === Paths ===
BASE_PATH = os.getcwd()
SIX_OR_NINE_PATH = os.path.join(BASE_PATH, "six_or_nine_task")
STIM_PATH = os.path.join(SIX_OR_NINE_PATH, "stimuli")
RESOURCE_PATH = os.path.join(BASE_PATH, "resources")
FIGURE_PATH = os.path.join(RESOURCE_PATH, "real_figures_standing")
os.makedirs(STIM_PATH, exist_ok=True)

# === Parameters ===
MARGIN = 200
FOV_ANGLE = 60
VIEW_DISTANCE = 5000
N_IMAGES = 100
PLACEMENT_LOCATIONS = ["left","right","front","behind"] # front, behind, left, right and combinations e.g., front_left
ROTATION_ANGLE_MIN = 0 # 0-180 = same as viewer perspective, 181-360 = different to viewer perspective
ROTATION_ANGLE_MAX = 360
ROTATE_NUMBER = True
IMAGE_OUTPUT_SIZE = (400, 400)
FIGURE_SCALE = 1.5
BG_IMG = "background_with_colours.jpg"
USE_ARROW = False
USE_NUMBER = False

# === Utilities ===
def point_in_triangle(px, py, p1, p2, p3):
    denom = (p2[1] - p3[1]) * (p1[0] - p3[0]) + (p3[0] - p2[0]) * (p1[1] - p3[1])
    if abs(denom) < 1e-10:
        return False
    a = ((p2[1] - p3[1]) * (px - p3[0]) + (p3[0] - p2[0]) * (py - p3[1])) / denom
    b = ((p3[1] - p1[1]) * (px - p3[0]) + (p1[0] - p3[0]) * (py - p3[1])) / denom
    c = 1 - a - b
    return all(coord >= 0 for coord in (a, b, c))

def is_in_cone(px, py, cx, cy, cone_angle, fov_angle, distance):
    rot = math.radians(cone_angle)
    half_fov = math.radians(fov_angle) / 2
    apex = (cx, cy)
    left = (cx + distance * math.sin(rot - half_fov), cy + distance * math.cos(rot - half_fov))
    right = (cx + distance * math.sin(rot + half_fov), cy + distance * math.cos(rot + half_fov))
    return point_in_triangle(px, py, apex, left, right)

def get_cone_angle(base_rotation, placement_zone):
    offsets = {
        "front": 90,
        "behind": -90,
        "left": 180,
        "right": 0,
        "front_left": 125,
        "front_right": 55,
        "behind_left": -125,
        "behind_right": -55,
    }
    if placement_zone not in offsets:
        raise ValueError(f"Unknown placement zone: {placement_zone}")
    return (base_rotation + offsets[placement_zone]) % 360

def find_valid_position(bg_size, fg_box, num_size, margin, center, base_rotation, fov, dist, placement_zone):
    bg_w, bg_h = bg_size
    num_w, num_h = num_size
    cone_angle = get_cone_angle(base_rotation, placement_zone)
    for _ in range(2000):
        x = random.randint(margin, bg_w - num_w - margin)
        y = random.randint(margin, bg_h - num_h - margin)
        num_center = (x + num_w // 2, y + num_h // 2)
        num_box = (x, y, x + num_w, y + num_h)
        fg_left, fg_top, fg_right, fg_bottom = fg_box
        overlap = not (num_box[2] < fg_left or num_box[0] > fg_right or
                       num_box[3] < fg_top or num_box[1] > fg_bottom)
        if overlap:
            continue
        if is_in_cone(*num_center, *center, cone_angle, fov, dist):
            return x, y
    raise RuntimeError(f"Couldn't find position in '{placement_zone}' zone after many attempts.")

def calculate_number_rotation(base_angle, as_six, location, jitter_range=10):
    primary = location.split("_")[0]
    offsets = {
        "front": -90 if as_six else 90,
        "behind": 90 if as_six else -90,
        "left": 0 if as_six else 180,
        "right": 180 if as_six else 0,
    }
    offset = offsets.get(primary)
    if offset is None:
        raise ValueError(f"Invalid location: {location}.")
    jitter = random.uniform(-jitter_range, jitter_range)
    return (base_angle + offset + jitter) % 360

def load_image(filename):
    return Image.open(os.path.join(RESOURCE_PATH, filename)).convert("RGBA")

# === Load Assets ===
background = load_image(BG_IMG)
if USE_NUMBER:
    number = load_image("im_of_6.jpg")
else:
    number = load_image("blank.png")
bg_w, bg_h = background.size
figure_files = [f for f in os.listdir(FIGURE_PATH) if f.lower().endswith((".jpg", ".png"))]
if not figure_files:
    raise ValueError("No figure images found.")

# === Metadata File ===
csv_path = os.path.join(STIM_PATH, "metadata.csv")
with open(csv_path, mode="w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=[
        "filename", "image_number","figure_type","margin_size","fov_angle",
        "figure_rotation", "number_rotation",
        "number_position_x", "number_position_y",
        "number_location_x", "number_location_y","relative_location",
        "number_appearance_type","number_appearance",
    ])
    writer.writeheader()

    for i in range(N_IMAGES):
        # Randomize properties
        if USE_ARROW:
            figure_file = "arrow.png"
            figure = Image.open(os.path.join(RESOURCE_PATH, figure_file)).convert("RGBA")
        else:
            figure_file = random.choice(figure_files)
            figure = Image.open(os.path.join(FIGURE_PATH, figure_file)).convert("RGBA")
        figure = figure.transpose(Image.ROTATE_90)
        figure_angle = random.uniform(ROTATION_ANGLE_MIN, ROTATION_ANGLE_MAX)
        appears_as_six = random.choice([True, False])
        placement_zone = random.choice(PLACEMENT_LOCATIONS)

        # Prep geometry
        fg_w, fg_h = figure.size
        figure = figure.resize((int(fg_w * FIGURE_SCALE), int(fg_h * FIGURE_SCALE)), resample=Image.LANCZOS)
        fg_x, fg_y = (bg_w - fg_w) // 2, (bg_h - fg_h) // 2
        figure_box = (fg_x, fg_y, fg_x + fg_w, fg_y + fg_h)
        figure_center = (fg_x + fg_w // 2, fg_y + fg_h // 2)

        # Rotate number
        if ROTATE_NUMBER:
            number_appearance_type = "figure_perspective"
            number_angle = calculate_number_rotation(figure_angle, appears_as_six, placement_zone, jitter_range=20)
        else:
            number_appearance_type = "viewer_perspective"
            number_angle = calculate_number_rotation(0, appears_as_six, "left", jitter_range=20)

        num_position = find_valid_position(
            (bg_w, bg_h), figure_box, number.size, MARGIN,
            figure_center, figure_angle, FOV_ANGLE, VIEW_DISTANCE,
            placement_zone
        )

        # Composite
        figure_rotated = figure.rotate(figure_angle, expand=True)
        number_rotated = number.rotate(number_angle, expand=True)
        fg_x = (bg_w - figure_rotated.size[0]) // 2
        fg_y = (bg_h - figure_rotated.size[1]) // 2
        composed = background.copy()
        composed.paste(figure_rotated, (fg_x, fg_y), figure_rotated)
        composed.paste(number_rotated, num_position, number_rotated)

        # Save
        appearance = "6" if appears_as_six else "9"
        filename = f"image_{i:03d}_{placement_zone}.jpg"
        output_path = os.path.join(STIM_PATH, filename)
        resized = composed.resize(IMAGE_OUTPUT_SIZE, resample=Image.LANCZOS)
        resized.convert("RGB").save(output_path)

        # Write metadata
        scale_x = IMAGE_OUTPUT_SIZE[0] / bg_w
        scale_y = IMAGE_OUTPUT_SIZE[1] / bg_h
        scaled_num_x = round(num_position[0] * scale_x)
        scaled_num_y = round(num_position[1] * scale_y)
        figure_type = figure_file.split(".")[0]
        resized_center_x = IMAGE_OUTPUT_SIZE[0] // 2
        resized_center_y = IMAGE_OUTPUT_SIZE[1] // 2
        resized_num_center_x = scaled_num_x + int(number.size[0] * scale_x / 2)
        resized_num_center_y = scaled_num_y + int(number.size[1] * scale_y / 2)
        number_location_x = "left" if resized_num_center_x < resized_center_x else "right"
        number_location_y = "top" if resized_num_center_y < resized_center_y else "bottom"

        writer.writerow({
            "filename": filename,
            "image_number": i,
            "figure_type": figure_type,
            "figure_rotation": round(figure_angle, 2),
            "number_rotation": round(number_angle, 2),
            "number_position_x": scaled_num_x,
            "number_position_y": scaled_num_y,
            "number_location_x": number_location_x,
            "number_location_y": number_location_y,
            "relative_location": placement_zone,
            "number_appearance_type": number_appearance_type,
            "number_appearance": appearance,
            "margin_size": MARGIN,
            "fov_angle": FOV_ANGLE,
        })

