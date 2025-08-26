import base64
from io import BytesIO
import json
import os
from pathlib import Path
from typing import Any, Dict
import PIL
import PIL.Image
from inspect_ai import Task, task
from inspect_ai.dataset import Dataset, MemoryDataset, Sample, json_dataset
from inspect_ai.model import ChatMessageUser, ContentImage
from inspect_ai.solver import Generate, Solver, TaskState, basic_agent, system_message, use_tools, solver, user_message
from inspect_ai.scorer import Score, Scorer, Target, accuracy, grouped, includes, match, scorer
from inspect_ai.tool import Tool, ToolResult, tool
from director_task.dataset import validate_dataset_file

SYSTEM_MESSAGE = """There is a shelf in front of you with a grid of items on it.The user is standing on the opposite side of the shelves and is asking you to pick up a specific item for them that they can see. Some of the cells in the grid are blocked from the users view hiding anything that might be there indicated by the dark background in the cell. You will receive and image of the grid from your point of view.

Submit your answer in the form <column><row>, for sample 'C2'."""

@tool()
def think() -> Tool:

    async def execute(thoughts: str) -> str:
        """
        Use this tool to stop, think and reason about the task at hand. Particularly useful to build plans and reflect on them prior to executing actions.

        Args:
            thoughts (str): The thoughts or reasoning process of the agent.

        Returns:
            str: The thoughts or reasoning process of the agent.
        """

        return thoughts
    
    return execute

# Function to encode the image
def encode_image(image: PIL.Image.Image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

@tool()
def crop_image(original_image_path: str) -> Tool:
    async def execute(x: int, y: int, width: int, height: int) -> ContentImage:
        """
        Crop the image to the specified coordinates and dimensions.
        
        Args:
            x (int): The x-coordinate of the top-left corner of the crop area.
            y (int): The y-coordinate of the top-left corner of the crop area.
            width (int): The width of the crop area.
            height (int): The height of the crop area.

        Returns:
            Image: The image after the cropping operation.
        """
        from PIL import Image
        assert os.path.isfile(original_image_path), f"Original image path {original_image_path} does not point to a valid file."
        # Open the original image
        original_image = Image.open(original_image_path)
        # Define the crop box
        crop_box = (x, y, x + width, y + height)
        # Crop the image
        cropped_image = original_image.crop(crop_box)
        encoded_image = encode_image(cropped_image)
        output_image = ContentImage(image=f"data:image/png;base64,{encoded_image}")
        
        return output_image

    return execute

@tool()
def rotate_image(original_image_path: str) -> Tool:
    async def execute(angle: int) -> ContentImage:
        """
        Rotate the image by the specified angle.
        
        Args:
            angle (int): The angle in degrees to rotate the image.

        Returns:
            Image: The image after the rotation operation.
        """
        from PIL import Image
        assert os.path.isfile(original_image_path), f"Original image path {original_image_path} does not point to a valid file."
        # Open the original image
        original_image = Image.open(original_image_path)
        # Rotate the image
        rotated_image = original_image.rotate(angle, expand=True)
        encoded_image = encode_image(rotated_image)
        output_image = ContentImage(image=f"data:image/png;base64,{encoded_image}")
        
        return output_image

    return execute

@solver
def add_additional_tools() -> Solver:
    async def solve(state: TaskState, generate: Generate):
        assert state.metadata is not None, "Task state metadata must be initialized."
        assert state.metadata["grid_image"] is not None, "Grid image must be provided in the task state metadata."
        state.tools.extend([crop_image(state.metadata["grid_image"]), rotate_image(state.metadata["grid_image"])])
        state.tool_choice = "any"
        return state
    return solve


@solver
def add_image() -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        """
        Adds an image of the grid from the agent's point of view to the task state.
        """
        assert state.metadata is not None, "Task state metadata must be initialized."
        assert state.metadata["grid_image"] is not None, "Grid image must be provided in the task state metadata."
        assert os.path.isfile(state.metadata["grid_image"]), "Grid image path must point to a valid file."
        # Add the image to the task state
        state.messages.append(ChatMessageUser(content=[ContentImage(image=state.metadata["grid_image"])]))
        return state

    return solve

def record_to_sample(record: Dict[str, Any], dataset_path: str) -> Sample:
    dataset_dir = os.path.dirname(dataset_path)
    sample_id  = record["sample_id"]
    sample_type = record["sample_type"]
    grid_image = os.path.join(dataset_dir, record["image_path"])
    question = record["question"]["full_question"]
    answer = record["answers"]["director_coordinates"]
    # Extract the target from the answer
    target = chr(ord('A') + answer[0][0]) + str(answer[0][1]+1)  
    return Sample(input= question, id=sample_id, target=target, metadata={
        "grid_image": grid_image,
        "grid_width": record["grid"]["width"],
        "grid_height": record["grid"]["height"],
        "items": record["grid"]["items"],
        "sample_type": sample_type,
        "answer_coordinates": answer,
        "participant_coordinates": record["answers"]["participant_coordinates"],
        "director_answer_coordinates": record["answers"]["director_coordinates"],
        "selection_rule_type": record["question"]["selection_rule_type"],
        "is_physics": record["is_physics"],
        "is_reversed": record["is_reversed"],
        "question": record["question"]
    })

def custom_loader(dataset_path: str) -> Dataset:
    # Validate dataset file before loading
    is_valid, errors = validate_dataset_file(dataset_path)
    if not is_valid:
        error_msg = f"Dataset validation failed for {dataset_path}:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ValueError(error_msg)
    
    json_data = json.load(open(dataset_path, 'r'))
    samples = []
    # Iterate through the samples in the record
    for item in json_data["samples"]:
        sample = record_to_sample(item, dataset_path)
        samples.append(sample)
    return MemoryDataset(samples=samples, name=json_data["dataset_name"], location=dataset_path, shuffled=False)

@scorer(metrics=[grouped(accuracy(), "sample_type"), grouped(accuracy(), "selection_rule_type")])
def grouped_accuracy_scorer() -> Scorer:
    """Custom scorer that provides grouped accuracy metrics."""
    async def score(state: TaskState, target: Target) -> Score:
        # Use the default includes() behavior for basic scoring
        includes_scorer = includes()
        base_score = await includes_scorer(state, target)
        return Score(
            value=base_score.value,
            answer=base_score.answer,
            explanation=base_score.explanation,
        )
    
    return score

@task
def directors_task(
    agent_solver: Solver | None = None,
    dataset_path: str | None = None,
    additional_tools: bool = False
    ) -> Task:
    if dataset_path is None:
        dataset_path = os.path.join(Path(__file__).parent.parent, "datasets", "director_task", "director_task.json")
    else:
        # If dataset_path is relative, try current working directory first, then repo root
        if not os.path.isabs(dataset_path):
            # First try relative to current working directory
            cwd_path = os.path.join(os.getcwd(), dataset_path)
            if os.path.exists(cwd_path):
                dataset_path = cwd_path
            else:
                # Fall back to relative to repository root
                dataset_path = os.path.join(Path(__file__).parent.parent, dataset_path)

    if additional_tools:
        solver = [
            system_message(SYSTEM_MESSAGE),
            use_tools([think()], tool_choice="any"),
            add_image(),
            add_additional_tools(),
            agent_solver or basic_agent(),
        ]
    else:
        solver = [
                system_message(SYSTEM_MESSAGE),
                use_tools([think()], tool_choice="any"),
                add_image(),
                agent_solver or basic_agent(),
            ]

    return Task(
        dataset=custom_loader(dataset_path),
        solver = solver,
        scorer=grouped_accuracy_scorer(),
    )