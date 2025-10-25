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

print("✅ crew.py loaded")

# 🔧 Base paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

import requests
import streamlit as st

# Use your Hugging Face API key
HF_API_KEY = st.secrets["HUGGINGFACE_ACCESS_TOKEN"]  # Ensure you add this secret in Streamlit secrets

# Hugging Face model endpoint
HF_API_URL = "https://api-inference.huggingface.co/models/gpt2"  # Replace with your chosen model (e.g., gpt2, gpt-j)

class FakeListLLM:
    def __init__(self, responses):
        self.responses = responses

    def invoke(self, prompt):
        return self.responses[0]

def get_llm():
    retries = 3
    backoff_factor = 2
    max_wait_time = 60  # in seconds

    for attempt in range(retries):
        try:
            print("🔌 Trying Hugging Face API...")

            headers = {
                "Authorization": f"Bearer {HF_API_KEY}"
            }

            # Prepare the request payload
            data = {
                "inputs": "Hello, Hugging Face!",  # Sample prompt for testing
                "parameters": {
                    "max_length": 100
                }
            }

            # Send the POST request to Hugging Face's hosted model
            response = requests.post(HF_API_URL, headers=headers, json=data)

            # If the request is successful
            if response.status_code == 200:
                print("✅ Hugging Face LLM loaded")
                return response  # Return the response to be used later

            # Handle rate limiting (429 error)
            elif response.status_code == 429:
                remaining = response.headers.get("X-RateLimit-Remaining", 0)
                reset_time = response.headers.get("X-RateLimit-Reset", time.time())
                wait_time = max(0, reset_time - time.time())
                print(f"⚠️ Rate limit hit. {remaining} requests remaining. Retrying in {wait_time} seconds.")
                time.sleep(wait_time)  # Wait before retrying
                continue

            else:
                print(f"⚠️ Error: {response.status_code} - {response.text}")
                return FakeListLLM(responses=["API error: Unable to fetch response from Hugging Face."])

        except Exception as e:
            print(f"⚠️ Error encountered: {str(e)}")
            return FakeListLLM(responses=["API error: Unable to fetch response."])

    # Fallback if all retries fail
    print("⚠️ Failed after multiple attempts. Using fallback.")
    return FakeListLLM(responses=["This is a fallback response."])

# Usage example to call the LLM
llm = get_llm()
if isinstance(llm, requests.Response):
    generated_text = llm.json()[0]['generated_text']  # Assuming response is in the expected format
    print("Generated Text:", generated_text)
else:
    print("⚠️ Using fallback response.")

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
