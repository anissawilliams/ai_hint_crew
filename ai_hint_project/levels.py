import json
import os

base_dir = os.path.dirname(__file__)
path = os.path.join(base_dir, 'config/agent_levels.json')



def load_levels():
    with open(path, 'r') as f:
        levels = json.load(f)
        return levels

def save_levels(data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def update_level(agent_name):
    levels = {}
    levels = load_levels()

    agent = levels.get(agent_name, {"level": 1, "tasks_completed": 0})
    agent["tasks_completed"] += 1

    # Leveling logic
    if agent["tasks_completed"] >= 5 and agent["level"] == 1:
        agent["level"] = 2
    elif agent["tasks_completed"] >= 10 and agent["level"] == 2:
        agent["level"] = 3

    levels[agent_name] = agent
    save_levels(levels)
