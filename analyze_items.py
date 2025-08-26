#!/usr/bin/env python3

from director_task.item import Item
import json

# Load items and analyze what combinations exist
items = Item.load_from_json('director_task/items.json')
print(f'Total items: {len(items)}')

# Analyze what target types exist
target_types = set()
colors = set()
physics_props = set()

for item in items:
    # Find target types (category properties)
    for prop, value in item.boolean_properties.items():
        if value and prop in ['star', 'circle', 'car']:  # Known target types
            target_types.add(prop)
        if value and prop in ['red', 'blue', 'green', 'yellow', 'orange', 'black', 'purple', 'brown']:
            colors.add(prop)
        if value and prop in ['stackable', 'sharp', 'hot', 'cold']:
            physics_props.add(prop)

print(f'Available target types in items: {sorted(target_types)}')
print(f'Available colors in items: {sorted(colors)}')
print(f'Available physics properties in items: {sorted(physics_props)}')

# Check what other category properties exist
all_category_props = ['Music_instument', 'fruit', 'bag', 'book', 'calculator', 'shoe', 'camera', 
                     'clothes', 'shirt', 'plant', 'socks', 'dress', 'car']

existing_categories = set()
for item in items:
    for prop in all_category_props:
        if item.boolean_properties.get(prop, False):
            existing_categories.add(prop)

print(f'Available category properties in items: {sorted(existing_categories)}')

# Check some specific combinations that failed
print('\nChecking specific combinations that failed:')
combinations_to_check = [
    {'shirt': True, 'green': True},
    {'book': True, 'cold': True, 'black': True},
    {'dress': True, 'black': True},
    {'bag': True, 'sharp': True, 'orange': True}
]

for combo in combinations_to_check:
    exists = False
    for item in items:
        matches = True
        for prop, value in combo.items():
            if item.boolean_properties.get(prop, False) != value:
                matches = False
                break
        if matches:
            exists = True
            break
    print(f'{combo}: {"EXISTS" if exists else "MISSING"}')

# Show sample of actual item properties
print('\nSample of first 5 items and their properties:')
for i, item in enumerate(items[:5]):
    true_props = [prop for prop, value in item.boolean_properties.items() if value]
    print(f'{item.name}: {true_props}')