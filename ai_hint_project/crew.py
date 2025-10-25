# crew.py
import os, sys, re, yaml, streamlit as st
from crewai import Crew, Agent, Task
#from langchain_groq import ChatGroq
from ai_hint_project.tools.rag_tool import build_rag_tool
from . import levels

print("✅ crew.py loaded")

# 🔧 Base paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# 🧠 LLM loader

from langchain_openai import ChatOpenAI
from langchain_community.llms.fake import FakeListLLM

from langchain_openai import ChatOpenAI
from langchain_community.llms.fake import FakeListLLM
import streamlit as st

import streamlit as st
from openrouter import ChatOpenAI

class FakeListLLM:
    def __init__(self, responses):
        self.responses = responses

    def invoke(self, prompt):
        return self.responses[0]

def get_llm():
    try:
        print("🔌 Trying OpenRouter via ChatOpenAI...")
        llm = ChatOpenAI(
            api_key=st.secrets["OPENROUTER_API_KEY"],  # Ensure this is correct
            base_url="https://openrouter.ai/api/v1",  # OpenRouter API URL
            model="gpt-3.5-turbo"  # Try with a simple model name for testing
        )
        # Testing if the model can respond to a simple ping or message
        response = llm.invoke("Hello, OpenRouter!")
        print("✅ OpenRouter LLM loaded with response:", response)
        return llm
    except Exception as e:
        # More detailed error logging
        print(f"⚠️ OpenRouter failed, falling back: {str(e)}")
        return FakeListLLM(responses=["This is a fallback response."])

# Usage example
llm = get_llm()
response = llm.invoke("What is the capital of France?")
print("Response:", response)


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
    print("✅ create_crew() called with persona:", persona)

    base_dir = os.path.dirname(__file__)
    agents_config = load_yaml(os.path.join(base_dir, 'config/agents.yaml'))
    tasks_config = load_yaml(os.path.join(base_dir, 'config/tasks.yaml'))

    agent_cfg = agents_config['agents'].get(persona)
    if not agent_cfg:
        raise ValueError(f"Unknown persona: {persona}")

    llm = get_llm()
    print("✅ LLM type:", type(llm))

    agent = Agent(
        role=agent_cfg["role"],
        goal=agent_cfg["goal"],
        backstory=agent_cfg["backstory"],
        level=agent_cfg.get("level", "beginner"),
        verbose=False,
        llm=llm
    )

    reaction = persona_reactions.get(persona, "")
    task_description = f"{reaction}\n\n{user_question}" if is_code_input(user_question) else user_question
    context = rag_tool(user_question)

    task_template = tasks_config['tasks']['explainer']
    task = Task(
        name=task_template['name'],
        description=task_template['description'].format(query=f"{task_description}\n\nRelevant Java context:\n{context}"),
        expected_output=task_template['expected_output'],
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    levels.update_level(persona)

    cleaned_content = re.sub(r"<think>.*?</think>\n?", "", result.tasks_output[0].raw, flags=re.DOTALL)
    return cleaned_content
