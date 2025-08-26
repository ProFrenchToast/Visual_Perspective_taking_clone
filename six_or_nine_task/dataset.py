import json
import os
import random
import math
import csv
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, validator, ValidationError
from PIL import Image


# Pydantic validation models for dataset structure
class StimulusMetadataModel(BaseModel):
    """Metadata for a single stimulus image."""
    filename: str
    image_number: int
    figure_type: str
    margin_size: int
    fov_angle: int
    figure_rotation: float
    number_rotation: float
    number_position_x: int
    number_position_y: int
    number_location_x: str  # "left" or "right"
    number_location_y: str  # "top" or "bottom"
    relative_location: str  # placement zone like "front", "behind", etc.
    number_appearance_type: str  # "figure_perspective" or "viewer_perspective"
    number_appearance: str  # "6" or "9"


class PromptSetModel(BaseModel):
    """Configuration for a stimulus set from prompts.csv."""
    stimulus_set: str
    visual_prompt: str
    spatial_prompt: str
    visual_correct_answer_column: str
    spatial_correct_answer_column: str
    context_prompt: str


class SampleModel(BaseModel):
    """A complete sample including stimulus, prompts, and correct answers."""
    sample_id: int
    stimulus_set: str
    question_type: str  # "visual" or "spatial"
    image_path: str
    question_prompt: str
    correct_answer: str
    metadata: StimulusMetadataModel
    
    @validator('question_type')
    def validate_question_type(cls, v):
        if v not in ['visual', 'spatial']:
            raise ValueError(f'question_type must be "visual" or "spatial", got "{v}"')
        return v


class SixOrNineDatasetModel(BaseModel):
    """Complete six-or-nine dataset structure."""
    dataset_name: str
    total_samples: int
    stimulus_sets: List[str]
    question_types: List[str]
    samples_per_set_type: int
    samples: List[SampleModel]
    
    @validator('total_samples')
    def validate_total_samples(cls, v, values):
        if 'samples' in values:
            actual_count = len(values['samples'])
            if v != actual_count:
                raise ValueError(f'total_samples ({v}) != actual samples count ({actual_count})')
        return v


def validate_dataset_json(dataset_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate dataset JSON structure using Pydantic models."""
    try:
        SixOrNineDatasetModel(**dataset_data)
        return True, []
    except ValidationError as e:
        errors = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error['loc'])
            errors.append(f"{loc}: {error['msg']}")
        return False, errors
    except Exception as e:
        return False, [f"Validation error: {str(e)}"]


def validate_dataset_file(dataset_path: str) -> Tuple[bool, List[str]]:
    """Validate a dataset JSON file."""
    try:
        with open(dataset_path, 'r') as f:
            dataset_data = json.load(f)
        return validate_dataset_json(dataset_data)
    except FileNotFoundError:
        return False, [f"Dataset file not found: {dataset_path}"]
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in dataset file: {str(e)}"]
    except Exception as e:
        return False, [f"Error reading dataset file: {str(e)}"]


def load_prompts(prompts_path: str) -> Dict[str, PromptSetModel]:
    """Load prompt configurations from prompts.csv."""
    prompts = {}
    
    try:
        with open(prompts_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['stimulus_set']:  # Skip empty rows
                    prompts[row['stimulus_set']] = PromptSetModel(**row)
    except Exception as e:
        raise ValueError(f"Error loading prompts from {prompts_path}: {e}")
    
    return prompts


def save_dataset(
    dataset_name: str,
    dataset_size: int,
    stimulus_sets: List[str],
    placement_locations: List[str],
    trial_num: int = 1000,
    output_dir: str = "datasets",
    use_number: bool = False,
    use_arrow: bool = False,
    image_size: Tuple[int, int] = (400, 400),
    figure_scale: float = 1.5,
    margin: int = 200,
    fov_angle: int = 60,
    view_distance: int = 5000,
    rotation_min: int = 0,
    rotation_max: int = 360,
    jitter_range: int = 20,
    resource_path: str = "resources",
    background_image: str = "background_with_colours.jpg",
    number_image: str = "im_of_6.jpg",
    seed: int = 42
):
    """
    Generate and save a complete six-or-nine dataset with images and JSON metadata.
    
    This function combines stimulus generation (like generate_stimuli.py) with
    prompt integration (like create_experiment_file.py) into a single workflow.
    """
    # Set random seed for reproducibility
    random.seed(seed)
    
    # Create dataset directory structure
    dataset_dir = os.path.join(output_dir, dataset_name)
    images_dir = os.path.join(dataset_dir, "images")
    
    os.makedirs(dataset_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    # Load prompts configuration
    prompts_path = os.path.join("six_or_nine_task", "prompts_clean.csv")
    try:
        prompt_configs = load_prompts(prompts_path)
    except Exception as e:
        raise ValueError(f"Failed to load prompts: {e}")
    
    # Validate requested stimulus sets
    available_sets = set(prompt_configs.keys())
    requested_sets = set(stimulus_sets)
    missing_sets = requested_sets - available_sets
    if missing_sets:
        raise ValueError(f"Requested stimulus sets not found in prompts.csv: {missing_sets}")
    
    # Generate stimuli per stimulus set with appropriate placement zones
    print("Generating stimulus images...")
    
    # Define placement zones for each stimulus set
    placement_zones_per_set = {
        "control_1": ["left", "right"],  # Use all requested placement zones
        "control_2": placement_locations,  # Use all requested placement zones  
        "control_3": placement_locations,  # Use all requested placement zones
        "level_1": ["front", "behind"],    # Only front/behind for level_1 spatial questions
        "level_2": ["front_left", "front_right"],      
    }
    
    stimuli_by_set = {}
    
    for stimulus_set in stimulus_sets:

        rotate_number = "control" not in stimulus_set

        # Get appropriate placement zones for this set
        set_placement_locations = placement_zones_per_set.get(stimulus_set, placement_locations)
        
        # Filter to only use locations that were requested
        set_placement_locations = [loc for loc in set_placement_locations if loc in placement_locations]
        
        if not set_placement_locations:
            raise ValueError(f"No valid placement locations for stimulus set '{stimulus_set}'. "
                           f"Set requires: {placement_zones_per_set.get(stimulus_set, 'any')}, "
                           f"but only {placement_locations} were provided.")
        
        print(f"  Generating {dataset_size} images for '{stimulus_set}' with placement zones: {set_placement_locations}")

        # make sure no number for the colour wall question
        use_number = stimulus_set != "control_2"

        # restrict rotation only for control_1
        if stimulus_set == "control_1":
            current_rotation_min = 70
            current_rotation_max = 110
        else:
            current_rotation_min = rotation_min
            current_rotation_max = rotation_max
        
        # Generate stimuli for this specific set
        set_stimuli_metadata = _generate_stimuli(
            dataset_size=dataset_size,
            placement_locations=set_placement_locations,
            images_dir=images_dir,
            stimulus_set=stimulus_set,  # Add set identifier for unique filenames
            use_number=use_number,
            use_arrow=use_arrow,
            rotate_number=rotate_number,
            image_size=image_size,
            figure_scale=figure_scale,
            margin=margin,
            fov_angle=fov_angle,
            view_distance=view_distance,
            rotation_min=current_rotation_min,
            rotation_max=current_rotation_max,
            jitter_range=jitter_range,
            resource_path=resource_path,
            background_image=background_image,
            number_image=number_image
        )
        
        stimuli_by_set[stimulus_set] = set_stimuli_metadata
    
    # Create samples by combining stimuli with prompts
    print("Creating dataset samples...")
    samples = []
    sample_id = 0
    question_types = ["visual", "spatial"]
    
    for stimulus_set in stimulus_sets:
        prompt_config = prompt_configs[stimulus_set]
        set_stimuli = stimuli_by_set[stimulus_set]
        
        for stimulus_meta in set_stimuli:
            for question_type in question_types:
                # Extract correct answer based on question type and stimulus set
                correct_answer = _extract_correct_answer(stimulus_meta, prompt_config, question_type)
                
                # Build question prompt
                question_prompt = prompt_config.context_prompt
                if question_type == "visual":
                    question_prompt += prompt_config.visual_prompt
                else:
                    question_prompt += prompt_config.spatial_prompt
                
                # Create sample
                sample = SampleModel(
                    sample_id=sample_id,
                    stimulus_set=stimulus_set,
                    question_type=question_type,
                    image_path=os.path.join("images", stimulus_meta.filename),
                    question_prompt=question_prompt,
                    correct_answer=correct_answer,
                    metadata=stimulus_meta
                )
                
                samples.append(sample)
                sample_id += 1
    
    # Create dataset structure
    dataset_data = {
        "dataset_name": dataset_name,
        "total_samples": len(samples),
        "stimulus_sets": stimulus_sets,
        "question_types": question_types,
        "samples_per_set_type": dataset_size,
        "samples": [sample.dict() for sample in samples]
    }
    
    # Validate dataset before saving
    is_valid, errors = validate_dataset_json(dataset_data)
    if not is_valid:
        error_msg = f"Generated dataset validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ValueError(error_msg)
    
    # Save JSON dataset file
    json_path = os.path.join(dataset_dir, f"{dataset_name}.json")
    with open(json_path, 'w') as f:
        json.dump(dataset_data, f, indent=2)
    
    print(f"Dataset saved to {dataset_dir}")
    print(f"  - JSON metadata: {json_path}")
    print(f"  - Stimulus images: {images_dir}")
    print(f"  - Total samples: {len(samples)} ({len(stimulus_sets)} sets × {len(question_types)} types × {dataset_size} stimuli)")


def _generate_stimuli(
    dataset_size: int,
    placement_locations: List[str],
    images_dir: str,
    stimulus_set: str,
    use_number: bool,
    use_arrow: bool,
    rotate_number: bool,
    image_size: Tuple[int, int],
    figure_scale: float,
    margin: int,
    fov_angle: int,
    view_distance: int,
    rotation_min: int,
    rotation_max: int,
    jitter_range: int,
    resource_path: str,
    background_image: str,
    number_image: str
) -> List[StimulusMetadataModel]:
    """Generate stimulus images and return metadata."""
    # Import stimulus generation utilities (to be implemented)
    from six_or_nine_task.stimulus_generator import generate_stimulus_images
    
    return generate_stimulus_images(
        n_images=dataset_size,
        placement_locations=placement_locations,
        images_dir=images_dir,
        stimulus_set=stimulus_set,
        use_number=use_number,
        use_arrow=use_arrow,
        rotate_number=rotate_number,
        image_size=image_size,
        figure_scale=figure_scale,
        margin=margin,
        fov_angle=fov_angle,
        view_distance=view_distance,
        rotation_min=rotation_min,
        rotation_max=rotation_max,
        jitter_range=jitter_range,
        resource_path=resource_path,
        background_image=background_image,
        number_image=number_image
    )


def _extract_correct_answer(
    stimulus_meta: StimulusMetadataModel,
    prompt_config: PromptSetModel,
    question_type: str
) -> str:
    """Extract the correct answer for a stimulus given the question type."""
    # Get the correct answer column for this question type
    if question_type == "visual":
        answer_col = prompt_config.visual_correct_answer_column
    else:
        answer_col = prompt_config.spatial_correct_answer_column
    
    # Get the raw answer from stimulus metadata
    raw_answer = getattr(stimulus_meta, answer_col, None)
    if raw_answer is None:
        raise ValueError(f"Answer column '{answer_col}' not found in stimulus metadata")
    
    # Apply answer transformations based on stimulus set and question type
    stimulus_set = prompt_config.stimulus_set
    
    if question_type == 'visual' and stimulus_set == "level_1":
        # For level_1 visual questions, map relative location to visibility
        return {"front": "CAN SEE", "behind": "CANNOT SEE"}.get(raw_answer, raw_answer)
    
    elif question_type == 'spatial' and stimulus_set == "level_1":
        # level_1 spatial questions ask "front or behind" - only accept FRONT/BEHIND
        raw_answer_upper = str(raw_answer).upper()
        if raw_answer_upper in ["FRONT", "BEHIND"]:
            return raw_answer_upper
        else:
            raise ValueError(f"Invalid answer '{raw_answer}' for level_1 spatial question. "
                           f"Expected 'front' or 'behind' but got '{raw_answer}'. "
                           f"This indicates a mismatch between stimulus placement and question type.")
    
    elif question_type == 'spatial' and stimulus_set == "level_2":
        # level_2 spatial questions ask "left or right" - only accept LEFT/RIGHT
        raw_answer_upper = str(raw_answer).upper().split("_")[-1]
        if raw_answer_upper in ["LEFT", "RIGHT"]:
            return raw_answer_upper
        else:
            raise ValueError(f"Invalid answer '{raw_answer}' for level_2 spatial question. "
                           f"Expected 'left' or 'right' but got '{raw_answer}'. "
                           f"This indicates a mismatch between stimulus placement and question type.")
    
    elif stimulus_set in ["control_2", "control_3"]:
        # For control sets, convert figure rotation to position/color
        try:
            angle = float(raw_answer)
        except (ValueError, TypeError):
            return str(raw_answer)
        
        # Map angle to position
        if 45 < angle <= 135:
            position = "TOP"
        elif 135 < angle <= 225:
            position = "LEFT"
        elif 225 < angle <= 315:
            position = "BOTTOM"
        else:
            position = "RIGHT"
        
        if question_type == "visual":
            # Map position to color for visual questions
            color_map = {"LEFT": "RED", "RIGHT": "GREEN", "TOP": "BLUE", "BOTTOM": "BLACK"}
            return color_map[position]
        else:
            # Return position for spatial questions
            return position
        
    elif stimulus_set == "control_1" and question_type == "visual":
        angle = stimulus_meta.number_rotation
        if angle > 270 or angle < 90:
            return str(6)
        else:
            return str(9)
        
    elif stimulus_set == "control_1" and question_type == "spatial":
        return stimulus_meta.number_location_x
    
    else:
        # Default: return raw answer as string
        return str(raw_answer)


def load_dataset(dataset_path: str) -> Dict[str, Any]:
    """
    Load a dataset from JSON file.
    
    Args:
        dataset_path: Path to the dataset JSON file
        
    Returns:
        Dict containing the loaded dataset
        
    Raises:
        FileNotFoundError: If dataset file doesn't exist
        ValueError: If dataset validation fails
    """
    try:
        with open(dataset_path, 'r') as f:
            dataset_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in dataset file: {str(e)}")
    
    # Validate the dataset
    is_valid, errors = validate_dataset_json(dataset_data)
    if not is_valid:
        error_msg = f"Dataset validation failed for {dataset_path}:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ValueError(error_msg)
    
    return dataset_data