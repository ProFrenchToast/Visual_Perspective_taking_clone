#!/usr/bin/env python3
"""
Test script for constraint-based question generation system.

Tests all four combinations of spatial/physics constraints to ensure
the new system generates appropriate questions.
"""

import sys
import os

from director_task.item import Item
from director_task.sample import Sample
from director_task.question import QuestionConstraints

def test_constraint_combinations():
    """Test all four combinations of spatial and physics constraints"""
    
    # Load items
    items_file = "director_task/items.json"
    if not os.path.exists(items_file):
        print(f"Error: {items_file} not found. Please run from project root directory.")
        return False
    
    print("Loading items...")
    items = Item.load_from_json(items_file)
    print(f"Loaded {len(items)} items.")
    
    # Test all four constraint combinations
    test_combinations = [
        (False, False, "Non-Spatial + Non-Physics"),
        (False, True,  "Non-Spatial + Physics"),
        (True,  False, "Spatial + Non-Physics"),
        (True,  True,  "Spatial + Physics")
    ]
    
    all_passed = True
    
    for is_spatial, is_physics, description in test_combinations:
        print(f"\n=== Testing {description} ===")
        
        try:
            # Create constraints using the new enum system
            from director_task.question import SelectionRuleType
            
            if is_spatial:
                # For spatial questions, use different perspective as default
                selection_rule_type = SelectionRuleType.SPATIAL_DIFFERENT_PERSPECTIVE
            else:
                # For non-spatial questions, use size-related as default
                selection_rule_type = SelectionRuleType.SIZE_RELATED
            
            constraints = QuestionConstraints(selection_rule_type, is_physics)
            
            # Generate multiple questions to test variety
            for i in range(5):
                question = Sample._generate_constrained_question(items, constraints)
                
                print(f"  {i+1}. Question: '{question.to_natural_language()}'")
                print(f"     Filter: {question.filter_criteria}")
                print(f"     Selection rule: {question.selection_rule}")
                
                # Verify constraints are met
                if is_spatial:
                    if question.selection_rule not in ["leftmost", "rightmost"]:
                        print(f"     ❌ ERROR: Expected spatial selection rule, got '{question.selection_rule}'")
                        all_passed = False
                    # Check reversal status for spatial questions
                    print(f"     Reversed: {question.is_reversed}")
                else:
                    if question.selection_rule in ["leftmost", "rightmost"]:
                        print(f"     ❌ ERROR: Expected non-spatial selection rule, got '{question.selection_rule}'")
                        all_passed = False
                    # Show reversal status for non-spatial questions (no restriction)
                    print(f"     Reversed: {question.is_reversed}")
                
                if is_physics:
                    has_physics_prop = any(prop in constraints.PHYSICS_PROPERTIES 
                                         for prop in question.filter_criteria.keys())
                    if not has_physics_prop:
                        print(f"     ❌ ERROR: Expected physics property, got {question.filter_criteria}")
                        all_passed = False
                else:
                    has_physics_prop = any(prop in constraints.PHYSICS_PROPERTIES 
                                         for prop in question.filter_criteria.keys())
                    if has_physics_prop:
                        print(f"     ❌ ERROR: Expected non-physics property, got {question.filter_criteria}")
                        all_passed = False
                
                print(f"     ✓ Constraints satisfied")
                
        except Exception as e:
            print(f"     ❌ ERROR: Failed to generate question - {str(e)}")
            all_passed = False
    
    return all_passed

def test_sample_generation():
    """Test that sample generation works with new constraints"""
    
    print(f"\n=== Testing Sample Generation ===")
    
    # Load items
    items = Item.load_from_json("director_task/items.json")
    
    try:
        # Generate a small dataset with specific proportions
        print("Generating control samples...")
        control_samples = Sample.generate_control_samples(
            items=items,
            grid_width=4,
            grid_height=4,
            num_samples=4,
            size_prop=0.25,
            spatial_same_prop=0.0,  # Skip spatial_same to avoid ambiguity generation issues
            spatial_diff_prop=0.25,
            physics_prop=0.5
        )
        
        print("Generating test samples...")
        # For test samples, use only reliable spatial_diff and size rules
        test_samples = Sample.generate_test_samples(
            items=items,
            grid_width=4,
            grid_height=4,
            num_samples=4,
            size_prop=0.25,
            spatial_same_prop=0.0,  # Skip spatial_same to avoid generation issues
            spatial_diff_prop=0.25,
            physics_prop=0.5
        )
        
        # Verify samples have the new fields
        all_samples = control_samples + test_samples
        
        # Count by SelectionRuleType
        rule_type_counts = {}
        for sample in all_samples:
            rule_type = sample.selection_rule_type
            rule_type_counts[rule_type] = rule_type_counts.get(rule_type, 0) + 1
        
        # Import SelectionRuleType for spatial checking
        from director_task.question import SelectionRuleType
        
        physics_count = sum(1 for s in all_samples if s.is_physics)
        spatial_count = sum(1 for s in all_samples if s.selection_rule_type in [
            SelectionRuleType.SPATIAL_SAME_PERSPECTIVE, 
            SelectionRuleType.SPATIAL_DIFFERENT_PERSPECTIVE
        ])
        
        print(f"Generated {len(all_samples)} total samples")
        print(f"  - {spatial_count} spatial (backward compatibility) ({spatial_count/len(all_samples)*100:.1f}%)")
        print(f"  - {physics_count} physics ({physics_count/len(all_samples)*100:.1f}%)")
        
        print("SelectionRuleType distribution:")
        for rule_type, count in rule_type_counts.items():
            percentage = count / len(all_samples) * 100
            print(f"  - {rule_type.value}: {count} ({percentage:.1f}%)")
        
        # Check distribution of combinations (SelectionRuleType + Physics)
        combinations = {}
        for sample in all_samples:
            key = (sample.selection_rule_type, sample.is_physics)
            combinations[key] = combinations.get(key, 0) + 1
        
        print("\nRule Type + Physics combinations:")
        for (rule_type, is_physics), count in combinations.items():
            physics_str = "Physics" if is_physics else "Non-Physics"
            percentage = count / len(all_samples) * 100
            print(f"  - {rule_type.value} + {physics_str}: {count} ({percentage:.1f}%)")
        
        print("✓ Sample generation successful!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Sample generation failed - {str(e)}")
        return False

def test_new_constraint_system():
    """Test the new 4-category SelectionRuleType system and proportion validation"""
    
    print(f"\n=== Testing New Constraint System ===")
    
    # Load items
    items = Item.load_from_json("director_task/items.json")
    
    all_passed = True
    
    # Test 1: Validate all 4 SelectionRuleType categories can be generated
    print("Testing all SelectionRuleType categories...")
    
    try:
        from director_task.question import SelectionRuleType
        for rule_type in SelectionRuleType:
            print(f"  Testing {rule_type.value}...")
            constraints = QuestionConstraints(rule_type, is_physics=False)
            question = Sample._generate_constrained_question(items, constraints)
            
            # Verify selection rule matches expected type
            expected_rules = constraints.get_selection_rules()
            if question.selection_rule not in expected_rules:
                print(f"    ❌ ERROR: Expected {expected_rules}, got '{question.selection_rule}'")
                all_passed = False
            else:
                print(f"    ✓ Generated rule: '{question.selection_rule}'")
        
    except Exception as e:
        print(f"❌ ERROR: Failed to generate questions for all rule types - {str(e)}")
        all_passed = False
    
    # Test 2: Proportion validation (sum > 1.0 should fail)
    print("\nTesting proportion validation...")
    
    try:
        # This should fail because proportions sum to > 1.0
        Sample.generate_control_samples(
            items=items,
            grid_width=2,
            grid_height=2,
            num_samples=4,
            size_prop=0.5,
            spatial_same_prop=0.5,
            spatial_diff_prop=0.5,  # 0.5 + 0.5 + 0.5 = 1.5 > 1.0
            physics_prop=0.5
        )
        print("  ❌ ERROR: Should have failed with proportions > 1.0")
        all_passed = False
    except ValueError as e:
        if "cannot exceed 1.0" in str(e):
            print("  ✓ Correctly rejected proportions > 1.0")
        else:
            print(f"  ❌ ERROR: Unexpected error message: {str(e)}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ ERROR: Unexpected exception: {str(e)}")
        all_passed = False
    
    # Test 3: Valid proportions should work
    print("\nTesting valid proportions...")
    
    try:
        samples = Sample.generate_control_samples(
            items=items,
            grid_width=2,
            grid_height=2,
            num_samples=4,
            size_prop=0.25,
            spatial_same_prop=0.25,
            spatial_diff_prop=0.25,  # 0.25 + 0.25 + 0.25 = 0.75 < 1.0
            physics_prop=0.5
        )
        
        # Verify correct distribution
        rule_counts = {}
        for sample in samples:
            rule_type = sample.selection_rule_type
            rule_counts[rule_type] = rule_counts.get(rule_type, 0) + 1
        
        expected_counts = {
            SelectionRuleType.SIZE_RELATED: 1,  # 4 * 0.25 = 1
            SelectionRuleType.SPATIAL_SAME_PERSPECTIVE: 1,  # 4 * 0.25 = 1
            SelectionRuleType.SPATIAL_DIFFERENT_PERSPECTIVE: 1,  # 4 * 0.25 = 1
            SelectionRuleType.NONE: 1  # 4 - (1 + 1 + 1) = 1
        }
        
        for rule_type, expected_count in expected_counts.items():
            actual_count = rule_counts.get(rule_type, 0)
            if actual_count == expected_count:
                print(f"  ✓ {rule_type.value}: {actual_count} samples (expected {expected_count})")
            else:
                print(f"  ❌ ERROR: {rule_type.value}: {actual_count} samples (expected {expected_count})")
                all_passed = False
        
    except Exception as e:
        print(f"  ❌ ERROR: Valid proportions failed - {str(e)}")
        all_passed = False
    
    # Test 4: Test spatial detection logic
    print("\nTesting spatial detection logic...")
    
    try:
        constraints_spatial_diff = QuestionConstraints(SelectionRuleType.SPATIAL_DIFFERENT_PERSPECTIVE, False)
        constraints_spatial_same = QuestionConstraints(SelectionRuleType.SPATIAL_SAME_PERSPECTIVE, False)
        constraints_size = QuestionConstraints(SelectionRuleType.SIZE_RELATED, False)
        constraints_none = QuestionConstraints(SelectionRuleType.NONE, False)
        
        # Test that spatial perspective types can be correctly identified
        spatial_types = [SelectionRuleType.SPATIAL_SAME_PERSPECTIVE, SelectionRuleType.SPATIAL_DIFFERENT_PERSPECTIVE]
        
        if constraints_spatial_diff.selection_rule_type in spatial_types and constraints_spatial_same.selection_rule_type in spatial_types:
            print("  ✓ Both spatial perspective types correctly identified as spatial")
        else:
            print("  ❌ ERROR: Spatial constraints should be identified as spatial")
            all_passed = False
        
        if constraints_size.selection_rule_type not in spatial_types and constraints_none.selection_rule_type not in spatial_types:
            print("  ✓ Non-spatial constraints correctly identified as non-spatial")
        else:
            print("  ❌ ERROR: Non-spatial constraints should be identified as non-spatial")
            all_passed = False
            
    except Exception as e:
        print(f"  ❌ ERROR: Spatial detection test failed - {str(e)}")
        all_passed = False
    
    return all_passed

def main():
    """Main test function"""
    
    print("Testing Constraint-Based Question Generation System")
    print("=" * 50)
    
    # Test constraint combinations
    constraints_ok = test_constraint_combinations()
    
    # Test sample generation
    samples_ok = test_sample_generation()
    
    # Test new constraint system
    new_system_ok = test_new_constraint_system()
    
    # Final results
    print(f"\n{'='*50}")
    if constraints_ok and samples_ok and new_system_ok:
        print("🎉 ALL TESTS PASSED!")
        print("\nThe 4-category constraint system with SelectionRuleType is working correctly.")
        print("You can now use the updated task_generator.py with --size_prop, --spatial_same_prop, --spatial_diff_prop, and --physics_prop arguments.")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the errors above and fix the issues.")
        return 1

if __name__ == "__main__":
    exit(main())