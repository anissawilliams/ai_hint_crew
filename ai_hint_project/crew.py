# crew.py
import os, sys, re, yaml, streamlit as st
from crewai import Crew, Agent, Task
#from langchain_openai import ChatOpenAI
from langchain_community.llms.fake import FakeListLLM
from langchain_groq import ChatGroq
from ai_hint_project.tools.rag_tool import build_rag_tool
from . import levels

print("✅ crew.py loaded")

# 🔧 Base paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# 🧠 LLM loader
def get_llm():
    llm = ChatGroq(
    groq_api_key="your-key",
    model_name="llama-3.1-8b-instant"
    )



# def get_llm():
#     provider = st.secrets.get("LLM_PROVIDER", "openai").lower()
#     try:
#         if provider == "groq":
#             return ChatGroq(
#                 groq_api_key=st.secrets["GROQ_API_KEY"],
#                 model_name="llama3-8b-8192"  # Update if needed
#             )
#         else:
#             return ChatOpenAI(
#                 api_key=st.secrets["OPENAI_API_KEY"],
#                 model=st.secrets.get("OPENAI_MODEL", "gpt-3.5-turbo")
#             )
#     except Exception as e:
#         print("⚠️ LLM load failed, using dummy:", e)
#         return FakeListLLM(responses=["This is a fallback response."])

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
