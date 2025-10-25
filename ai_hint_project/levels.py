import json
import os

# Base directory and path to the levels file
base_dir = os.path.dirname(__file__)
path = os.path.join(base_dir, 'config/agent_levels.json')


def load_levels():
    """Loads the levels from the JSON file."""
    try:
        with open(path, 'r') as f:
            levels = json.load(f)
            return levels
    except FileNotFoundError:
        # Handle file not found (if this is the first time or a problem)
        print("⚠️ agent_levels.json not found. Creating a new file.")
        return {}  # Return an empty dictionary if no file exists


def save_levels(data):
    """Saves the updated levels to the JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def update_level(agent_name):
    """Updates the agent's level based on tasks completed."""
    # Load the levels at the start of the function
    levels = load_levels()

    # Get the agent's current data (or default to level 1 if not found)
    agent = levels.get(agent_name, {"level": 1, "tasks_completed": 0})

    # Increment tasks completed
    agent["tasks_completed"] += 1

    # Apply leveling logic
    if agent["tasks_completed"] >= 5 and agent["level"] == 1:
        agent["level"] = 2
    elif agent["tasks_completed"] >= 10 and agent["level"] == 2:
        agent["level"] = 3

    # Save the updated agent data back to the levels dictionary
    levels[agent_name] = agent
    save_levels(levels)

    print(f"Updated {agent_name}: Level {agent['level']}, Tasks Completed {agent['tasks_completed']}")
