import os
import sys
import re
import yaml
import streamlit as st
from crewai import Crew, Agent, Task
from ai_hint_project.tools.rag_tool import build_rag_tool
from langchain_openai import ChatOpenAI
from langchain_community.llms.fake import FakeListLLM
import cohere
from . import levels

print("✅ crew.py loaded")

# 🔧 Base paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

import requests
import streamlit as st
import json

# Retrieve the Hugging Face Access Token from Streamlit secrets
HF_ACCESS_TOKEN = st.secrets["HUGGINGFACE_ACCESS_TOKEN"]

# Hugging Face model endpoint (for GPT-2, you can change it to other models as needed)
HF_API_URL = "https://api-inference.huggingface.co/models/gpt2"  # You can use other models like gpt-j or distilGPT

def get_llm():
    # Prepare the headers with Authorization
    headers = {
        "Authorization": f"Bearer {HF_ACCESS_TOKEN}",
        "Content-Type": "application/json"  # Ensure the content type is set to JSON
    }

    # Prepare the data (the prompt text to pass to the model)
    data = {
        "inputs": "Hello, Hugging Face! Can you help me?",  # Sample prompt for testing
        "parameters": {
            "max_length": 100  # Optional: Controls the maximum length of the output
        }
    }

    try:
        print("🔌 Sending request to Hugging Face API...")

        # Send POST request to the Hugging Face API
        response = requests.post(HF_API_URL, headers=headers, json=data)

        # Check if the response is successful
        if response.status_code == 200:
            print("✅ Hugging Face LLM successfully loaded!")
            return response.json()  # Return the generated response as JSON
        else:
            print(f"⚠️ Error: {response.status_code} - {response.text}")
            return None  # Return None if error occurs
    except Exception as e:
        print(f"⚠️ Exception occurred: {e}")
        return None  # Return None in case of an exception

# Test the LLM call
llm_response = get_llm()

if llm_response:
    print("Generated Text:", llm_response[0]['generated_text'])
else:
    print("⚠️ Unable to generate text, using fallback.")



# ✅ Build RAG tool
rag_folder = os.path.join(base_dir, "baeldung_scraper")
rag_tool, _ = build_rag_tool(
    index_path=os.path.join(rag_folder, "baeldung_scraper"),
    chunks_path=os.path.join(rag_folder, "chunks.json")
)

# 🎭 Persona reactions
persona_reactions = {
    "Batman": "Code received. Let’s patch the vulnerability.",
    "Yoda": "Code, you have pasted. Analyze it, we must.",
    "Spider-Gwen": "Let’s swing through this syntax.",
    "Shuri": "Let’s scan it with Wakandan tech.",
    "Elsa": "Let me freeze the bugs and refactor.",
    "Wednesday Addams": "Let’s dissect it like a corpse.",
    "Iron Man": "Let’s run diagnostics and upgrade it.",
    "Nova": "Let’s orbit through its logic.",
    "Zee": "Let’s treat this like a boss fight.",
    "Sherlock Holmes": "Let’s deduce its structure."
}

# 🧠 Detect code input
def is_code_input(text):
    code_patterns = [
        r"\bdef\b", r"\bclass\b", r"\bimport\b", r"\breturn\b",
        r"\bif\b\s*\(?.*?\)?\s*:", r"\bfor\b\s*\(?.*?\)?\s*:", r"\bwhile\b\s*\(?.*?\)?\s*:",
        r"\btry\b\s*:", r"\bexcept\b\s*:", r"\w+\s*=\s*.+", r"\w+\(.*?\)", r"{.*?}", r"<.*?>"
    ]
    return any(re.search(pattern, text) for pattern in code_patterns)

# 📦 Load YAML
def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# 🚀 Crew creation
def create_crew(persona: str, user_question: str):
    print(f"✅ create_crew() called with persona: {persona}")

    # Load agent and task configurations from YAML files
    base_dir = os.path.dirname(__file__)
    agents_config = load_yaml(os.path.join(base_dir, 'config/agents.yaml'))
    tasks_config = load_yaml(os.path.join(base_dir, 'config/tasks.yaml'))

    # Get the configuration for the selected persona
    agent_cfg = agents_config['agents'].get(persona)
    if not agent_cfg:
        raise ValueError(f"Unknown persona: {persona}")

    # Get the LLM (language model) instance
    llm = get_llm()
    print("✅ LLM type:", type(llm))

    # Create an agent based on persona and task configuration
    agent = Agent(
        role=agent_cfg["role"],
        goal=agent_cfg["goal"],
        backstory=agent_cfg["backstory"],
        level=agent_cfg.get("level", "beginner"),
        verbose=False,
        llm=llm
    )

    # Add persona-specific reactions to the task description
    reaction = persona_reactions.get(persona, "No reaction available.")
    task_description = f"{reaction}\n\n{user_question}" if is_code_input(user_question) else user_question

    # Get the context for the task using the RAG tool
    context = rag_tool(user_question)

    # Create the task based on the configuration
    task_template = tasks_config['tasks']['explainer']
    task = Task(
        name=task_template['name'],
        description=task_template['description'].format(query=f"{task_description}\n\nRelevant context:\n{context}"),
        expected_output=task_template['expected_output'],
        agent=agent
    )

    # Create the crew (with one agent and one task)
    crew = Crew(agents=[agent], tasks=[task], verbose=True)

    # Kick off the crew and get the result
    result = crew.kickoff()

    # Update the agent's level (if applicable)
    levels.update_level(persona)

    # Clean the output to remove unwanted tags
    cleaned_content = re.sub(r"<think>.*?</think>\n?", "", result.tasks_output[0].raw, flags=re.DOTALL)

    return cleaned_content
