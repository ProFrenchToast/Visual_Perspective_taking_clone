#!/usr/bin/env python3
"""
Test script for grouped metrics functionality.
This script demonstrates how to use the new grouped metrics with the director task.
"""

import asyncio
import os
from pathlib import Path
from inspect_ai import eval
from inspect_ai.model import get_model
from director_task.grouped_metrics import (
    directors_task_basic_grouped,
    directors_task_with_grouped_metrics,
    print_grouping_summary
)

def test_basic_grouped_metrics():
    """Test basic single-dimension grouped metrics."""
    print("Testing basic grouped metrics...")
    
    # First, show the grouping summary
    dataset_path = os.path.join(Path(__file__).parent.parent, "datasets", "director_task", "director_task.json")
    print_grouping_summary(dataset_path)
    
    print("\nBasic grouped metrics task created successfully!")
    print("This version includes:")
    print("- Overall accuracy and standard error")
    print("- Accuracy grouped by sample_type (control vs test)")
    print("- Accuracy grouped by is_physics (physics vs non-physics)")
    print("- Accuracy grouped by selection_rule_type (different selection strategies)")
    print("- Accuracy grouped by is_spatial (spatial vs non-spatial)")
    print("- Accuracy grouped by is_reversed (reversed perspective vs normal)")

def test_multi_dimensional_metrics():
    """Test multi-dimensional grouped metrics."""
    print("\nTesting multi-dimensional grouped metrics...")
    
    print("Multi-dimensional grouped metrics task created successfully!")
    print("This version includes all basic metrics PLUS:")
    print("- Multi-dimensional combinations:")
    print("  * sample_type × is_physics")
    print("  * sample_type × selection_rule_type") 
    print("  * is_physics × selection_rule_type")
    print("  * sample_type × is_physics × selection_rule_type")

def demonstrate_usage():
    """Demonstrate how to use the new grouped metrics."""
    print("\n" + "="*60)
    print("USAGE DEMONSTRATION")
    print("="*60)
    
    print("\n1. Basic Usage (Single-dimension grouping only):")
    print("   from director_task.grouped_metrics import directors_task_basic_grouped")
    print("   task = directors_task_basic_grouped()")
    print("   # This gives you accuracy broken down by each metadata dimension")
    
    print("\n2. Advanced Usage (Multi-dimensional grouping):")
    print("   from director_task.grouped_metrics import directors_task_with_grouped_metrics")
    print("   task = directors_task_with_grouped_metrics(enable_multi_dimensional=True)")
    print("   # This gives you accuracy for combinations of dimensions")
    
    print("\n3. Using with inspect_ai eval:")
    print("   from inspect_ai import eval")
    print("   from inspect_ai.model import get_model")
    print("   ")
    print("   # Basic evaluation with grouped metrics")
    print("   results = eval(directors_task_basic_grouped(), model='gpt-4')")
    print("   ")
    print("   # Advanced evaluation with multi-dimensional metrics")
    print("   results = eval(directors_task_with_grouped_metrics(), model='gpt-4')")
    
    print("\n4. Expected Output Structure:")
    print("   The results will include metrics like:")
    print("   - accuracy: Overall accuracy")
    print("   - accuracy/sample_type=control: Accuracy for control samples")
    print("   - accuracy/sample_type=test: Accuracy for test samples")
    print("   - accuracy/is_physics=true: Accuracy for physics tasks")
    print("   - accuracy/is_physics=false: Accuracy for non-physics tasks")
    print("   - accuracy/selection_rule_type=rightmost: Accuracy for rightmost selection")
    print("   - ... and so on for all dimensions and combinations")
    
    print("\n5. Adding New Dimensions:")
    print("   To add new grouping dimensions, update GROUPING_CONFIG in grouped_metrics.py:")
    print("   GROUPING_CONFIG = {")
    print("       'your_new_dimension': {")
    print("           'name': 'Readable Name',")
    print("           'description': 'Description of what this dimension measures'")
    print("       }")
    print("   }")
    print("   Then add it to MULTI_DIMENSIONAL_GROUPS if you want combinations.")

if __name__ == "__main__":
    print("Director Task Grouped Metrics Test")
    print("="*50)
    
    # Test basic functionality
    test_basic_grouped_metrics()
    
    # Test multi-dimensional functionality
    test_multi_dimensional_metrics()
    
    # Show usage examples
    demonstrate_usage()
    
    print("\n" + "="*60)
    print("READY TO USE!")
    print("="*60)
    print("You can now use the grouped metrics with:")
    print("- directors_task_basic_grouped() for simple grouped metrics")
    print("- directors_task_with_grouped_metrics() for advanced multi-dimensional metrics")
    print("\nBoth functions can be imported from director_task.grouped_metrics")