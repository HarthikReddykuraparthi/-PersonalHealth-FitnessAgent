import time
import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.groq import Groq

st.set_page_config(
    page_title="AI Health & Fitness Planner",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0fff4;
        border: 1px solid #9ae6b4;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fffaf0;
        border: 1px solid #fbd38d;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)


def display_dietary_plan(plan_content):
    with st.expander("📋 Your Personalized Dietary Plan", expanded=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 🎯 Why this plan works")
            st.info(plan_content.get("why_this_plan_works", "Information not available"))
            st.markdown("### 🍽️ Meal Plan")
            st.write(plan_content.get("meal_plan", "Plan not available"))

        with col2:
            st.markdown("### ⚠️ Important Considerations")
            considerations = plan_content.get("important_considerations", "").split('\n')
            for consideration in considerations:
                if consideration.strip():
                    st.warning(consideration)


def display_fitness_plan(plan_content):
    with st.expander("💪 Your Personalized Fitness Plan", expanded=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 🎯 Goals")
            st.success(plan_content.get("goals", "Goals not specified"))
            st.markdown("### 🏋️‍♂️ Exercise Routine")
            st.write(plan_content.get("routine", "Routine not available"))

        with col2:
            st.markdown("### 💡 Pro Tips")
            tips = plan_content.get("tips", "").split('\n')
            for tip in tips:
                if tip.strip():
                    st.info(tip)


def main():
    if 'dietary_plan' not in st.session_state:
        st.session_state.dietary_plan = {}
        st.session_state.fitness_plan = {}
        st.session_state.qa_pairs = []
        st.session_state.plans_generated = False

    st.title("🏋️‍♂️ AI Health & Fitness Planner")
    st.markdown("""
        <div style='background-color: #00008B; padding: 1rem; border-radius: 0.5rem; margin-bottom: 2rem;'>
        Get personalized dietary and fitness plans tailored to your goals and preferences.
        Our AI-powered system considers your unique profile to create the perfect plan for you.
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("🔑 API Configuration")
        groq_api_key = st.text_input(
            "Groq API Key",
            type="password",
            help="Enter your Groq API key to access the service"
        )

        if not groq_api_key:
            st.warning("⚠️ Please enter your Groq API Key to proceed")
            st.markdown("[Get your API key here](https://console.groq.com/keys)")
            return

        st.success("API Key accepted!")

    if groq_api_key:
        FALLBACK_MODELS = [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]

        def get_working_model(api_key):
            """Return the first Groq model that is not rate-limited or unavailable."""
            for model_id in FALLBACK_MODELS:
                try:
                    m = Groq(id=model_id, api_key=api_key)
                    # Quick smoke-test: create a throwaway agent and run a tiny prompt
                    test_agent = Agent(model=m)
                    test_agent.run("hi")
                    return m, model_id
                except Exception as e:
                    err = str(e)
                    if "429" in err or "rate_limit" in err.lower():
                        st.toast(f"⚠️ {model_id} rate limit hit, trying next model…")
                        time.sleep(2)
                        continue
                    elif "404" in err or "model_not_found" in err.lower():
                        st.toast(f"⚠️ {model_id} not available on this API key, trying next…")
                        continue
                    else:
                        raise  # unexpected error – bubble up
            return None, None

        with st.spinner("🔍 Finding an available Groq model for your API key…"):
            groq_model, active_model_id = get_working_model(groq_api_key)

        if groq_model is None:
            st.error(
                "❌ **All Groq models are currently rate-limited or unavailable.**\n\n"
                "**What you can do:**\n"
                "1. ⏰ Wait a moment and try again (rate limits reset quickly on Groq)\n"
                "2. 🆕 Generate a new API key at [console.groq.com/keys](https://console.groq.com/keys)\n"
                "3. 💳 Check your usage limits in the Groq console"
            )
            return

        st.sidebar.success(f"✅ Using model: `{active_model_id}`")

        st.header("👤 Your Profile")

        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input("Age", min_value=10, max_value=100, step=1, help="Enter your age")
            height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, step=0.1)
            activity_level = st.selectbox(
                "Activity Level",
                options=["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
                help="Choose your typical activity level"
            )
            dietary_preferences = st.selectbox(
                "Dietary Preferences",
                options=["Vegetarian", "Keto", "Gluten Free", "Low Carb", "Dairy Free"],
                help="Select your dietary preference"
            )

        with col2:
            weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, step=0.1)
            sex = st.selectbox("Sex", options=["Male", "Female", "Other"])
            fitness_goals = st.selectbox(
                "Fitness Goals",
                options=["Lose Weight", "Gain Muscle", "Endurance", "Stay Fit", "Strength Training"],
                help="What do you want to achieve?"
            )

        if st.button("🎯 Generate My Personalized Plan", use_container_width=True):
            with st.spinner("Creating your perfect health and fitness routine..."):
                try:
                    dietary_agent = Agent(
                        name="Dietary Expert",
                        role="Provides personalized dietary recommendations",
                        model=groq_model,
                        instructions=[
                            "Consider the user's input, including dietary restrictions and preferences.",
                            "Suggest a detailed meal plan for the day, including breakfast, lunch, dinner, and snacks.",
                            "Provide a brief explanation of why the plan is suited to the user's goals.",
                            "Focus on clarity, coherence, and quality of the recommendations.",
                        ]
                    )

                    fitness_agent = Agent(
                        name="Fitness Expert",
                        role="Provides personalized fitness recommendations",
                        model=groq_model,
                        instructions=[
                            "Provide exercises tailored to the user's goals.",
                            "Include warm-up, main workout, and cool-down exercises.",
                            "Explain the benefits of each recommended exercise.",
                            "Ensure the plan is actionable and detailed.",
                        ]
                    )

                    user_profile = f"""
                    Age: {age}
                    Weight: {weight}kg
                    Height: {height}cm
                    Sex: {sex}
                    Activity Level: {activity_level}
                    Dietary Preferences: {dietary_preferences}
                    Fitness Goals: {fitness_goals}
                    """

                    def run_with_retry(agent, prompt, retries=3, wait=20):
                        for attempt in range(retries):
                            try:
                                return agent.run(prompt)
                            except Exception as e:
                                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                                    if attempt < retries - 1:
                                        st.warning(f"⏳ Rate limit hit. Waiting {wait}s before retrying... (attempt {attempt + 1}/{retries})")
                                        time.sleep(wait)
                                    else:
                                        raise
                                else:
                                    raise

                    dietary_plan_response: RunOutput = run_with_retry(dietary_agent, user_profile)
                    dietary_plan = {
                        "why_this_plan_works": "High Protein, Healthy Fats, Moderate Carbohydrates, and Caloric Balance",
                        "meal_plan": dietary_plan_response.content,
                        "important_considerations": """
                        - Hydration: Drink plenty of water throughout the day
                        - Electrolytes: Monitor sodium, potassium, and magnesium levels
                        - Fiber: Ensure adequate intake through vegetables and fruits
                        - Listen to your body: Adjust portion sizes as needed
                        """
                    }

                    time.sleep(5)  # avoid per-minute rate limit between calls

                    fitness_plan_response: RunOutput = run_with_retry(fitness_agent, user_profile)
                    fitness_plan = {
                        "goals": "Build strength, improve endurance, and maintain overall fitness",
                        "routine": fitness_plan_response.content,
                        "tips": """
                        - Track your progress regularly
                        - Allow proper rest between workouts
                        - Focus on proper form
                        - Stay consistent with your routine
                        """
                    }

                    st.session_state.dietary_plan = dietary_plan
                    st.session_state.fitness_plan = fitness_plan
                    st.session_state.plans_generated = True
                    st.session_state.qa_pairs = []

                    display_dietary_plan(dietary_plan)
                    display_fitness_plan(fitness_plan)

                except Exception as e:
                    st.error(f"❌ An error occurred: {e}")

        if st.session_state.plans_generated:
            st.header("❓ Questions about your plan?")
            question_input = st.text_input("What would you like to know?")

            if st.button("Get Answer"):
                if question_input:
                    with st.spinner("Finding the best answer for you..."):
                        dietary_plan = st.session_state.dietary_plan
                        fitness_plan = st.session_state.fitness_plan

                        context = f"Dietary Plan: {dietary_plan.get('meal_plan', '')}\n\nFitness Plan: {fitness_plan.get('routine', '')}"
                        full_context = f"{context}\nUser Question: {question_input}"

                        try:
                            agent = Agent(model=groq_model, debug_mode=True, markdown=True)
                            run_response: RunOutput = agent.run(full_context)

                            if hasattr(run_response, 'content'):
                                answer = run_response.content
                            else:
                                answer = "Sorry, I couldn't generate a response at this time."

                            st.session_state.qa_pairs.append((question_input, answer))
                        except Exception as e:
                            st.error(f"❌ An error occurred while getting the answer: {e}")

            if st.session_state.qa_pairs:
                st.header("💬 Q&A History")
                for question, answer in st.session_state.qa_pairs:
                    st.markdown(f"**Q:** {question}")
                    st.markdown(f"**A:** {answer}")


if __name__ == "__main__":
    main()