import streamlit as st
import sys
import os
import yaml
import traceback
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# 🔧 Setup paths
base_dir = os.path.dirname(__file__)
sys.path.insert(0, base_dir)

# Page config
st.set_page_config(page_title="AI Java Tutor Pro", page_icon="🧠", layout="wide")

# Custom CSS with transparent backgrounds
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .level-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 15px;
        border: 2px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 20px;
    }
    .persona-card {
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        transition: transform 0.3s;
        border: 2px solid rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(10px);
    }
    .persona-card:hover {
        transform: scale(1.02);
    }
    .locked-persona {
        opacity: 0.5;
        filter: grayscale(100%);
    }
    .xp-bar {
        height: 30px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 15px;
        overflow: hidden;
        position: relative;
    }
    .xp-fill {
        height: 100%;
        background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%);
        transition: width 0.5s ease;
    }
    .xp-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-weight: bold;
        color: white;
        text-shadow: 0 0 10px rgba(0,0,0,0.5);
    }
    .streak-badge {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 10px 20px;
        border-radius: 20px;
        font-size: 24px;
        font-weight: bold;
        color: white;
    }
    .affinity-bar {
        height: 8px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
        overflow: hidden;
        margin-top: 5px;
    }
    .affinity-fill {
        height: 100%;
        background: linear-gradient(90deg, #ffd93d 0%, #f5576c 100%);
    }
    .explanation-box {
        background-color: rgba(230, 247, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1890ff;
        margin: 15px 0;
        color: white;
    }
    .reward-popup {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 50px rgba(0,0,0,0.5);
        z-index: 1000;
        text-align: center;
        animation: bounceIn 0.5s;
    }
    @keyframes bounceIn {
        0% { transform: translate(-50%, -50%) scale(0.3); }
        50% { transform: translate(-50%, -50%) scale(1.05); }
        100% { transform: translate(-50%, -50%) scale(1); }
    }
    /* Ensure text is readable on all backgrounds */
    .stApp {
        background-attachment: fixed;
    }
    </style>
""", unsafe_allow_html=True)

# Load YAML
def load_yaml(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"YAML config not found at: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# Import AI crew
try:
    from ai_hint_project.crew import create_crew
    AI_AVAILABLE = True
except ImportError:
    st.warning("⚠️ AI crew module not found. Running in demo mode.")
    AI_AVAILABLE = False
    def create_crew(persona, question):
        return f"[Demo Mode] {persona} would explain: {question[:50]}..."

# Cache persona data
@st.cache_data(show_spinner=False)
def get_cached_persona_data():
    yaml_path = os.path.join(base_dir, 'ai_hint_project/config/agents.yaml')
    return load_yaml(yaml_path)

# Load/Save gamification data
def load_user_progress():
    filepath = os.path.join(base_dir, "user_progress.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading progress: {e}")
    return {
        'level': 1,
        'xp': 0,
        'streak': 0,
        'last_visit': None,
        'affinity': {}
    }

def save_user_progress(data):
    filepath = os.path.join(base_dir, "user_progress.json")
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving progress: {e}")
        return False

# Load historical ratings
@st.cache_data(ttl=60)
def load_historical_ratings():
    filepath = os.path.join(base_dir, "ratings.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = [json.loads(line) for line in f if line.strip()]
                if data:
                    return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error loading ratings: {e}")
    return pd.DataFrame()

def save_rating(rating_data):
    filepath = os.path.join(base_dir, "ratings.json")
    try:
        with open(filepath, "a") as f:
            f.write(json.dumps(rating_data) + "\n")
        return True
    except Exception as e:
        st.error(f"Error saving rating: {e}")
        return False

# Gamification helpers
def get_xp_for_level(level):
    return level * 100

def get_level_tier(level):
    if level <= 10:
        return {'name': 'Beginner', 'color': '#43e97b', 'icon': '🌱'}
    elif level <= 20:
        return {'name': 'Intermediate', 'color': '#38f9d7', 'icon': '💪'}
    else:
        return {'name': 'Advanced', 'color': '#667eea', 'icon': '🚀'}

def add_xp(amount):
    """Add XP and check for level up"""
    progress = st.session_state.user_progress
    progress['xp'] += amount
    
    next_level_xp = get_xp_for_level(progress['level'])
    
    if progress['xp'] >= next_level_xp:
        progress['level'] += 1
        st.session_state.show_reward = {
            'type': 'level_up',
            'level': progress['level']
        }
        st.balloons()
    
    save_user_progress(progress)
    st.session_state.user_progress = progress

def update_streak():
    """Update daily streak"""
    progress = st.session_state.user_progress
    today = datetime.now().date().isoformat()
    
    if progress['last_visit'] != today:
        last_date = datetime.fromisoformat(progress['last_visit']).date() if progress['last_visit'] else None
        yesterday = (datetime.now().date() - timedelta(days=1))
        
        if last_date == yesterday:
            progress['streak'] += 1
            if progress['streak'] % 7 == 0:
                st.session_state.show_reward = {
                    'type': 'streak',
                    'days': progress['streak']
                }
                add_xp(20)  # Bonus XP
        elif last_date != datetime.now().date():
            progress['streak'] = 1
        
        progress['last_visit'] = today
        save_user_progress(progress)
        st.session_state.user_progress = progress

def add_affinity(persona_name, amount):
    """Add affinity points to a persona"""
    progress = st.session_state.user_progress
    if 'affinity' not in progress:
        progress['affinity'] = {}
    
    progress['affinity'][persona_name] = progress['affinity'].get(persona_name, 0) + amount
    save_user_progress(progress)
    st.session_state.user_progress = progress

# Initialize session state
def init_session_state():
    if 'user_progress' not in st.session_state:
        st.session_state.user_progress = load_user_progress()
    
    if 'explanation' not in st.session_state:
        st.session_state.explanation = None
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""
    if 'current_persona' not in st.session_state:
        st.session_state.current_persona = None
    if 'show_analytics' not in st.session_state:
        st.session_state.show_analytics = False
    if 'show_rating' not in st.session_state:
        st.session_state.show_rating = False
    if 'show_reward' not in st.session_state:
        st.session_state.show_reward = None

init_session_state()

# Update streak on page load
update_streak()

# Load data
try:
    agents_config = get_cached_persona_data()
    agents = agents_config.get('agents', {})
except Exception as e:
    st.error(f"⚠️ Failed to load agents: {e}")
    st.stop()

if not agents or not isinstance(agents, dict):
    st.error("⚠️ Invalid agents configuration")
    st.stop()

# Build persona data structures with TRANSPARENT backgrounds
persona_by_level = {}
backgrounds = {}
persona_options = {}
persona_avatars = {}
persona_unlock_levels = {
    'Nova': 1,
    'Spider-Gwen': 1,
    'Yoda': 1,
    'Elsa': 1,
    'Batman': 11,
    'Wednesday Addams': 11,
    'Shuri': 21,
    'Iron Man': 21,
    'Katniss Everdeen': 21
}

for name, data in agents.items():
    if not isinstance(data, dict):
        continue
    
    unlock_level = persona_unlock_levels.get(name, 1)
    level_tier = 1 if unlock_level == 1 else (3 if unlock_level == 11 else 5)
    
    persona_by_level.setdefault(level_tier, []).append(name)
    
    # Make backgrounds TRANSPARENT (rgba with 0.85 opacity)
    bg = data.get('background', "linear-gradient(135deg, #667eea 0%, #764ba2 100%)")
    if 'rgb(' in bg:
        bg = bg.replace('rgb(', 'rgba(').replace(')', ', 0.85)')
    elif '#' in bg and 'gradient' in bg:
        # Convert hex gradients to rgba
        bg = bg.replace('linear-gradient', 'linear-gradient')
        # Add transparency overlay
        bg = f"linear-gradient(rgba(0,0,0,0.15), rgba(0,0,0,0.15)), {bg}"
    
    backgrounds[name] = bg
    persona_options[name] = f"{data.get('role', name)} — {data.get('goal', '')}"
    persona_avatars[name] = data.get('avatar', "🧠")

historical_df = load_historical_ratings()

# Get user progress
progress = st.session_state.user_progress
user_level = progress['level']
user_xp = progress['xp']
user_streak = progress['streak']
user_affinity = progress.get('affinity', {})

# Calculate XP progress
current_level_xp = get_xp_for_level(user_level - 1) if user_level > 1 else 0
next_level_xp = get_xp_for_level(user_level)
xp_progress = ((user_xp - current_level_xp) / (next_level_xp - current_level_xp)) * 100
xp_progress = max(0, min(100, xp_progress))

tier = get_level_tier(user_level)

# ==========================
# REWARD POPUP
# ==========================
if st.session_state.show_reward:
    reward = st.session_state.show_reward
    
    if reward['type'] == 'level_up':
        st.markdown(f"""
        <div class='reward-popup'>
            <div style='font-size: 80px;'>🎉</div>
            <h1 style='color: white; margin: 20px 0;'>Level Up!</h1>
            <h2 style='color: white;'>You're now Level {reward['level']}!</h2>
            <p style='color: white; margin-top: 20px;'>Keep learning to unlock more tutors!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Awesome!", key="close_reward"):
            st.session_state.show_reward = None
            st.rerun()
    
    elif reward['type'] == 'streak':
        st.markdown(f"""
        <div class='reward-popup'>
            <div style='font-size: 80px;'>🔥</div>
            <h1 style='color: white; margin: 20px 0;'>Streak Milestone!</h1>
            <h2 style='color: white;'>{reward['days']} Days Strong!</h2>
            <p style='color: white; margin-top: 20px;'>+20 Bonus XP!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Keep Going!", key="close_streak"):
            st.session_state.show_reward = None
            st.rerun()

# ==========================
# HEADER WITH XP BAR
# ==========================
st.markdown(f"""
<div class='level-card'>
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>
        <div style='display: flex; align-items: center; gap: 20px;'>
            <div style='font-size: 60px;'>{tier['icon']}</div>
            <div>
                <h1 style='color: white; margin: 0;'>Level {user_level} {tier['name']}</h1>
                <p style='color: rgba(255,255,255,0.8); margin: 0;'>Java Programming Tutor</p>
            </div>
        </div>
        <div style='display: flex; gap: 30px; align-items: center;'>
            <div style='text-align: center;'>
                <div class='streak-badge'>
                    🔥 {user_streak}
                </div>
                <p style='color: rgba(255,255,255,0.8); margin-top: 5px; font-size: 12px;'>day streak</p>
            </div>
            <div style='text-align: right;'>
                <p style='color: rgba(255,255,255,0.8); margin: 0; font-size: 14px;'>XP Progress</p>
                <p style='color: white; margin: 0; font-size: 24px; font-weight: bold;'>{user_xp} / {next_level_xp}</p>
            </div>
        </div>
    </div>
    <div class='xp-bar'>
        <div class='xp-fill' style='width: {xp_progress}%;'></div>
        <div class='xp-text'>{int(xp_progress)}%</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================
# SIDEBAR
# ==========================
with st.sidebar:
    st.title("⚙️ Control Center")
    
    st.header("📊 Your Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Level", user_level)
        st.metric("Streak", f"{user_streak} 🔥")
    with col2:
        st.metric("XP", user_xp)
        unlocked_count = sum(1 for p in persona_unlock_levels if persona_unlock_levels[p] <= user_level)
        st.metric("Tutors", f"{unlocked_count}/{len(persona_unlock_levels)}")
    
    st.divider()
    
    # Analytics toggle
    if st.button("📊 Analytics Dashboard", 
                 type="primary" if st.session_state.show_analytics else "secondary",
                 use_container_width=True):
        st.session_state.show_analytics = not st.session_state.show_analytics
        st.rerun()
    
    st.divider()
    
    # Unlock progress
    st.header("🔓 Unlock Progress")
    next_unlock = None
    for persona, level in sorted(persona_unlock_levels.items(), key=lambda x: x[1]):
        if level > user_level:
            next_unlock = (persona, level)
            break
    
    if next_unlock:
        levels_needed = next_unlock[1] - user_level
        st.info(f"**Next unlock:** {persona_avatars.get(next_unlock[0], '🧠')} {next_unlock[0]}")
        st.caption(f"Reach level {next_unlock[1]} ({levels_needed} levels to go!)")
    else:
        st.success("🎉 All tutors unlocked!")
    
    st.divider()
    
    # Quick stats from history
    if not historical_df.empty:
        st.header("📈 All-Time Stats")
        avg_rating = historical_df['clarity'].mean() if 'clarity' in historical_df.columns else 0
        st.metric("Avg Clarity", f"{avg_rating:.1f}⭐")
        st.metric("Total Questions", len(historical_df))

# ==========================
# MAIN CONTENT
# ==========================

if st.session_state.show_analytics:
    # [Keep existing analytics dashboard code - it's already good]
    st.header("📊 Analytics Dashboard")
    
    if not historical_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_clarity = historical_df['clarity'].mean()
            st.metric("📊 Avg Clarity", f"{avg_clarity:.2f}⭐")
        
        with col2:
            total = len(historical_df)
            st.metric("📝 Total Ratings", total)
        
        with col3:
            if 'persona' in historical_df.columns:
                best = historical_df.groupby('persona')['clarity'].mean().idxmax()
                st.metric("🏆 Top Persona", best[:12])
        
        with col4:
            if 'helpfulness' in historical_df.columns:
                avg_help = historical_df['helpfulness'].mean()
                st.metric("💡 Helpfulness", f"{avg_help:.2f}⭐")
        
        # Add more analytics as needed...
    else:
        st.info("📊 No ratings data yet. Start asking questions!")

else:
    # ==========================
    # MAIN TUTOR INTERFACE
    # ==========================
    
    # Filter personas by unlock level
    available_personas = [p for p, lvl in persona_unlock_levels.items() if lvl <= user_level]
    
    if not available_personas:
        st.error("⚠️ No personas available")
        st.stop()
    
    # Persona selection
    st.subheader("🎯 Choose Your Tutor")
    
    # Display personas in a grid
    cols_per_row = 3
    persona_list = list(persona_unlock_levels.keys())
    
    for i in range(0, len(persona_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(persona_list):
                persona_name = persona_list[i + j]
                unlock_level = persona_unlock_levels[persona_name]
                is_unlocked = unlock_level <= user_level
                affinity = user_affinity.get(persona_name, 0)
                affinity_stars = min(5, affinity // 25)
                
                with col:
                    if is_unlocked:
                        if st.button(
                            f"{persona_avatars[persona_name]} {persona_name}",
                            key=f"persona_{persona_name}",
                            use_container_width=True,
                            type="primary" if st.session_state.current_persona == persona_name else "secondary"
                        ):
                            st.session_state.current_persona = persona_name
                            st.rerun()
                        
                        # Show affinity
                        if affinity > 0:
                            st.markdown(f"""
                            <div style='text-align: center;'>
                                <small>{'⭐' * affinity_stars}{'☆' * (5 - affinity_stars)}</small>
                                <div class='affinity-bar'>
                                    <div class='affinity-fill' style='width: {(affinity % 25) * 4}%;'></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class='persona-card locked-persona' style='text-align: center; padding: 15px;'>
                            <div style='font-size: 40px;'>{persona_avatars[persona_name]}</div>
                            <div>🔒 Level {unlock_level}</div>
                            <small>{persona_name}</small>
                        </div>
                        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Selected persona display
    if st.session_state.current_persona:
        selected_persona = st.session_state.current_persona
        selected_background = backgrounds.get(selected_persona, "rgba(102, 126, 234, 0.85)")
        
        # Apply background
        st.markdown(f"""
            <style>
                .stApp {{
                    background: {selected_background};
                    background-attachment: fixed;
                }}
            </style>
        """, unsafe_allow_html=True)
        
        # Persona card
        st.markdown(f"""
        <div class='persona-card' style='background: {selected_background};'>
            <h2 style='color: white;'>{persona_avatars[selected_persona]} {selected_persona}</h2>
            <p style='color: rgba(255,255,255,0.9);'>{persona_options[selected_persona]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Question input
        st.subheader("💬 Ask Your Java Question")
        user_question = st.text_area(
            "Enter your programming question:",
            height=150,
            placeholder="e.g., How do I implement a LinkedList in Java?",
            key="question_input"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            ask_button = st.button("🚀 Get Explanation (+10 XP)", type="primary", use_container_width=True)
        
        with col2:
            if st.session_state.explanation:
                if st.button("🗑️ Clear", use_container_width=True):
                    st.session_state.explanation = None
                    st.session_state.show_rating = False
                    st.rerun()
        
        # Process question
        if ask_button:
            if not user_question.strip():
                st.warning("⚠️ Please enter a question first!")
            else:
                try:
                    with st.spinner(f"{persona_avatars[selected_persona]} Thinking..."):
                        result = create_crew(selected_persona, user_question)
                    
                    # Save explanation
                    st.session_state.explanation = result
                    st.session_state.current_question = user_question
                    st.session_state.show_rating = True
                    
                    # Award XP and affinity
                    add_xp(10)
                    add_affinity(selected_persona, 10)
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    with st.expander("Show detailed error"):
                        st.code(traceback.format_exc())
        
        # Display explanation
        if st.session_state.explanation:
            st.divider()
            st.markdown("### 🗣️ Explanation")
            st.markdown(f"""
            <div class='explanation-box'>
                {st.session_state.explanation}
            </div>
            """, unsafe_allow_html=True)
            
            # Rating section
            if st.session_state.show_rating:
                st.divider()
                st.subheader("⭐ Rate This Explanation (+5 XP)")
                
                with st.form("rating_form"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        clarity = st.slider("🔍 Clarity", 1, 5, 3)
                    with col2:
                        accuracy = st.slider("✅ Accuracy", 1, 5, 3)
                    with col3:
                        helpfulness = st.slider("💡 Helpfulness", 1, 5, 3)
                    
                    feedback = st.text_area("Additional comments (optional):", height=80)
                    
                    submit_rating = st.form_submit_button("📊 Submit Rating", type="primary", use_container_width=True)
                    
                    if submit_rating:
                        rating_data = {
                            'timestamp': datetime.now().isoformat(),
                            'persona': selected_persona,
                            'question': st.session_state.current_question[:200],
                            'user_level': user_level,
                            'clarity': clarity,
                            'accuracy': accuracy,
                            'helpfulness': helpfulness,
                            'feedback': feedback
                        }
                        
                        if save_rating(rating_data):
                            st.success("✅ Rating submitted! +5 XP!")
                            
                            # Award XP
                            add_xp(5)
                            
                            # Bonus affinity for high ratings
                            avg_rating = (clarity + accuracy + helpfulness) / 3
                            if avg_rating >= 4:
                                add_affinity(selected_persona, 5)
                                st.success(f"🌟 High rating! +5 affinity with {selected_persona}")
                            
                            st.session_state.show_rating = False
                            load_historical_ratings.clear()
                            st.rerun()
                        else:
                            st.error("❌ Failed to save rating.")
    
    else:
        st.info("👆 Select a tutor to get started!")

# Footer
st.divider()
st.caption(f"🧠 AI Java Tutor Pro | Level {user_level} • {user_streak} day streak 🔥")
