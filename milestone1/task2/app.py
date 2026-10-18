# ============================================================
# AI-BASED EXAMINATION PLATFORM
# Task 2: MCQ Generator Web Application
# ============================================================

import streamlit as st

from mcq_generator import generate_mcqs

# ============================================================
# 1. CONFIGURE THE PAGE
# Set the browser tab title and application layout.
# ============================================================

st.set_page_config(
    page_title="AI MCQ Generator",
    page_icon="📝",
    layout="centered",
)

st.title("AI MCQ Generator")
st.write("Generate multiple-choice questions using AI.")

# ============================================================
# 2. CREATE THE INPUT FORM
# Allow users to select the topic, difficulty, and question count.
# ============================================================

with st.form("mcq_form"):
    topic_options = [
        "Python",
        "Java",
        "C Programming",
        "DBMS",
        "Machine Learning",
        "Artificial Intelligence",
        "Other",
    ]

    topic = st.selectbox("Topic", topic_options)

    custom_topic = ""

    if topic == "Other":
        custom_topic = st.text_input(
            "Custom topic",
            placeholder="Enter your topic",
        )

    difficulty = st.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"],
    )

    number = st.number_input(
        "Number of questions",
        min_value=1,
        max_value=50,
        value=5,
        step=1,
    )

    generate_button = st.form_submit_button("Generate MCQs")

# ============================================================
# 3. GENERATE AND DISPLAY MCQS
# Call the generator when the user submits the form.
# ============================================================

if generate_button:
    selected_topic = custom_topic.strip() if topic == "Other" else topic

    if not selected_topic:
        st.error("Please enter a custom topic.")
    else:
        with st.spinner("Generating your questions..."):
            try:
                questions = generate_mcqs(
                    selected_topic,
                    difficulty,
                    int(number),
                )

                # Save the generated questions for this session.
                st.session_state["mcq_questions"] = questions
                st.session_state["mcq_topic"] = selected_topic
                st.session_state["mcq_difficulty"] = difficulty

            except Exception as error:
                st.error(f"Unable to generate MCQs: {error}")

# ============================================================
# 4. SHOW THE GENERATED QUESTIONS
# Display each question and its four options.
# Users can reveal the correct answer and explanation.
# ============================================================

if "mcq_questions" in st.session_state:
    st.subheader(
        f"Questions: {st.session_state['mcq_topic']} "
        f"({st.session_state['mcq_difficulty']})"
    )

    for index, question in enumerate(
        st.session_state["mcq_questions"], start=1
    ):
        st.markdown(f"### Question {index}")
        st.write(question["question"])

        # Display the four available answer options.
        for option, answer in question["options"].items():
            st.write(f"**{option}.** {answer}")

        # Reveal the answer and explanation when requested.
        with st.expander("Show correct answer and explanation"):
            correct = question["correct_answer"]
            st.success(
                f"Correct answer: {correct}. "
                f"{question['options'][correct]}"
            )
            st.write(question["explanation"])

        st.divider()