# Six or Nine Task

A visual perspective-taking experiment that tests whether models can understand spatial relationships and perspective-dependent interpretation of ambiguous stimuli. The task uses images containing figures (people or arrows) and ambiguous numbers that can appear as either "6" or "9" depending on viewing angle.

## Overview

This task evaluates models' ability to:
- Take the perspective of figures in images
- Understand spatial relationships (front/behind, left/right)
- Interpret ambiguous visual stimuli based on viewpoint
- Distinguish between viewer perspective and figure perspective

The experiment generates composite images with figures and numbers positioned according to field-of-view constraints, creating scenarios where the correct answer depends on understanding spatial perspective.

## Setup

Run these commands from the repository root:

```bash
# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .

# Change to the six_or_nine_task directory
cd six_or_nine_task
```

## Quick Start

### 1. Generate Stimuli

```bash
python generate_stimuli.py
```

This creates:
- Visual stimuli images in `stimuli/` directory
- Metadata CSV with positioning and rotation information

### 2. Create Experiment File

```bash
python create_experiment_file.py
```

Processes stimuli metadata and combines with prompt templates to create evaluation-ready datasets.

### 3. Run Evaluation

```bash
# From repository root
inspect eval six_or_nine_task/task.py@six_or_nine_task --model <model_name>
```

### 4. Analyze Results

```bash
python analyse_results.py
```

Generates performance visualizations and accuracy metrics.

## Task Structure

### Stimulus Generation

The task generates composite images with:

- **Background**: Colored background with spatial reference points
- **Figures**: People or arrows positioned in the center
- **Numbers**: Ambiguous 6/9 stimuli placed in various positions relative to figures

Key parameters (configurable in `generate_stimuli.py`):
- `N_IMAGES`: Number of stimuli to generate (default: 100)
- `FOV_ANGLE`: Field-of-view constraint angle (default: 60°)
- `PLACEMENT_LOCATIONS`: Spatial zones for number placement
- `ROTATION_ANGLE_MIN/MAX`: Figure rotation range
- `FIGURE_SCALE`: Size scaling for figures

### Experimental Conditions

The task includes multiple stimulus sets defined in `prompts.csv`:

1. **Control Conditions**:
   - `control_1`: Basic number identification from viewer perspective
   - `control_2/3`: Figure orientation relative to colored walls

2. **Test Conditions**:
   - `level_1`: Visibility testing (can the figure see the number?)
   - `level_2`: Perspective-dependent number interpretation

### Question Types

Each stimulus set supports two question types:

- **Visual Perspective**: What does the figure see?
- **Spatial Perspective**: Spatial relationships from figure's viewpoint

## File Structure

### Core Scripts

- **`generate_stimuli.py`**: Creates visual stimuli with configurable parameters
  - Implements field-of-view constraints using cone geometry
  - Handles figure and number positioning with collision detection
  - Generates metadata for each stimulus

- **`create_experiment_file.py`**: Prepares data for model evaluation
  - Combines stimuli metadata with prompt templates
  - Extracts correct answers based on stimulus properties
  - Creates batch files for different experimental conditions

- **`analyse_results.py`**: Performance analysis and visualization
  - Processes model evaluation results
  - Generates accuracy plots by stimulus set and rotation angle
  - Supports comparative analysis across models

- **`task.py`**: Inspect AI integration
  - Defines evaluation task structure
  - Provides system messages and scoring functions
  - Handles image presentation to models

### Configuration Files

- **`prompts.csv`**: Defines experimental conditions and prompts
  - Stimulus set definitions with visual/spatial question variants
  - Correct answer column mappings
  - Context descriptions for each condition

### Generated Data

- **`stimuli/`**: Generated stimulus images and metadata
  - `image_XXX_YYYY.jpg`: Stimulus images (XXX = number, YYYY = placement)
  - `metadata.csv`: Detailed positioning and rotation data

- **`results/`**: Model evaluation outputs (created during evaluation)

## Key Algorithms

### Field-of-View Constraints

The task uses cone geometry to simulate realistic field-of-view limitations:

```python
def is_in_cone(px, py, cx, cy, cone_angle, fov_angle, distance):
    # Determines if point (px, py) is within figure's field of view
    # Uses triangular cone projection based on figure position and orientation
```

### Perspective-Dependent Number Rotation

Numbers are rotated based on spatial relationships to create ambiguous 6/9 stimuli:

```python
def calculate_number_rotation(base_angle, as_six, location, jitter_range=10):
    # Calculates number orientation to appear as 6 or 9 from figure's perspective
    # Accounts for placement zone and desired interpretation
```

### Spatial Zone Mapping

Converts abstract spatial concepts to image coordinates:

```python
def get_cone_angle(base_rotation, placement_zone):
    # Maps spatial zones (front, behind, left, right) to viewing angles
    # Handles complex zones like "front_left", "behind_right"
```

## Evaluation Metrics

The task provides several analysis dimensions:

1. **Accuracy by Stimulus Set**: Performance across different experimental conditions
2. **Rotation Analysis**: Accuracy vs. figure rotation angle
3. **Question Type Comparison**: Visual vs. spatial perspective performance
4. **Spatial Zone Analysis**: Performance by number placement location

## Customization

### Modifying Generation Parameters

Edit constants in `generate_stimuli.py`:

```python
# Image generation parameters
N_IMAGES = 100                    # Number of stimuli
FOV_ANGLE = 60                    # Field-of-view constraint
PLACEMENT_LOCATIONS = ["left", "right", "front", "behind"]
ROTATION_ANGLE_MIN = 0            # Figure rotation range
ROTATION_ANGLE_MAX = 360
IMAGE_OUTPUT_SIZE = (400, 400)    # Output image dimensions
```

### Adding New Experimental Conditions

1. Add new rows to `prompts.csv` with stimulus set definition
2. Update `create_experiment_file.py` to handle new answer extraction logic
3. Modify `analyse_results.py` to include new conditions in analysis

### Using Different Figure Types

Configure figure selection in `generate_stimuli.py`:

```python
USE_ARROW = False     # Use arrow figures instead of people
FIGURE_PATH = "path/to/your/figures"  # Custom figure directory
```

## Dependencies

- **PIL (Pillow)**: Image processing and composition
- **pandas**: Data manipulation and CSV handling
- **seaborn/matplotlib**: Statistical visualization
- **numpy**: Numerical computations
- **inspect_ai**: Evaluation framework integration

## Validation

The task includes built-in validation:

- Collision detection prevents figure-number overlap
- Field-of-view verification ensures spatial constraints
- Metadata consistency checks validate generation parameters
- Answer extraction validation for all experimental conditions

## Troubleshooting

**Common Issues:**

1. **Missing figures**: Ensure figure images exist in `resources/real_figures_standing/`
2. **Generation failures**: Check placement constraints and increase attempt limits
3. **Evaluation errors**: Verify prompt templates match expected answer formats
4. **Analysis issues**: Ensure result files follow expected naming convention

**Performance Tips:**

- Reduce `N_IMAGES` for faster testing
- Adjust `MARGIN` to increase valid placement area
- Use smaller `IMAGE_OUTPUT_SIZE` for faster processing
- Enable parallel processing for large datasets