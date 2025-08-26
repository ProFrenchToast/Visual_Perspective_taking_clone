# Visual Perspective-Taking

A research repository containing experimental tasks for evaluating AI models' visual perspective-taking and spatial reasoning abilities. This repository implements two main experimental paradigms designed to test how well models understand different viewpoints and spatial relationships.

## Overview

This repository contains implementations of two visual perspective-taking tasks:

1. **Director Task** (`director_task/`): A grid-based task where a director gives instructions to a participant who must consider the director's limited perspective to select the correct item
2. **Six or Nine Task** (`six_or_nine_task/`): A visual task using ambiguous numerical stimuli (6/9) that tests perspective-dependent interpretation

Both tasks are designed for evaluation using the [Inspect AI](https://inspect.aisi.org.uk/) framework and generate datasets with accompanying visual stimuli.

## Quick Start

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd visual-perspective-taking

# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### Basic Usage

#### Director Task
```bash
# Generate a dataset
python -m director_task.task_generator --dataset_name my_dataset --dataset_size 100

# Run evaluation
inspect eval director_task/task.py@directors_task --model <model_name>
```

#### Six or Nine Task
```bash
# Generate stimuli
cd six_or_nine_task
python generate_stimuli.py

# Create experiment file
python create_experiment_file.py

# Run evaluation
inspect eval six_or_nine_task/task.py@six_or_nine_task --model <model_name>
```

## Task Details

### Director Task
The director task tests whether models can take the perspective of a "director" who has a limited view of a grid containing various objects. The participant must select items based on the director's instructions, considering what the director can and cannot see.

**Key Features:**
- Grid-based spatial reasoning
- Blocked cell mechanics (director's limited view)
- Control vs. test samples (ambiguous vs. unambiguous)
- Physics-based and spatial constraints
- Configurable item properties and generation parameters

See [director_task/README.md](director_task/README.md) for detailed documentation.

### Six or Nine Task
This task presents visual stimuli where numbers can appear as either "6" or "9" depending on viewing perspective. Models must determine what a figure in the image would see based on their spatial position and orientation.

**Key Features:**
- Ambiguous visual stimuli (6/9 numbers)
- Figure positioning and rotation
- Spatial relationship questions (front/behind, left/right)
- Field-of-view constraints using cone geometry
- Visual vs. spatial perspective conditions

## Project Structure

```
visual-perspective-taking/
├── director_task/          # Grid-based perspective-taking task
├── six_or_nine_task/       # Ambiguous numeral perspective task
├── datasets/               # Generated datasets with images
├── logs/                   # Evaluation results and logs
├── resources/              # Shared assets (images, figures)
├── setup.py               # Package configuration
└── CLAUDE.md              # Development guidelines for AI assistants
```

## Dependencies

- **inspect_ai**: Framework for AI evaluation tasks
- **pillow**: Image processing and generation
- **pydantic**: Data validation and serialization
- **jsonschema**: JSON validation for datasets
- **pandas/seaborn**: Data analysis and visualization (six_or_nine_task)

## Evaluation

Both tasks integrate with the Inspect AI framework for systematic model evaluation:

- Support for multiple model providers
- Structured evaluation metrics and logging
- Batch processing capabilities
- Statistical analysis tools

## Development

The repository includes comprehensive test suites and validation tools:

```bash
# Run tests
python -m unittest discover -s director_task -p "test_*.py"

# Interactive item editing (director task)
python -m director_task.item_editor
```

## Citation

If you use this repository in your research, please cite the relevant papers and acknowledge the experimental paradigms implemented here.

## License

[Add appropriate license information]