import streamlit as st

from exam_generator import (
    generate_mcqs,
    generate_written_questions,
    evaluate_written_answer,
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="AI-Based Examination",
    page_icon="📝",
    layout="wide",
)

st.title("📝 AI-Based Examination System")
st.write(
    "Create one examination with Part-A MCQs and Part-B written questions. "
    "After submission, view marks, correct answers, model answers, and feedback."
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

DEFAULTS = {
    "questions_generated": False,
    "submitted": False,
    "mcq_questions": [],
    "written_questions": [],
    "mcq_answers": {},
    "written_answers": {},
    "written_results": [],
    "exam_topic": "",
    "exam_difficulty": "",
    "exam_error": "",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_exam():
    """Clear exam data and answer widget values."""

    for key in list(st.session_state.keys()):
        if key.startswith("mcq_answer_") or key.startswith("written_answer_"):
            del st.session_state[key]

    for key, value in DEFAULTS.items():
        st.session_state[key] = value


# --------------------------------------------------
# EXAM CONFIGURATION AND GENERATION
# --------------------------------------------------

if not st.session_state.questions_generated:
    st.header("⚙️ Configure Examination")

    with st.form("exam_configuration"):
        topic_choice = st.selectbox(
            "Choose topic",
            [
                "Python",
                "Java",
                "JavaScript",
                "React",
                "SQL",
                "Machine Learning",
                "Artificial Intelligence",
                "Data Science",
                "Other",
            ],
        )

        custom_topic = ""
        if topic_choice == "Other":
            custom_topic = st.text_input("Enter your topic")

        difficulty = st.selectbox(
            "Difficulty",
            ["Easy", "Medium", "Hard"],
        )

        st.subheader("Part-A: MCQ")
        mcq_count = st.number_input(
            "Number of MCQs (1 mark each)",
            min_value=1,
            max_value=30,
            value=5,
            step=1,
        )

        st.subheader("Part-B: Written Questions")
        written_count = st.number_input(
            "Number of written questions",
            min_value=1,
            max_value=20,
            value=3,
            step=1,
        )

        marks_per_question = st.number_input(
            "Marks for each written question",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
        )

        generate = st.form_submit_button(
            "Generate Part-A and Part-B",
            use_container_width=True,
        )

    if generate:
        topic = (
            custom_topic.strip()
            if topic_choice == "Other"
            else topic_choice
        )

        if not topic:
            st.error("Please enter a topic.")
        else:
            try:
                with st.spinner(
                    "OpenAI is generating Part-A and Part-B..."
                ):
                    # Generate both sections in the same examination.
                    mcqs = generate_mcqs(
                        topic,
                        difficulty,
                        int(mcq_count),
                    )
                    written = generate_written_questions(
                        topic,
                        difficulty,
                        int(written_count),
                        int(marks_per_question),
                    )

                # Clear old widget values only after generation succeeds.
                reset_exam()
                st.session_state.mcq_questions = mcqs
                st.session_state.written_questions = written
                st.session_state.exam_topic = topic
                st.session_state.exam_difficulty = difficulty
                st.session_state.questions_generated = True
                st.rerun()

            except Exception as error:
                st.error(
                    "Could not generate the examination. Check your API key, "
                    "API access/quota, internet connection, and try again."
                )
                with st.expander("Technical error details"):
                    st.code(str(error))


# --------------------------------------------------
# DISPLAY EXAM
# --------------------------------------------------

if st.session_state.questions_generated:
    mcqs = st.session_state.mcq_questions
    written_questions = st.session_state.written_questions
    topic = st.session_state.exam_topic
    difficulty = st.session_state.exam_difficulty

    part_a_total = len(mcqs)
    part_b_total = sum(
        int(question["max_marks"]) for question in written_questions
    )
    total_marks = part_a_total + part_b_total

    st.info(
        f"**Topic:** {topic}  |  **Difficulty:** {difficulty}  |  "
        f"**Maximum marks:** {total_marks}"
    )

    # --------------------------------------------------
    # ONE FORM FOR BOTH PARTS
    # --------------------------------------------------

    if not st.session_state.submitted:
        with st.form("complete_exam"):
            st.header("Part-A: Multiple-Choice Questions")
            st.caption(
                f"{len(mcqs)} questions · 1 mark per correct answer"
            )

            for index, question in enumerate(mcqs):
                st.markdown(
                    f"**Q{index + 1}. {question['question']}**"
                )

                options = question["options"]
                st.radio(
                    "Choose one answer",
                    options=["A", "B", "C", "D"],
                    format_func=lambda option, opts=options: (
                        f"{option}. {opts[option]}"
                    ),
                    key=f"mcq_answer_{index}",
                    index=None,
                )
                st.divider()

            st.header("Part-B: Question & Answer")
            st.caption(
                "Write your answers in your own words. OpenAI will evaluate "
                "them after you submit."
            )

            for index, question in enumerate(written_questions):
                st.markdown(
                    f"**Q{index + 1}. {question['question']}**"
                )
                st.caption(f"Maximum marks: {question['max_marks']}")

                st.text_area(
                    "Your answer",
                    key=f"written_answer_{index}",
                    height=140,
                    placeholder="Type your answer here...",
                )
                st.divider()

            submit_exam = st.form_submit_button(
                "Submit Examination",
                use_container_width=True,
            )

        if submit_exam:
            mcq_answers = {
                index: st.session_state.get(f"mcq_answer_{index}")
                for index in range(len(mcqs))
            }
            written_answers = {
                index: st.session_state.get(
                    f"written_answer_{index}", ""
                ).strip()
                for index in range(len(written_questions))
            }

            try:
                results = []
                with st.spinner(
                    "Evaluating Part-B written answers with OpenAI..."
                ):
                    for index, question in enumerate(written_questions):
                        result = evaluate_written_answer(
                            topic=topic,
                            difficulty=difficulty,
                            question=question,
                            student_answer=written_answers[index],
                        )
                        # Clamp and normalize the marks defensively.
                        maximum = float(question["max_marks"])
                        awarded = float(result.get("marks_awarded", 0))
                        result["marks_awarded"] = max(
                            0.0, min(maximum, awarded)
                        )
                        results.append(result)

                st.session_state.mcq_answers = mcq_answers
                st.session_state.written_answers = written_answers
                st.session_state.written_results = results
                st.session_state.submitted = True
                st.rerun()

            except Exception as error:
                st.error(
                    "The written answers could not be evaluated. Check your "
                    "OpenAI API access/quota and try submitting again."
                )
                with st.expander("Technical error details"):
                    st.code(str(error))


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

if st.session_state.questions_generated and st.session_state.submitted:
    mcqs = st.session_state.mcq_questions
    written_questions = st.session_state.written_questions
    mcq_answers = st.session_state.mcq_answers
    written_answers = st.session_state.written_answers
    written_results = st.session_state.written_results

    st.success("Examination submitted and evaluated.")
    st.header("📊 Final Results")

    # Part-A score
    mcq_correct = 0
    mcq_wrong = 0
    mcq_unanswered = 0

    for index, question in enumerate(mcqs):
        selected = mcq_answers.get(index)
        correct = question["correct_answer"].strip().upper()

        if not selected:
            mcq_unanswered += 1
        elif selected.strip().upper() == correct:
            mcq_correct += 1
        else:
            mcq_wrong += 1

    part_a_obtained = mcq_correct
    part_a_total = len(mcqs)

    # Part-B score
    part_b_total = sum(
        int(question["max_marks"]) for question in written_questions
    )
    part_b_obtained = sum(
        float(result["marks_awarded"]) for result in written_results
    )

    total_marks = part_a_total + part_b_total
    obtained_marks = part_a_obtained + part_b_obtained
    percentage = (
        obtained_marks / total_marks * 100 if total_marks else 0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Total Marks",
        f"{obtained_marks:g} / {total_marks}",
    )
    col2.metric("Percentage", f"{percentage:.2f}%")
    col3.metric(
        "Part-A MCQ Score",
        f"{part_a_obtained} / {part_a_total}",
    )

    st.progress(max(0.0, min(1.0, percentage / 100)))

    st.subheader("Section Summary")
    summary_col1, summary_col2 = st.columns(2)
    summary_col1.metric(
        "Part-A: MCQ",
        f"{part_a_obtained} / {part_a_total}",
    )
    summary_col2.metric(
        "Part-B: Written Answers",
        f"{part_b_obtained:g} / {part_b_total}",
    )

    # --------------------------------------------------
    # PART-A REVIEW
    # --------------------------------------------------

    st.header("Part-A: MCQ Answer Review")
    st.write(
        f"Correct: {mcq_correct} · Wrong: {mcq_wrong} · "
        f"Unanswered: {mcq_unanswered}"
    )

    for index, question in enumerate(mcqs):
        selected = mcq_answers.get(index)
        correct = question["correct_answer"].strip().upper()
        options = question["options"]

        st.markdown(f"**Q{index + 1}. {question['question']}**")

        if selected:
            st.write(
                f"**Your answer:** {selected}. {options[selected]}"
            )
        else:
            st.write("**Your answer:** Not answered")

        st.write(
            f"**Correct answer:** {correct}. {options[correct]}"
        )

        if selected and selected.strip().upper() == correct:
            st.success("Correct · 1 mark")
        else:
            st.error("Incorrect or unanswered · 0 marks")

        st.info(
            f"**Explanation:** {question.get('explanation', 'No explanation provided.')}"
        )
        st.divider()

    # --------------------------------------------------
    # PART-B REVIEW
    # --------------------------------------------------

    st.header("Part-B: Written Answer Evaluation")

    for index, question in enumerate(written_questions):
        result = written_results[index]
        maximum = int(question["max_marks"])
        awarded = float(result.get("marks_awarded", 0))

        st.subheader(f"Q{index + 1} · {maximum} marks")
        st.write(question["question"])

        st.markdown("**Your answer**")
        student_answer = written_answers.get(index, "")
        st.write(student_answer if student_answer else "Not answered.")

        st.markdown("**Correct / model answer**")
        st.write(question["expected_answer"])

        st.metric("Marks awarded", f"{awarded:g} / {maximum}")

        st.markdown("**AI feedback**")
        st.write(result.get("feedback", "No feedback available."))

        strengths = result.get("strengths", [])
        if strengths:
            st.markdown("**What you did well**")
            for item in strengths:
                st.write(f"✅ {item}")

        improvements = result.get("improvements", [])
        if improvements:
            st.markdown("**What to improve**")
            for item in improvements:
                st.write(f"📌 {item}")

        st.divider()

    if st.button("Start New Examination", use_container_width=True):
        reset_exam()
        st.rerun()
