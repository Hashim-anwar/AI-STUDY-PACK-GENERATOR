import streamlit as st
from workflow import run_study_workflow


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="🎓",
    layout="wide",
)


# ============================================================
# HEADER
# ============================================================

st.title("🎓 AI Study Pack Generator")

st.markdown(
    """
Create a personalized study pack using a multi-stage AI workflow.

**Planning → Content Generation → Assessment → Review → Refinement**
"""
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Study Settings")

    subject = st.text_input(
        "📘 Subject",
        placeholder="Example: Biology",
    )

    topic = st.text_input(
        "📖 Topic",
        placeholder="Example: Photosynthesis",
    )

    level = st.selectbox(
        "🎓 Student Level",
        [
            "Primary School",
            "Middle School",
            "High School",
            "College",
            "Professional",
        ],
    )

    language = st.selectbox(
        "🌐 Language",
        [
            "English",
            "Arabic",
            "Urdu",
        ],
    )

    difficulty = st.selectbox(
        "📊 Difficulty",
        [
            "Easy",
            "Medium",
            "Hard",
            "Mixed",
        ],
        index=1,
    )

    goals = st.text_area(
        "🎯 Learning Goals",
        placeholder=(
            "Example:\n"
            "Understand the topic, remember key concepts, "
            "and prepare for an exam."
        ),
        height=120,
    )

    generate_button = st.button(
        "🚀 Generate Study Pack",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# WORKFLOW EXECUTION
# ============================================================

if generate_button:

    if not subject.strip():
        st.warning("Please enter a subject.")
        st.stop()

    if not topic.strip():
        st.warning("Please enter a topic.")
        st.stop()

    try:

        # ----------------------------------------------------
        # WORKFLOW STATUS
        # ----------------------------------------------------

        with st.status(
            "Running AI Study Workflow...",
            expanded=True,
        ) as status:

            st.write(
                "🧠 Stage 1: Planning personalized learning strategy..."
            )

            st.write(
                "📚 Stage 2: Generating study content..."
            )

            st.write(
                "📝 Stage 3: Creating assessment..."
            )

            st.write(
                "🔎 Stage 4: Reviewing content and assessment..."
            )

            st.write(
                "✨ Stage 5: Refining material when required..."
            )

            # ------------------------------------------------
            # RUN WORKFLOW
            # ------------------------------------------------

            result = run_study_workflow(

                subject=subject,

                topic=topic,

                level=level,

                language=language,

                difficulty=difficulty,

                goals=goals,

            )

            status.update(

                label="✅ Study Pack Generated Successfully",

                state="complete",

                expanded=False,

            )


        # ====================================================
        # FINAL STUDY PACK
        # ====================================================

        st.markdown(
            result["final_pack"]
        )


        # ====================================================
        # DOWNLOAD STUDY PACK
        # ====================================================

        st.download_button(

            label="⬇️ Download Study Pack",

            data=result["final_pack"],

            file_name="AI_Study_Pack.md",

            mime="text/markdown",

            use_container_width=True,

        )


        # ====================================================
        # WORKFLOW TRACE
        # ====================================================

        with st.expander(
            "🔬 View AI Workflow Details"
        ):

            st.json(
                result["trace"]
            )


    except Exception as error:

        st.error(
            f"❌ Workflow Error: "
            f"{type(error).__name__}: {error}"
        )

        st.info(
            """
Please check:

1. GROQ_API_KEY is correctly configured.
2. requirements.txt is installed.
3. The Groq model is available.
4. Your Groq API quota/rate limit is available.
"""
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI-generated educational content should be reviewed "
    "before use in high-stakes examinations or specialized subjects."
)