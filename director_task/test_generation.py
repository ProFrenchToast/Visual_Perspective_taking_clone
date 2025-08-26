#!/usr/bin/env python3

from director_task.item import Item
from director_task.sample import Sample
from director_task.question import SelectionRuleType

# Define a simple ITEMS pool for testing
ITEMS = [
    {
        "name": "small_red_star",
        "image_path": "star_small_red.png",
        "boolean_properties": {"star": True, "red": True, "small": True},
        "scalar_properties": {"size": 1}
    },
    {
        "name": "large_red_star", 
        "image_path": "star_large_red.png",
        "boolean_properties": {"star": True, "red": True, "large": True},
        "scalar_properties": {"size": 3}
    },
    {
        "name": "small_blue_star",
        "image_path": "star_small_blue.png", 
        "boolean_properties": {"star": True, "blue": True, "small": True},
        "scalar_properties": {"size": 1}
    },
    {
        "name": "large_blue_star",
        "image_path": "star_large_blue.png",
        "boolean_properties": {"star": True, "blue": True, "large": True}, 
        "scalar_properties": {"size": 3}
    },
    {
        "name": "small_red_circle",
        "image_path": "circle_small_red.png",
        "boolean_properties": {"circle": True, "red": True, "small": True},
        "scalar_properties": {"size": 1}
    },
    {
        "name": "large_red_circle",
        "image_path": "circle_large_red.png", 
        "boolean_properties": {"circle": True, "red": True, "large": True},
        "scalar_properties": {"size": 3}
    },
    {
        "name": "small_blue_circle",
        "image_path": "circle_small_blue.png",
        "boolean_properties": {"circle": True, "blue": True, "small": True},
        "scalar_properties": {"size": 1}
    },
    {
        "name": "large_blue_circle", 
        "image_path": "circle_large_blue.png",
        "boolean_properties": {"circle": True, "blue": True, "large": True},
        "scalar_properties": {"size": 3}
    },
    {
        "name": "red_car",
        "image_path": "car_red.png",
        "boolean_properties": {"car": True, "red": True},
        "scalar_properties": {"size": 2}
    },
    {
        "name": "blue_car",
        "image_path": "car_blue.png", 
        "boolean_properties": {"car": True, "blue": True},
        "scalar_properties": {"size": 2}
    }
]

def main():
    # Use real items from items.json instead of hardcoded test items
    # to avoid physics property issues
    try:
        items = Item.load_from_json("director_task/items.json")
        print(f"Loaded {len(items)} items from items.json")
    except FileNotFoundError:
        print("items.json not found, using hardcoded test items (may have limited physics properties)")
        # Convert ITEMS dictionaries to Item objects
        items = []
        for item_dict in ITEMS:
            item = Item(
                name=item_dict["name"],
                image_path=item_dict["image_path"],
                boolean_properties=item_dict["boolean_properties"],
                scalar_properties=item_dict["scalar_properties"]
            )
            items.append(item)
    
    print("Generating 5 test samples...\n")
    
    try:
        samples = Sample.generate_test_samples(
            items=items,
            grid_width=3,
            grid_height=3, 
            num_samples=5,  # Generate just 5 samples for testing
            item_fill_ratio=0.6,
            block_ratio=0.3,
            size_prop=0.4,
            spatial_same_prop=0.0,  # Skip spatial_same to avoid generation issues 
            spatial_diff_prop=0.4,
            physics_prop=0.2  # Reduce physics proportion
        )
        
        for i, sample in enumerate(samples, 1):
            print(f"{'='*60}")
            print(f"SAMPLE {i}")
            print(f"{'='*60}")
            
            # Display the question
            print(f"Question: {sample.question.full_question()}")
            print(f"Natural Language: {sample.question.to_natural_language()}")
            print(f"Filter Criteria: {sample.question.filter_criteria}")
            if sample.question.selection_rule:
                print(f"Selection Rule: {sample.question.selection_rule} by {sample.question.selection_property}")
            print(f"Selection Rule Type: {sample.selection_rule_type.value}")
            print(f"Is Physics: {sample.is_physics}")
            # Check if spatial based on selection rule type
            spatial_types = [SelectionRuleType.SPATIAL_SAME_PERSPECTIVE, SelectionRuleType.SPATIAL_DIFFERENT_PERSPECTIVE]
            is_spatial = sample.selection_rule_type in spatial_types
            print(f"Is Spatial: {is_spatial}")
            print(f"Is Reversed: {sample.is_reversed}")
            print()
            
            # Display the grid
            print("Grid:")
            print(sample.grid.pretty_print())
            print()
            
            # Display the answer
            print(f"Participant Answer Coordinates: {sample.answer_coordinates}")
            print(f"Director Answer Coordinates: {sample.director_answer_coordinates}")
            
            # Verify the answer
            computed_answer = sample.question.find_target(sample.grid)
            print(f"Computed Answer: {computed_answer}")
            print(f"Answer Verified: {sample.verify_answer()}")
            print(f"Is Ambiguous: {sample.has_ambiguous_answer()}")
            
            print("\n")
            
    except Exception as e:
        print(f"Error generating samples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()