import streamlit as st
import sys
import os


import yaml
import traceback

# 📁 Setup paths
#sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

sys.path.append(os.path.join(os.path.dirname(__file__), "ai_hint_project", "src"))

base_dir = os.path.dirname(__file__)
from ai_hint_project.crew import create_crew

@st.cache_data(show_spinner=False)
def get_cached_explanation(persona, question):
    return create_crew(persona, question)



#  Load YAML
def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)
@st.cache_data(show_spinner=False)
def get_cached_explanation(persona, question):
    return create_crew(persona, question)


agents_config = load_yaml(os.path.join(base_dir, 'ai_hint_project/src/ai_hint_project/config/agents.yaml'))

# 🎮 Initialize Level
if "level" not in st.session_state:
    st.session_state.level = 1

level_titles = {
    1: "Curious Coder",
    2: "Debugging Rookie",
    3: "Syntax Sleuth",
    4: "Code Commander",
    5: "Explainer Elite"
}

# 🧠 Validate agents
if not agents_config or 'agents' not in agents_config:
    st.error("⚠️ Failed to load agents from YAML. Check your file path or format.")
    st.stop()

agents = agents_config.get('agents', {})
if not isinstance(agents, dict):
    st.error("⚠️ YAML format error: 'agents' should be a dictionary.")
    st.stop()

# 🎭 Build persona data
persona_by_level = {}
backgrounds = {}
persona_options = {}
persona_avatars = {}

for name, data in agents.items():
    print(f"🔍 Checking agent: {name}, data type: {type(data)}")
    if not isinstance(data, dict):
        st.warning(f"⚠️ Skipping malformed agent: {name}")
        continue
    

    level = data.get('level', 'beginner')
    level_num = {
        "beginner": 1,
        "intermediate": 3,
        "advanced": 5
    }.get(level, 1)

    persona_by_level.setdefault(level_num, []).append(name)
    backgrounds[name] = data.get('background', "#ffffff")
    persona_options[name] = f"{data.get('role', name)} — {data.get('goal', '')}"
    persona_avatars[name] = data.get('avatar', "🧠")

# 🖼️ App Title
st.markdown("<h1 style='text-align: center;'>AI Coding Explainer</h1>", unsafe_allow_html=True)
st.markdown("### Get programming explanations from your favorite personas!")

# 🎯 Filter Available Personas
available_personas = []
for lvl in range(1, st.session_state.level + 1):
    available_personas.extend(persona_by_level.get(lvl, []))

# 🎨 Apply Background
selected_persona = st.selectbox("Choose your explainer", options=available_personas, key="persona_selector")
selected_background = backgrounds.get(selected_persona, "#ffffff")

st.markdown(f"""
    <style>
        body {{
            background: {selected_background};
            background-attachment: fixed;
        }}
    </style>
""", unsafe_allow_html=True)

# 🏆 Level Badge
st.markdown(f"### 🏆 Level {st.session_state.level} — {level_titles[st.session_state.level]}")

# 🧠 Persona Preview
st.markdown(f"### {persona_avatars[selected_persona]} {selected_persona} is ready to explain!")
st.markdown(f"**{persona_options[selected_persona]}**")

# 💬 Question Input
user_question = st.text_area("Ask your programming question:")
if any(x in user_question for x in ["def ", "class ", "{", "}", "()", "<", ">", "if ", "for ", "while "]):
    st.markdown("🧑‍💻 Code detected! Your explainer will respond accordingly.")

# 🚀 Trigger Explanation
if st.button("Explain it!"):
    try:
        with st.spinner("🧠 Thinking..."):
            result = get_cached_explanation(selected_persona, user_question)


        if result:
            st.markdown("### 🗣️ Explanation")
            st.markdown(f"""
            <div style="background-color:#e6f7ff;padding:15px;border-radius:10px;">
                {result}
            </div>
            """, unsafe_allow_html=True)

            # 🎮 Level Up Logic
            if st.session_state.level < 5:
                st.session_state.level += 1
                st.success(f"🎉 You leveled up to Level {st.session_state.level} — {level_titles[st.session_state.level]}!")


    except Exception as e:
        st.error(f"Error: {e}")
        st.text(traceback.format_exc())

