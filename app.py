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

# 📁 Setup paths
base_dir = os.path.dirname(__file__)
sys.path.insert(0, base_dir)

# Page config
st.set_page_config(page_title="AI Tutor Pro", page_icon="🧠", layout="wide")

# Custom CSS
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
    .persona-card {
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        transition: transform 0.3s;
    }
    .persona-card:hover {
        transform: scale(1.02);
    }
    .rating-container {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        margin: 20px 0;
    }
    .alert-box {
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 5px solid;
        animation: slideIn 0.5s;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    .explanation-box {
        background-color: #e6f7ff;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1890ff;
        margin: 15px 0;
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
    """Save rating to file"""
    filepath = os.path.join(base_dir, "ratings.json")
    try:
        with open(filepath, "a") as f:
            f.write(json.dumps(rating_data) + "\n")
        return True
    except Exception as e:
        st.error(f"Error saving rating: {e}")
        return False

# Initialize session state
def init_session_state():
    if 'level' not in st.session_state:
        st.session_state.level = 5
    if 'explanation' not in st.session_state:
        st.session_state.explanation = None
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""
    if 'current_persona' not in st.session_state:
        st.session_state.current_persona = None
    if 'show_analytics' not in st.session_state:
        st.session_state.show_analytics = False
    if 'favorite_personas' not in st.session_state:
        st.session_state.favorite_personas = set()
    if 'session_stats' not in st.session_state:
        st.session_state.session_stats = {
            'questions_asked': 0,
            'personas_used': set(),
            'start_time': datetime.now(),
            'clarifications': 0
        }
    if 'show_rating' not in st.session_state:
        st.session_state.show_rating = False

init_session_state()

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

# Build persona data structures
persona_by_level = {}
backgrounds = {}
persona_options = {}
persona_avatars = {}

# Debug: Show what we're loading
st.sidebar.write("🔍 Debug: Loading personas...")

for name, data in agents.items():
    if not isinstance(data, dict):
        st.sidebar.warning(f"⚠️ Skipping {name}: not a dict")
        continue
    
    level = data.get('level', 'beginner')
    level_num = {
        "beginner": 1,
        "intermediate": 3,
        "advanced": 5
    }.get(level.lower() if isinstance(level, str) else level, 1)
    
    persona_by_level.setdefault(level_num, []).append(name)
    backgrounds[name] = data.get('background', "linear-gradient(135deg, #667eea 0%, #764ba2 100%)")
    persona_options[name] = f"{data.get('role', name)} — {data.get('goal', '')}"
    persona_avatars[name] = data.get('avatar', "🧠")
    
    st.sidebar.caption(f"✓ {name} (lvl {level_num}): {persona_avatars[name]}")

# Show what we have
st.sidebar.write(f"📊 Total personas loaded: {sum(len(v) for v in persona_by_level.values())}")
st.sidebar.write(f"📊 By level: {dict(persona_by_level)}")

# Load historical data
historical_df = load_historical_ratings()

# ==========================
# HEADER
# ==========================
st.markdown("""
<div class='main-header'>
    <h1>🧠 AI Coding Tutor Pro</h1>
    <p>Personalized programming explanations with intelligent analytics</p>
</div>
""", unsafe_allow_html=True)

# ==========================
# SIDEBAR
# ==========================
with st.sidebar:
    st.title("⚙️ Control Center")
    
    # User level
    st.header("👤 Your Profile")
    user_level = st.slider("Skill Level", 1, 5, st.session_state.level,
                           help="1=Beginner, 3=Intermediate, 5=Expert")
    st.session_state.level = user_level
    
    level_labels = {
        1: "🌱 Beginner", 
        2: "📚 Learning", 
        3: "💪 Intermediate",
        4: "🚀 Advanced", 
        5: "🏆 Expert"
    }
    st.caption(f"Current: {level_labels[user_level]}")
    
    st.divider()
    
    # Analytics toggle
    if st.button("📊 Analytics Dashboard", 
                 type="primary" if st.session_state.show_analytics else "secondary",
                 use_container_width=True):
        st.session_state.show_analytics = not st.session_state.show_analytics
        st.rerun()
    
    st.divider()
    
    # Session stats
    st.header("📊 Session Stats")
    session = st.session_state.session_stats
    duration = datetime.now() - session['start_time']
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Questions", session['questions_asked'])
        st.metric("Duration", f"{duration.seconds // 60}m")
    with col2:
        st.metric("Personas", len(session['personas_used']))
        st.metric("Clarified", session['clarifications'])
    
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.session_stats = {
            'questions_asked': 0,
            'personas_used': set(),
            'start_time': datetime.now(),
            'clarifications': 0
        }
        st.rerun()
    
    st.divider()
    
    # Quick stats from history
    if not historical_df.empty:
        st.header("📈 All-Time Stats")
        avg_rating = historical_df['clarity'].mean() if 'clarity' in historical_df.columns else 0
        st.metric("Avg Clarity", f"{avg_rating:.1f}⭐")
        st.metric("Total Ratings", len(historical_df))

# ==========================
# MAIN CONTENT
# ==========================

if st.session_state.show_analytics:
    # ==========================
    # ANALYTICS DASHBOARD
    # ==========================
    st.header("📊 Analytics Dashboard")
    
    if not historical_df.empty:
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_clarity = historical_df['clarity'].mean()
            st.metric("📊 Avg Clarity", f"{avg_clarity:.2f}⭐",
                     delta=f"{avg_clarity - 3:.1f}")
        
        with col2:
            total = len(historical_df)
            recent = len(historical_df[historical_df['timestamp'] > 
                        (datetime.now() - timedelta(days=7)).isoformat()])
            st.metric("📝 Total Ratings", total, delta=f"{recent} this week")
        
        with col3:
            if 'persona' in historical_df.columns:
                best = historical_df.groupby('persona')['clarity'].mean().idxmax()
                st.metric("🏆 Top Persona", best[:12])
        
        with col4:
            if 'helpfulness' in historical_df.columns:
                avg_help = historical_df['helpfulness'].mean()
                st.metric("💡 Helpfulness", f"{avg_help:.2f}⭐")
        
        st.divider()
        
        # Tabs
        tabs = st.tabs([
            "📈 Overview",
            "👥 Personas", 
            "🎯 Patterns",
            "⚠️ Quality"
        ])
        
        with tabs[0]:  # OVERVIEW
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🌡️ Quality Meter")
                recent_clarity = historical_df.tail(20)['clarity'].mean()
                
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=recent_clarity,
                    title={'text': "Recent Quality", 'font': {'size': 20}},
                    delta={'reference': 3.5},
                    gauge={
                        'axis': {'range': [None, 5]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 2.5], 'color': '#f5576c'},
                            {'range': [2.5, 3.5], 'color': '#ffd93d'},
                            {'range': [3.5, 5], 'color': '#43e97b'}
                        ]
                    }
                ))
                fig_gauge.update_layout(height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)
            
            with col2:
                st.subheader("📊 Rating Distribution")
                fig_dist = px.histogram(
                    historical_df,
                    x='clarity',
                    nbins=5,
                    color_discrete_sequence=['#667eea']
                )
                fig_dist.update_layout(height=300)
                st.plotly_chart(fig_dist, use_container_width=True)
            
            st.subheader("📈 Ratings Over Time")
            historical_df['date'] = pd.to_datetime(historical_df['timestamp']).dt.date
            daily = historical_df.groupby('date')['clarity'].mean().reset_index()
            
            fig_trend = px.line(daily, x='date', y='clarity', markers=True)
            fig_trend.add_hline(y=3.5, line_dash="dash", annotation_text="Target")
            st.plotly_chart(fig_trend, use_container_width=True)
            
            st.subheader("🎯 Quality Dimensions")
            if all(col in historical_df.columns for col in ['clarity', 'accuracy', 'helpfulness']):
                dims = historical_df[['clarity', 'accuracy', 'helpfulness']].mean()
                
                fig_radar = go.Figure(data=go.Scatterpolar(
                    r=dims.values,
                    theta=['Clarity', 'Accuracy', 'Helpfulness'],
                    fill='toself'
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 5]))
                )
                st.plotly_chart(fig_radar, use_container_width=True)
        
        with tabs[1]:  # PERSONAS
            st.subheader("🏆 Persona Performance")
            
            if 'persona' in historical_df.columns:
                persona_stats = historical_df.groupby('persona').agg({
                    'clarity': ['mean', 'count'],
                    'accuracy': 'mean',
                    'helpfulness': 'mean'
                }).round(2)
                
                persona_stats.columns = ['Clarity', 'Uses', 'Accuracy', 'Helpfulness']
                persona_stats = persona_stats.sort_values('Clarity', ascending=False).reset_index()
                
                st.dataframe(persona_stats, use_container_width=True, hide_index=True)
                
                fig_personas = px.bar(
                    persona_stats.head(10),
                    x='Clarity',
                    y='persona',
                    orientation='h',
                    color='Clarity',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig_personas, use_container_width=True)
        
        with tabs[2]:  # PATTERNS
            st.subheader("🔍 Success Patterns")
            
            if all(col in historical_df.columns for col in ['clarity', 'accuracy', 'helpfulness']):
                corr = historical_df[['clarity', 'accuracy', 'helpfulness']].corr()
                
                fig_corr = px.imshow(
                    corr,
                    text_auto='.2f',
                    color_continuous_scale='RdBu_r'
                )
                st.plotly_chart(fig_corr, use_container_width=True)
            
            if 'user_level' in historical_df.columns:
                level_perf = historical_df.groupby('user_level')['clarity'].mean().reset_index()
                fig_level = px.line(level_perf, x='user_level', y='clarity', markers=True)
                st.plotly_chart(fig_level, use_container_width=True)
        
        with tabs[3]:  # QUALITY
            st.subheader("⚠️ Quality Issues")
            
            low_ratings = historical_df[historical_df['clarity'] <= 2]
            
            if not low_ratings.empty:
                st.warning(f"⚠️ {len(low_ratings)} low clarity ratings")
                
                for _, row in low_ratings.tail(5).iterrows():
                    feedback_text = f"<br><em>{row['feedback']}</em>" if row.get('feedback') else ""
                    st.markdown(f"""
                    <div class='alert-box' style='border-left-color: #f5576c; background: #fff5f5;'>
                        <strong>🚨 {row.get('persona', 'Unknown')}</strong><br>
                        Clarity: {'⭐' * int(row['clarity'])}<br>
                        <small>{row['timestamp'][:16]}</small>
                        {feedback_text}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No quality issues found!")
        
        st.divider()
        
        # Export
        st.subheader("📥 Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = historical_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📄 Download All Ratings",
                data=csv,
                file_name=f"ratings_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            if 'feedback' in historical_df.columns:
                feedback_df = historical_df[historical_df['feedback'].notna()]
                if not feedback_df.empty:
                    csv_feedback = feedback_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "💬 Download Feedback",
                        data=csv_feedback,
                        file_name=f"feedback_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
    
    else:
        st.info("📊 No ratings data yet. Start asking questions and rating explanations!")

else:
    # ==========================
    # MAIN TUTOR INTERFACE
    # ==========================
    
    # Filter personas by level
    available_personas = []
    for lvl in range(1, st.session_state.level + 1):
        available_personas.extend(persona_by_level.get(lvl, []))
    
    # If no personas available at current level, show all
    if not available_personas:
        for personas_list in persona_by_level.values():
            available_personas.extend(personas_list)
    
    if not available_personas:
        st.error("⚠️ No personas available")
        st.stop()
    
    # Persona selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Choose Your Tutor")
        selected_persona = st.selectbox(
            "Select Persona:",
            options=available_personas,
            format_func=lambda x: f"{persona_avatars[x]} {x}",
            key="persona_selector"
        )
    
    with col2:
        st.subheader("⭐ Actions")
        is_fav = selected_persona in st.session_state.favorite_personas
        
        if st.button(
            f"{'💔 Unfavorite' if is_fav else '💖 Favorite'}",
            use_container_width=True
        ):
            if is_fav:
                st.session_state.favorite_personas.remove(selected_persona)
            else:
                st.session_state.favorite_personas.add(selected_persona)
            st.rerun()
        
        if st.session_state.favorite_personas:
            st.caption("❤️ " + ", ".join([
                persona_avatars[p] for p in st.session_state.favorite_personas
            ]))
    
    # Apply background
    selected_background = backgrounds.get(selected_persona, "#ffffff")
    st.markdown(f"""
        <style>
            .stApp {{
                background: {selected_background};
                background-attachment: fixed;
            }}
            /* Ensure text is readable on all backgrounds */
            .stMarkdown, .stText, p, span, div {{
                text-shadow: 0 0 10px rgba(255,255,255,0.8), 0 0 20px rgba(255,255,255,0.6);
            }}
            /* Make sure form elements are visible */
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div,
            .stSlider > div > div {{
                background-color: rgba(255, 255, 255, 0.95) !important;
                backdrop-filter: blur(10px);
            }}
            /* Ensure buttons are visible */
            .stButton > button {{
                background-color: rgba(255, 255, 255, 0.9) !important;
                color: #333 !important;
                border: 2px solid rgba(0,0,0,0.1) !important;
            }}
            .stButton > button[kind="primary"] {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: white !important;
                border: none !important;
            }}
            /* Sidebar stays readable */
            section[data-testid="stSidebar"] {{
                background-color: rgba(255, 255, 255, 0.95) !important;
                backdrop-filter: blur(10px);
            }}
        </style>
    """, unsafe_allow_html=True)
    
    # Persona card
    st.markdown(f"""
    <div class='persona-card' style='background: {selected_background}; border: 2px solid rgba(255,255,255,0.3); box-shadow: 0 4px 20px rgba(0,0,0,0.3);'>
        <h2 style='text-shadow: 2px 2px 4px rgba(0,0,0,0.8), 0 0 10px rgba(255,255,255,0.5);'>{persona_avatars[selected_persona]} {selected_persona}</h2>
        <p style='text-shadow: 1px 1px 3px rgba(0,0,0,0.8), 0 0 8px rgba(255,255,255,0.5);'>{persona_options[selected_persona]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show persona stats if available
    if not historical_df.empty and 'persona' in historical_df.columns:
        persona_history = historical_df[historical_df['persona'] == selected_persona]
        if not persona_history.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Times Used", len(persona_history))
            with col2:
                st.metric("Avg Clarity", f"{persona_history['clarity'].mean():.1f}⭐")
            with col3:
                if 'helpfulness' in persona_history.columns:
                    st.metric("Avg Helpful", f"{persona_history['helpfulness'].mean():.1f}⭐")
    
    st.divider()
    
    # Question input
    st.subheader("💬 Ask Your Question")
    user_question = st.text_area(
        "Enter your programming question:",
        height=150,
        placeholder="e.g., How do I implement a binary search tree in Python?",
        key="question_input"
    )
    
    # Code detection
    has_code = user_question and any(x in user_question for x in [
        "def ", "class ", "{", "}", "()", "if ", "for ", "while ", "import "
    ])
    
    if has_code:
        st.info("🧑‍💻 Code detected! Your tutor will provide hands-on examples.")
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        ask_button = st.button("🚀 Get Explanation", type="primary", use_container_width=True)
    
    with col2:
        if st.session_state.explanation:
            if st.button("❓ Need Clarification", use_container_width=True):
                st.session_state.session_stats['clarifications'] += 1
                st.warning("🤔 Requesting simpler explanation...")
                # Could trigger a follow-up with the AI
    
    with col3:
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
                
                # Update session stats
                st.session_state.session_stats['questions_asked'] += 1
                st.session_state.session_stats['personas_used'].add(selected_persona)
                
                # Save explanation
                st.session_state.explanation = result
                st.session_state.current_question = user_question
                st.session_state.current_persona = selected_persona
                st.session_state.show_rating = True
                
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
            st.markdown("<div class='rating-container'>", unsafe_allow_html=True)
            st.subheader("⭐ Rate This Explanation")
            st.caption("Your feedback helps improve our AI tutors!")
            
            with st.form("rating_form"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    clarity = st.slider(
                        "🔍 Clarity", 1, 5, 3,
                        help="Was the explanation clear and easy to understand?"
                    )
                    accuracy = st.slider(
                        "✅ Accuracy", 1, 5, 3,
                        help="Was the information correct?"
                    )
                    helpfulness = st.slider(
                        "💡 Helpfulness", 1, 5, 3,
                        help="Did this help you solve your problem?"
                    )
                    
                    feedback = st.text_area(
                        "Additional comments (optional):",
                        height=100,
                        placeholder="What worked well? What could be better?"
                    )
                    
                    was_confused = st.checkbox(
                        "😕 I needed clarification",
                        help="Check if the explanation wasn't clear enough"
                    )
                
                with col2:
                    st.write("**Quick Stats:**")
                    avg_score = np.mean([clarity, accuracy, helpfulness])
                    st.metric("Average Score", f"{avg_score:.1f}/5.0")
                    
                    if avg_score >= 4:
                        st.success("🎉 Great!")
                    elif avg_score >= 3:
                        st.info("👍 Good")
                    else:
                        st.warning("😔 Needs work")
                
                submit_rating = st.form_submit_button(
                    "📊 Submit Rating",
                    type="primary",
                    use_container_width=True
                )
                
                if submit_rating:
                    rating_data = {
                        'timestamp': datetime.now().isoformat(),
                        'persona': st.session_state.current_persona,
                        'question': st.session_state.current_question[:200],
                        'has_code': has_code,
                        'user_level': st.session_state.level,
                        'clarity': clarity,
                        'accuracy': accuracy,
                        'helpfulness': helpfulness,
                        'feedback': feedback,
                        'confused': was_confused
                    }
                    
                    if save_rating(rating_data):
                        st.success("✅ Rating submitted! Thank you!")
                        st.balloons()
                        st.session_state.show_rating = False
                        
                        # Reload cache
                        load_historical_ratings.clear()
                        
                        # Show next steps
                        st.info("💡 Tip: Check the Analytics Dashboard to see trends!")
                    else:
                        st.error("❌ Failed to save rating. Please try again.")
            
            st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.caption(f"🧠 AI Tutor Pro | Session: {st.session_state.session_stats['questions_asked']} questions")

with col2:
    if not historical_df.empty:
        st.caption(f"📊 All-time: {len(historical_df)} ratings")

with col3:
    st.caption("💡 Made with Streamlit + CrewAI")
