import streamlit as st
import sys
import os
import yaml
import traceback

# 📁 Setup paths
base_dir = os.path.dirname(__file__)

# Load YAML
def load_yaml(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"YAML config not found at: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

from ai_hint_project.crew import create_crew

# Cache persona and configuration data to avoid unnecessary reloads
@st.cache_data(show_spinner=False)
def get_cached_persona_data():
    return load_yaml(os.path.join(base_dir, 'ai_hint_project/config/agents.yaml'))

# Initialize session state
if 'level' not in st.session_state:
    st.session_state.level = 5  # Default to all levels available
if 'explanation' not in st.session_state:
    st.session_state.explanation = None

agents_config = get_cached_persona_data()

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
backgrounds = {}  # Fixed: uncommented this line
persona_options = {}
persona_avatars = {}

for name, data in agents.items():
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

if not available_personas:
    st.error("⚠️ No personas available. Check your YAML configuration.")
    st.stop()

# 🎨 Apply Background
selected_persona = st.selectbox(
    "Choose your explainer", 
    options=available_personas, 
    key="persona_selector"
)

selected_background = backgrounds.get(selected_persona, "#ffffff")
st.markdown(f"""
    <style>
        .stApp {{
            background: {selected_background};
            background-attachment: fixed;
        }}
    </style>
""", unsafe_allow_html=True)

# 🧠 Persona Preview
st.markdown(f"### {persona_avatars[selected_persona]} {selected_persona} is ready to explain!")
st.markdown(f"**{persona_options[selected_persona]}**")

# 💬 Question Input
user_question = st.text_area("Ask your programming question:", key="question_input")

if user_question and any(x in user_question for x in ["def ", "class ", "{", "}", "()", "<", ">", "if ", "for ", "while "]):
    st.markdown("🧑‍💻 Code detected! Your explainer will respond accordingly.")

# 🚀 Trigger Explanation
if st.button("Explain it!", type="primary"):
    if not user_question.strip():
        st.warning("⚠️ Please enter a question first!")
    else:
        try:
            with st.spinner("🧠 Thinking..."):
                result = create_crew(selected_persona, user_question)
            
            # Save the result in session_state
            st.session_state.explanation = result
            
            # Rerun to show the explanation in the dedicated section below
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            with st.expander("Show detailed error"):
                st.code(traceback.format_exc())

# Display stored explanation (only once, below the button)
if st.session_state.explanation:
    st.markdown("---")
    st.markdown("### 🗣️ Explanation")
    st.markdown(f"""
    <div style="background-color:#e6f7ff;padding:15px;border-radius:10px;border-left:4px solid #1890ff;">
        {st.session_state.explanation}
    </div>
    """, unsafe_allow_html=True)
    
    # Add a clear button
    if st.button("Clear explanation"):
        st.session_state.explanation = None
        st.rerun()

# Collect multiple dimensions
st.subheader("Please rate this explanation:")
clarity = st.slider("Clarity", 1, 5, 3)
accuracy = st.slider("Accuracy", 1, 5, 3)
helpfulness = st.slider("Helpfulness", 1, 5, 3)

# Optional qualitative feedback
feedback = st.text_area("Additional comments (optional):")

if st.button("Submit Rating"):
    rating_data = {
        "timestamp": datetime.now().isoformat(),
        "persona": selected_persona,
        "question": user_question,
        "clarity": clarity,
        "accuracy": accuracy,
        "helpfulness": helpfulness, 
        "feedback": feedback,
        "user_level": st.session_state.level
    }
    
    # Append to JSON file
    with open("ratings.json", "a") as f:
        f.write(json.dumps(rating_data) + "\n")
