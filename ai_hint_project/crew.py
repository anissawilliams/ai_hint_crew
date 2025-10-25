# crew.py
print("✅ crew.py loaded")

import streamlit as st
import os
import sys
import yaml
import re
import json
import faiss
from crewai import Crew, Agent, Task
from . import levels
from ai_hint_project.tools.rag_tool import build_rag_tool
from openai import OpenAI
from langchain_openai import ChatOpenAI


# 🔧 Base paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# ✅ Initialize LangChain-compatible LLM

api_key = st.secrets["OPENAI_API_KEY"]
if not api_key or not api_key.startswith("sk-"):
    raise RuntimeError("OPENAI_API_KEY is missing or malformed.")

client = OpenAI(api_key=api_key) 
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7,
    api_key=api_key
)

print("🔑 OPENAI_API_KEY:", repr(api_key))
# ✅ Build RAG tool
rag_folder = os.path.join(base_dir, "baeldung_scraper")
rag_tool, _ = build_rag_tool(
    index_path=os.path.join(rag_folder, "baeldung_index.faiss"),
    chunks_path=os.path.join(rag_folder, "chunks.json")
)

# 🔍 Load YAML config
def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# 🧠 Detect if input contains code
def is_code_input(text):
    code_patterns = [
        r"\bdef\b", r"\bclass\b", r"\bimport\b", r"\breturn\b",
        r"\bif\b\s*\(?.*?\)?\s*:", r"\bfor\b\s*\(?.*?\)?\s*:", r"\bwhile\b\s*\(?.*?\)?\s*:",
        r"\btry\b\s*:", r"\bexcept\b\s*:", r"\w+\s*=\s*.+", r"\w+\(.*?\)", r"{.*?}", r"<.*?>"
    ]
    return any(re.search(pattern, text) for pattern in code_patterns)

# 🎭 Persona-specific reactions
persona_reactions = {
    "Batman": "Code received. Looks like a breach in logic. Let’s patch the vulnerability before it spreads.",
    "Yoda": "Code, you have pasted. Analyze it, we must. Hidden, the bug may be.",
    "Spider-Gwen": "Nice drop! Let’s swing through this syntax and catch any bugs midair.",
    "Shuri": "Vibranium-grade logic? Let’s scan it with Wakandan tech and optimize the flow.",
    "Elsa": "This code is… chaotic. Let me freeze the bugs and refactor with elegance.",
    "Wednesday Addams": "You’ve pasted code. How delightfully broken it looks. Let’s dissect it like a corpse.",
    "Iron Man": "Code drop detected. Let’s run diagnostics and upgrade it to Stark-level performance.",
    "Nova": "Cosmic code detected. Let’s orbit through its logic and illuminate the stars within.",
    "Zee": "Code incoming! Let’s treat this like a boss fight and break it down tactically.",
    "Sherlock Holmes": "Ah, a code snippet. Let’s deduce its structure and uncover any hidden flaws."
}

# ✅ Crew creation
def create_crew(persona: str, user_question: str):
    print("✅ create_crew() called with persona:", persona)

    base_dir = os.path.dirname(__file__)
    agents_config = load_yaml(os.path.join(base_dir, 'config/agents.yaml'))
    tasks_config = load_yaml(os.path.join(base_dir, 'config/tasks.yaml'))
    print("🔑 OPENAI_API_KEY loaded:", bool(os.getenv("OPENAI_API_KEY")))
    agent_cfg = agents_config['agents'].get(persona)
    if not agent_cfg:
        raise ValueError(f"Unknown persona: {persona}")

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
