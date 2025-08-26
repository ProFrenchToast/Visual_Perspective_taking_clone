import os
import re
import argparse
import json
import shutil
import pandas as pd
from typing import List, Dict
from PIL import Image
from six_or_nine_task.dataset import SampleModel, StimulusMetadataModel, SixOrNineDatasetModel

def load_prompts(prompts_path: str = "six_or_nine_task/prompts_external.csv") -> Dict[str, Dict[str, str]]:
    """
    Load prompts from CSV file, similar to how director_task/dataset.py loads items.
    
    Args:
        prompts_path: Path to prompts.csv file
        
    Returns:
        Dictionary mapping stimulus_set to prompt information
    """
    try:
        df = pd.read_csv(prompts_path)
        prompts = {}
        for _, row in df.iterrows():
            stimulus_set = row['stimulus_set']
            prompts[stimulus_set] = {
                'visual_prompt': row['visual_prompt'],
                'spatial_prompt': row['spatial_prompt'],
                'visual_correct_answer_column': row['visual_correct_answer_column'],
                'spatial_correct_answer_column': row['spatial_correct_answer_column'],
                'context_prompt': row['context_prompt']
            }
        return prompts
    except Exception as e:
        raise ValueError(f"Failed to load prompts from {prompts_path}: {e}")

def external_rotation_to_internal(external_angle: float) -> float:
    """
    Convert external rotation format to internal format.
    
    External format: 0° = north/up, anti-clockwise rotation
    Internal format: 0° = right/east, standard mathematical coordinates
    
    Args:
        external_angle: Angle in external format (0-359, anti-clockwise from north)
        
    Returns:
        Angle in internal format (0-359, standard mathematical coordinates)
    """
    # External: 0=north, 90=west, 180=south, 270=east (anti-clockwise)
    # Internal: 0=east, 90=north, 180=west, 270=south (standard math)
    # Conversion: internal = (450 - external) % 360
    return (450 - external_angle) % 360

def internal_rotation_to_external(internal_angle: float) -> float:
    """
    Convert internal rotation format to external format.
    
    Internal format: 0° = right/east, standard mathematical coordinates  
    External format: 0° = north/up, anti-clockwise rotation
    
    Args:
        internal_angle: Angle in internal format (0-359, standard mathematical coordinates)
        
    Returns:
        Angle in external format (0-359, anti-clockwise from north)
    """
    # Inverse of the above conversion
    return (450 - internal_angle) % 360

def parse_external_stimuli(directory_path: str) -> List[Dict[str, str]]:
    """
    Parse external stimuli filenames with format: <rotation><distance><side><number>.bmp
    
    Args:
        directory_path: Path to directory containing .bmp files
        
    Returns:
        List of dictionaries containing parsed metadata:
        - filepath: Full path to the image file
        - filename: Just the filename
        - rotation_degrees_external: Person's rotation in external format (0-359, anti-clockwise from north)
        - rotation_degrees_internal: Person's rotation in internal format (0-359, standard mathematical coordinates)
        - distance: "close" (1) or "far" (2)
        - side: "left" (L) or "right" (R) from person's perspective  
        - perspective_number: The number as seen by the person ("6" or "9")
    """
    
    parsed_files = []
    
    # Pattern to match: <rotation><distance><side><number>.bmp
    # rotation: 0-3 digits (0-359)
    # distance: 1 digit (1 or 2)
    # side: 1 letter (L or R)
    # number: 1 digit (6 or 9)
    pattern = r'^(\d{1,3})(1|2)(L|R)(6|9|4|7)\.bmp$'
    
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            if filename.lower().endswith('.bmp'):
                match = re.match(pattern, filename)
                
                if match:
                    rotation, distance, side, number = match.groups()
                    
                    # Convert to our format
                    distance_str = "close" if distance == "1" else "far"
                    side_str = "left" if side == "L" else "right"
                    external_angle = float(rotation)
                    internal_angle = external_rotation_to_internal(external_angle)
                    
                    parsed_files.append({
                        'filepath': os.path.join(root, filename),
                        'filename': filename,
                        'rotation_degrees_external': rotation,
                        'rotation_degrees_internal': round(internal_angle, 2),
                        'distance': distance_str,
                        'side': side_str, 
                        'perspective_number': number
                    })
                else:
                    print(f"Warning: Could not parse filename: {filename}")
    
    return parsed_files

def create_control_1_visual_task(parsed_file: Dict[str, str], sample_id: int, prompts: Dict[str, Dict[str, str]]) -> SampleModel:
    """
    Create control_1 visual task: "What number can you see in the image?"
    
    Args:
        parsed_file: Dictionary containing parsed metadata from external stimuli
        sample_id: Unique identifier for this sample
        prompts: Dictionary containing prompt templates loaded from prompts.csv
        
    Returns:
        SampleModel with question, correct answer, and metadata
    """
    external_rotation = int(parsed_file['rotation_degrees_external'])
    perspective_number = parsed_file['perspective_number']
    
    # Filter to only numbers that are visible currently
    if external_rotation == 0:
        # Everything is visible when person faces north
        visible_number = perspective_number
    elif external_rotation == 180:
        # 6 and 9s are swapped when person faces south (upside down view)
        if perspective_number == '6':
            visible_number = '9'
        elif perspective_number == '9':
            visible_number = '6'
        else:
            raise ValueError(f"Invalid perspective number {perspective_number} for rotation {external_rotation}")
    else:
        raise ValueError(f"Unsupported rotation {external_rotation} for control_1 visual task")
    
    sample = SampleModel(
        sample_id=sample_id,
        stimulus_set="control_1",
        question_type="visual",
        question_prompt=prompts["control_1"]["context_prompt"] + prompts["control_1"]["visual_prompt"],
        image_path=parsed_file["filepath"],
        correct_answer=str(visible_number),
        metadata=StimulusMetadataModel(
            filename=parsed_file['filepath'],
            image_number=0,
            figure_type="",
            margin_size=0,
            fov_angle=120,
            figure_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_position_x=0,
            number_position_y=0,
            number_location_x="",
            number_location_y="",
            relative_location="",
            number_appearance="",
            number_appearance_type="",
        ),
    )
    return sample

def create_control_1_spatial_task(parsed_file: Dict[str, str], sample_id: int, prompts: Dict[str, Dict[str, str]]) -> SampleModel:
    """
    Create control_1 spatial task: "Is the number on the left or right side of the image?"
    
    Args:
        parsed_file: Dictionary containing parsed metadata from external stimuli
        
    Returns:
        Task dictionary with question, correct answer, and metadata
    """
    external_rotation = int(parsed_file['rotation_degrees_external'])
    side = parsed_file['side']  # 'left' or 'right' from person's perspective
    
    # Filter only to numbers that are clearly on one side or the other
    if external_rotation == 0:
        # Person faces north, L/R mapping is direct
        image_side = side.upper()
    elif external_rotation == 180:
        # Person faces south, L/R mapping is flipped
        image_side = "RIGHT" if side == "left" else "LEFT"
    elif external_rotation == 60:
        # Only L numbers are clearly on one side (right is too close to middle)
        if side != "left":
            raise ValueError(f"Only left numbers supported for rotation {external_rotation}")
        image_side = "LEFT"
    elif external_rotation == 120:
        # Only R numbers are clearly on one side
        if side != "right":
            raise ValueError(f"Only right numbers supported for rotation {external_rotation}")
        image_side = "LEFT"
    elif external_rotation == 240:
        # Only L numbers are clearly on one side
        if side != "left":
            raise ValueError(f"Only left numbers supported for rotation {external_rotation}")
        image_side = "RIGHT"
    elif external_rotation == 300:
        # Only R numbers are clearly on one side
        if side != "right":
            raise ValueError(f"Only right numbers supported for rotation {external_rotation}")
        image_side = "RIGHT"
    else:
        raise ValueError(f"Unsupported rotation {external_rotation} for control_1 spatial task")
    
    sample = SampleModel(
        sample_id=sample_id,
        stimulus_set="control_1",
        question_type="spatial",
        question_prompt=prompts["control_1"]["context_prompt"] + prompts["control_1"]["spatial_prompt"],
        image_path=parsed_file["filepath"],
        correct_answer=image_side,
        metadata=StimulusMetadataModel(
            filename=parsed_file['filepath'],
            image_number=0,
            figure_type="",
            margin_size=0,
            fov_angle=120,
            figure_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_position_x=0,
            number_position_y=0,
            number_location_x="",
            number_location_y="",
            relative_location="",
            number_appearance="",
            number_appearance_type="",
        ),
    )
    return sample

def create_control_2_visual_task(parsed_file: Dict[str, str], sample_id: int, prompts: Dict[str, Dict[str, str]]) -> SampleModel:
    """
    Create control_2 visual task: "What colour is the wall directly in front of the person?"
    
    Args:
        parsed_file: Dictionary containing parsed metadata from external stimuli
        
    Returns:
        Task dictionary with question, correct answer, and metadata
    """
    # Throw an error for all images - there are no coloured walls in this image set
    raise ValueError("External stimuli do not contain coloured walls - control_2 visual task not supported")

def create_control_2_spatial_task(parsed_file: Dict[str, str], sample_id: int, prompts: Dict[str, Dict[str, str]]) -> SampleModel:
    """
    Create control_2 spatial task: "Which side of the image is directly in front of the person?"
    
    Args:
        parsed_file: Dictionary containing parsed metadata from external stimuli
        
    Returns:
        Task dictionary with question, correct answer, and metadata
    """
    external_rotation = int(parsed_file['rotation_degrees_external'])
    
    # Filter only to images where the person is clearly facing a particular wall
    if external_rotation == 0:
        # Person faces north (top of image)
        facing_direction = "TOP"
    elif external_rotation == 180:
        # Person faces south (bottom of image)
        facing_direction = "BOTTOM"
    elif external_rotation in [60, 120]:
        # Person faces left side of image
        facing_direction = "LEFT"
    elif external_rotation in [240, 300]:
        # Person faces right side of image
        facing_direction = "RIGHT"
    else:
        raise ValueError(f"Unsupported rotation {external_rotation} for control_2 spatial task")
    
    sample = SampleModel(
        sample_id=sample_id,
        stimulus_set="control_2",
        question_type="spatial",
        question_prompt=prompts["control_2"]["context_prompt"] + prompts["control_2"]["spatial_prompt"],
        image_path=parsed_file["filepath"],
        correct_answer=facing_direction,
        metadata=StimulusMetadataModel(
            filename=parsed_file['filepath'],
            image_number=0,
            figure_type="",
            margin_size=0,
            fov_angle=120,
            figure_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_position_x=0,
            number_position_y=0,
            number_location_x="",
            number_location_y="",
            relative_location="",
            number_appearance="",
            number_appearance_type="",
        ),
    )
    return sample

def create_level_1_visual_task(parsed_file: Dict[str, str], sample_id: int, prompts: Dict[str, Dict[str, str]]) -> SampleModel:
    """
    Create level_1 visual task: "Can the person see the number?"
    
    This tests understanding of field-of-view constraints and occlusion.
    
    Example:
        - Filename: 90L2L6.bmp (person at 90°, close distance, left side, number 6)
        - Person faces west (left side of image)
        - Number is on left side from person's perspective
        - Answer: "CAN SEE" (number is in field of view)
    
    Args:
        parsed_file: Dictionary containing parsed metadata from external stimuli
        sample_id: Unique identifier for this sample
        prompts: Dictionary containing prompt templates loaded from prompts.csv
        
    Returns:
        SampleModel with question, correct answer, and metadata
    """
    external_rotation = int(parsed_file['rotation_degrees_external'])
    side = parsed_file['side']  # 'left' or 'right' from person's perspective
    distance = parsed_file['distance']  # 'close' or 'far'
    
    # in this set of stimuli the number can always be seen by the person 
    # so its not super informative 
    visibility = "CAN SEE"
    
    sample = SampleModel(
        sample_id=sample_id,
        stimulus_set="level_1",
        question_type="visual",
        question_prompt=prompts["level_1"]["context_prompt"] + prompts["level_1"]["visual_prompt"],
        image_path=parsed_file["filepath"],
        correct_answer=visibility,
        metadata=StimulusMetadataModel(
            filename=parsed_file['filepath'],
            image_number=0,
            figure_type="",
            margin_size=0,
            fov_angle=120,
            figure_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_position_x=0,
            number_position_y=0,
            number_location_x="",
            number_location_y="",
            relative_location="front" if visibility == "CAN SEE" else "behind",
            number_appearance="",
            number_appearance_type="",
        ),
    )
    return sample

def create_level_1_spatial_task(parsed_file: Dict[str, str], sample_id: int, prompts: Dict[str, Dict[str, str]]) -> SampleModel:
    """
    Create level_1 spatial task: "Is the number in front of or behind the person?"
    
    This tests understanding of spatial relationships from the person's perspective.
    
    Example:
        - Filename: 180L1R9.bmp (person at 180°, close distance, right side, number 9)  
        - Person faces south (bottom of image)
        - Number is on right side from person's perspective at close distance
        - From person's view, this is "FRONT" (in their field of view)
    
    Args:
        parsed_file: Dictionary containing parsed metadata from external stimuli
        sample_id: Unique identifier for this sample
        prompts: Dictionary containing prompt templates loaded from prompts.csv
        
    Returns:
        SampleModel with question, correct answer, and metadata
    """
    external_rotation = int(parsed_file['rotation_degrees_external'])
    side = parsed_file['side']  # 'left' or 'right' from person's perspective
    distance = parsed_file['distance']  # 'close' or 'far'
    
    # for this again the number is always in front of the person
    spatial_relation = "FRONT"
    
    sample = SampleModel(
        sample_id=sample_id,
        stimulus_set="level_1",
        question_type="spatial",
        question_prompt=prompts["level_1"]["context_prompt"] + prompts["level_1"]["spatial_prompt"],
        image_path=parsed_file["filepath"],
        correct_answer=spatial_relation,
        metadata=StimulusMetadataModel(
            filename=parsed_file['filepath'],
            image_number=0,
            figure_type="",
            margin_size=0,
            fov_angle=120,
            figure_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_position_x=0,
            number_position_y=0,
            number_location_x="",
            number_location_y="",
            relative_location=spatial_relation.lower(),
            number_appearance="",
            number_appearance_type="",
        ),
    )
    return sample

def create_level_2_visual_task(parsed_file: Dict[str, str], sample_id: int, prompts: Dict[str, Dict[str, str]]) -> SampleModel:
    """
    Create level_2 visual task: "What number can the person see from their perspective?"
    
    This tests understanding of rotational perspective - what the number looks like from the person's viewpoint.
    
    Example:
        - Filename: 270L1L6.bmp (person at 270°, close distance, left side, number 6)
        - Person faces east (right side of image)
        - Number 6 is on left side from person's perspective
        - From person's rotated view, the 6 might appear as 9 due to perspective rotation
    
    Args:
        parsed_file: Dictionary containing parsed metadata from external stimuli
        sample_id: Unique identifier for this sample
        prompts: Dictionary containing prompt templates loaded from prompts.csv
        
    Returns:
        SampleModel with question, correct answer, and metadata
    """
    external_rotation = int(parsed_file['rotation_degrees_external'])
    perspective_number = parsed_file['perspective_number']
    
    # for these images the perspective number is always just the number in the file name
    visible_number = perspective_number
    
    sample = SampleModel(
        sample_id=sample_id,
        stimulus_set="level_2",
        question_type="visual",
        question_prompt=prompts["level_2"]["context_prompt"] + prompts["level_2"]["visual_prompt"],
        image_path=parsed_file["filepath"],
        correct_answer=str(visible_number),
        metadata=StimulusMetadataModel(
            filename=parsed_file['filepath'],
            image_number=0,
            figure_type="",
            margin_size=0,
            fov_angle=120,
            figure_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_position_x=0,
            number_position_y=0,
            number_location_x="",
            number_location_y="",
            relative_location="",
            number_appearance=str(visible_number),
            number_appearance_type="viewer_perspective",
        ),
    )
    return sample

def create_level_2_spatial_task(parsed_file: Dict[str, str], sample_id: int, prompts: Dict[str, Dict[str, str]]) -> SampleModel:
    """
    Create level_2 spatial task: "From the person's perspective, is the number to their left or right?"
    
    This tests understanding of egocentric spatial relationships - left/right from the person's viewpoint.
    
    Example:
        - Filename: 90L2R7.bmp (person at 90°, close distance, right side, number 7)
        - Person faces west (left side of image)
        - Number is on "right side" in image coordinates
        - From person's egocentric perspective facing west, this is to their "LEFT"
    
    Args:
        parsed_file: Dictionary containing parsed metadata from external stimuli
        sample_id: Unique identifier for this sample
        prompts: Dictionary containing prompt templates loaded from prompts.csv
        
    Returns:
        SampleModel with question, correct answer, and metadata
    """
    external_rotation = int(parsed_file['rotation_degrees_external'])
    side = parsed_file['side']  # 'left' or 'right' from person's perspective
    
    sample = SampleModel(
        sample_id=sample_id,
        stimulus_set="level_2",
        question_type="spatial",
        question_prompt=prompts["level_2"]["context_prompt"] + prompts["level_2"]["spatial_prompt"],
        image_path=parsed_file["filepath"],
        correct_answer=side,
        metadata=StimulusMetadataModel(
            filename=parsed_file['filepath'],
            image_number=0,
            figure_type="",
            margin_size=0,
            fov_angle=120,
            figure_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_rotation=external_rotation_to_internal(int(parsed_file['rotation_degrees_external'])),
            number_position_x=0,
            number_position_y=0,
            number_location_x=side,
            number_location_y="",
            relative_location="",
            number_appearance="",
            number_appearance_type="",
        ),
    )
    return sample

def print_sample_results(parsed_files: List[Dict[str, str]], n: int = 5) -> None:
    """Print first n parsed files for inspection"""
    print(f"Parsed {len(parsed_files)} files. Sample results:")
    for i, file_data in enumerate(parsed_files[:n]):
        print(f"{i+1}. {file_data}")

def save_external_dataset(dataset_name: str, samples: List[SampleModel], output_dir: str = "datasets") -> None:
    """
    Save external stimuli dataset with copied images and JSON metadata.
    
    Args:
        dataset_name: Name of the dataset
        samples: List of SampleModel objects to save
        output_dir: Base directory to save datasets in
    """
    # Create dataset directory structure
    dataset_dir = os.path.join(output_dir, dataset_name)
    images_dir = os.path.join(dataset_dir, "images")
    
    os.makedirs(dataset_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    # Convert and copy images, updating paths to JPG format
    updated_samples = []
    for sample in samples:
        # Convert BMP to JPG
        original_image_path = sample.image_path
        original_filename = os.path.basename(original_image_path)
        
        # Change extension from .bmp to .jpg
        jpg_filename = os.path.splitext(original_filename)[0] + '.jpg'
        new_image_path = os.path.join(images_dir, jpg_filename)
        
        # Load BMP, resize to standard size, and save as JPG
        with Image.open(original_image_path) as img:
            # Convert to RGB if necessary (BMP might be in a different mode)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Resize to match standard dataset image size (400x400)
            img_resized = img.resize((400, 400), Image.LANCZOS)
            img_resized.save(new_image_path, 'JPEG', quality=95)
        
        # Update sample with relative JPG image path
        updated_sample = sample.copy()
        updated_sample.image_path = os.path.join("images", jpg_filename)
        updated_samples.append(updated_sample)
    
    # Group samples by stimulus set and question type for counting
    stimulus_sets = list(set(sample.stimulus_set for sample in updated_samples))
    question_types = list(set(sample.question_type for sample in updated_samples))
    
    # Estimate samples per set type (this may not be exact due to filtering)
    samples_per_set_type = len(updated_samples) // (len(stimulus_sets) * len(question_types)) if stimulus_sets and question_types else 0
    
    # Create dataset structure using the existing SixOrNineDatasetModel
    dataset_data = {
        "dataset_name": dataset_name,
        "total_samples": len(updated_samples),
        "stimulus_sets": stimulus_sets,
        "question_types": question_types,
        "samples_per_set_type": samples_per_set_type,
        "samples": [sample.dict() for sample in updated_samples]
    }
    
    # Validate dataset using existing validation
    try:
        validated_dataset = SixOrNineDatasetModel(**dataset_data)
    except Exception as e:
        raise ValueError(f"Dataset validation failed: {e}")
    
    # Save JSON dataset file
    json_path = os.path.join(dataset_dir, f"{dataset_name}.json")
    with open(json_path, 'w') as f:
        json.dump(validated_dataset.dict(), f, indent=2)
    
    print(f"External stimuli dataset saved to {dataset_dir}")
    print(f"  - JSON metadata: {json_path}")
    print(f"  - Converted & resized images (BMP → JPG, 400x400): {images_dir}")
    print(f"  - Total samples: {len(updated_samples)}")
    print(f"  - Stimulus sets: {stimulus_sets}")
    print(f"  - Question types: {question_types}")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse external stimuli filenames with format: <rotation><distance><side><number>.bmp')
    parser.add_argument('--directory', required=True, help='Path to directory containing .bmp files')
    parser.add_argument('--output', '-o', required=True, help='Output dataset name')
    
    args = parser.parse_args()

    prompts = load_prompts()
    
    if os.path.exists(args.directory):
        results = parse_external_stimuli(args.directory)
        samples: list[SampleModel] = []
        
        print(f"Processing {len(results)} external stimulus files...")
        
        for result in results:
            try:
                samples.append(create_control_1_visual_task(result, len(samples)+1, prompts))
            except Exception:
                pass
            try:
                samples.append(create_control_1_spatial_task(result, len(samples)+1, prompts))
            except Exception:
                pass
            try:
                samples.append(create_control_2_visual_task(result, len(samples)+1, prompts))
            except Exception:
                pass
            try:
                samples.append(create_control_2_spatial_task(result, len(samples)+1, prompts))
            except Exception:
                pass
            try:
                samples.append(create_level_1_visual_task(result, len(samples)+1, prompts))
            except Exception:
                pass
            try:
                samples.append(create_level_1_spatial_task(result, len(samples)+1, prompts))
            except Exception:
                pass
            try:
                samples.append(create_level_2_visual_task(result, len(samples)+1, prompts))
            except Exception:
                pass
            try:
                samples.append(create_level_2_spatial_task(result, len(samples)+1, prompts))
            except Exception:
                pass

        print(f"Created {len(samples)} samples from external stimuli")
        
        # Save dataset
        if samples:
            save_external_dataset(args.output, samples)
        else:
            print("Warning: No samples were created. Check your input files and filtering logic.")
        
    else:
        print(f"Error: Directory not found: {args.directory}")
        exit(1)