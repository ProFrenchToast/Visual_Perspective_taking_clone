"""
Six or Nine Task Package

Visual perspective-taking experiments using ambiguous 6/9 stimuli.
"""

from .task import six_or_nine_task, six_or_nine_control_only, six_or_nine_level_only
from .dataset import save_dataset, load_dataset, validate_dataset_file
from .task_generator import main as generate_dataset

__version__ = "1.0.0"
__all__ = [
    "six_or_nine_task",
    "six_or_nine_control_only", 
    "six_or_nine_level_only",
    "save_dataset",
    "load_dataset",
    "validate_dataset_file",
    "generate_dataset"
]