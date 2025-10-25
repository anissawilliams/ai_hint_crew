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

# 🧠 LLM loader
class FakeListLLM:
    def __init__(self, responses):
        self.responses = responses

    def invoke(self, prompt):
        return self.responses[0]

import time
import random

def get_llm():
    retries = 5  # Set a limit for retries
    backoff_factor = 2  # Exponential backoff factor
    max_wait_time = 60  # Max wait time for retries in seconds

    for attempt in range(retries):
        try:
            print("🔌 Trying OpenRouter via ChatOpenAI...")
            llm = ChatOpenAI(
                api_key=st.secrets["OPENROUTER_API_KEY"],  # Ensure this is correct
                base_url="https://openrouter.ai/api/v1",  # OpenRouter API URL
                model="gpt-3.5-turbo"  # Try with a simple model name for testing
            )
            # Test if the model can respond to a simple ping or message
            response = llm.invoke("Hello, OpenRouter!")
            print("✅ OpenRouter LLM loaded with response:", response)
            return llm
        
        except Exception as e:
            if "429" in str(e):  # Check for rate limit error
                wait_time = min(backoff_factor ** attempt, max_wait_time)
                print(f"⚠️ Rate limit hit. Retrying in {wait_time}s...")
                time.sleep(wait_time + random.uniform(0, 5))  # Adding randomness to avoid hitting limits simultaneously
            else:
                print(f"⚠️ Error encountered: {str(e)}")
                break

    # Fallback in case of failure after retries
    print("⚠️ All retries failed, falling back to alternative LLM...")
    return FakeListLLM(responses=["This is a fallback response."])


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
