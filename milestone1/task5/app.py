# ============================================================
# TASK 5: AI-BASED EXAMINATION SYSTEM WITH IMAGE TEXT EXTRACTION
# ============================================================
# This file controls the Streamlit user interface:
#   1. The student configures and generates an examination.
#   2. Part-A displays MCQs.
#   3. Part-B accepts typed answers or answer images.
#   4. OCR text is placed in an editable box.
#   5. Submitted answers are evaluated and results are displayed.
#
# The actual OpenAI/LangChain functions live in exam_generator.py.

import streamlit as st

# Import the functions that perform the AI work.
from exam_generator import (
    generate_mcqs,                 # Creates Part-A questions.
    generate_written_questions,    # Creates Part-B questions and model answers.
    extract_text_from_image,       # Reads text from an uploaded answer image.
    evaluate_written_answer,       # Grades a written answer with OpenAI.
)


# ------------------------------------------------------------
# 1. PAGE SETUP
# ------------------------------------------------------------

# Configure the browser tab title, icon, and wide page layout.
st.set_page_config(
    page_title="Task 5 - AI Examination with OCR",
    page_icon="📝",
    layout="wide",
)

# Show the main heading and explain the two answer methods.
st.title("📝 AI-Based Examination — Task 5")
st.write(
    "Part-A: MCQs. Part-B: written Q&A. In Part-B, type an answer or upload an "
    "image, extract its text, edit it, and submit the edited answer for evaluation."
)


# ------------------------------------------------------------
# 2. SESSION STATE: REMEMBER DATA BETWEEN STREAMLIT RERUNS
# ------------------------------------------------------------

# Streamlit reruns this script when a user clicks a button or changes a widget.
# session_state keeps important exam information available across those reruns.
DEFAULTS = {
    "questions_generated": False,  # Has the exam been created?
    "submitted": False,            # Has the exam been evaluated successfully?
    "mcq_questions": [],           # Generated MCQs and their correct answers.
    "written_questions": [],       # Written questions and their model answers.
    "mcq_answers": {},             # Student's selected MCQ options.
    "written_answers": {},         # Student's typed or OCR-edited answers.
    "written_results": [],         # Marks and feedback from written grading.
    "exam_topic": "",              # Topic selected for this exam.
    "exam_difficulty": "",         # Easy, Medium, or Hard.
}

# Create each session variable only if it does not already exist.
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ------------------------------------------------------------
# 3. RESET FUNCTION: START A FRESH EXAM
# ------------------------------------------------------------

def reset_exam():
    """Clear the current exam, student answers, and dynamic widget values."""

    # Remove old values belonging to question widgets and image upload controls.
    # list(...) creates a copy so it is safe to delete keys while looping.
    for key in list(st.session_state.keys()):
        if key.startswith(("mcq_answer_", "written_answer_", "answer_image_")):
            del st.session_state[key]

    # Restore the main exam data to its initial values.
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


# ------------------------------------------------------------
# 4. EXAM CONFIGURATION AND QUESTION GENERATION
# ------------------------------------------------------------

# Show this form only before questions have been generated.
if not st.session_state.questions_generated:
    st.header("Configure Examination")

    # A form groups the settings together. They are processed when submitted.
    with st.form("exam_configuration"):

        # Let the student choose a common topic or enter a custom one.
        topic_choice = st.selectbox("Topic", [
            "Python", "Java", "JavaScript", "React", "SQL",
            "Machine Learning", "Artificial Intelligence", "Data Science", "Other"
        ])

        # Ask for a custom topic only when the student selects Other.
        custom_topic = (
            st.text_input("Enter topic")
            if topic_choice == "Other"
            else ""
        )

        # The chosen difficulty is passed to the AI prompts.
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

        # Part-A settings: each correctly answered MCQ is worth one mark.
        st.subheader("Part-A: MCQ")
        mcq_count = st.number_input(
            "Number of MCQs (1 mark each)", 1, 30, 5
        )

        # Part-B settings: written questions can have more marks per question.
        st.subheader("Part-B: Written Q&A")
        written_count = st.number_input(
            "Number of written questions", 1, 20, 3
        )
        marks_each = st.number_input(
            "Marks per written question", 1, 20, 5
        )

        # Clicking this button submits the configuration form.
        generate = st.form_submit_button(
            "Generate Part-A and Part-B",
            use_container_width=True
        )

    # Generate the exam only after the configuration form is submitted.
    if generate:
        # Use the custom topic if Other was selected; otherwise use the dropdown.
        topic = custom_topic.strip() if topic_choice == "Other" else topic_choice

        if not topic:
            st.error("Please enter a topic.")
        else:
            try:
                # Show a progress message while the AI calls are running.
                with st.spinner("Generating both exam sections..."):

                    # Generate Part-A MCQs.
                    mcqs = generate_mcqs(
                        topic, difficulty, int(mcq_count)
                    )

                    # Generate Part-B written questions and model answers.
                    written = generate_written_questions(
                        topic, difficulty, int(written_count), int(marks_each)
                    )

                # Remove any previous exam data before storing the new exam.
                reset_exam()

                # Save generated questions and settings in session state.
                st.session_state.mcq_questions = mcqs
                st.session_state.written_questions = written
                st.session_state.exam_topic = topic
                st.session_state.exam_difficulty = difficulty
                st.session_state.questions_generated = True

                # Rerun so Streamlit displays the newly generated exam.
                st.rerun()

            except Exception as exc:
                # Display a helpful message and the technical error for debugging.
                st.error("Could not generate the examination.")
                st.code(f"{type(exc).__name__}: {exc}")


# ------------------------------------------------------------
# 5. DISPLAY THE EXAMINATION
# ------------------------------------------------------------

# This section runs only after the exam has been generated.
if st.session_state.questions_generated:

    # Short local names make the display code easier to read.
    mcqs = st.session_state.mcq_questions
    written = st.session_state.written_questions
    topic = st.session_state.exam_topic
    difficulty = st.session_state.exam_difficulty

    # Calculate the maximum marks for each section.
    max_a = len(mcqs)  # One mark for every MCQ.
    max_b = sum(int(q["max_marks"]) for q in written)

    st.info(
        f"Topic: {topic} | Difficulty: {difficulty} | "
        f"Total marks: {max_a + max_b}"
    )

    # Do not display editable exam questions after successful submission.
    if not st.session_state.submitted:

        # ----------------------------------------------------
        # PART-A: MCQ DISPLAY
        # ----------------------------------------------------
        st.header("Part-A: Multiple-Choice Questions")
        st.caption(
            f"{len(mcqs)} questions · 1 mark for each correct answer"
        )

        # Display every MCQ and its four options.
        for i, q in enumerate(mcqs):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            opts = q["options"]

            # Radio buttons let the student select one option.
            # format_func displays both the option letter and its text.
            # The unique key stores each question's answer separately.
            # index=None means no option is selected initially.
            st.radio(
                "Choose an answer",
                ["A", "B", "C", "D"],
                format_func=lambda k, options=opts: f"{k}. {options[k]}",
                key=f"mcq_answer_{i}",
                index=None
            )
            st.divider()

        # ----------------------------------------------------
        # PART-B: WRITTEN QUESTIONS AND OPTIONAL IMAGE UPLOAD
        # ----------------------------------------------------
        st.header("Part-B: Written Question & Answer")
        st.write(
            "For each question, type your answer OR upload an image of it. "
            "Click Extract Text, then edit the extracted text in the answer box."
        )

        # Create a separate answer box and optional image uploader for each question.
        for i, q in enumerate(written):

            # This key links the answer text box to the correct question.
            answer_key = f"written_answer_{i}"

            st.subheader(f"Q{i+1} · {q['max_marks']} marks")
            st.markdown(f"**{q['question']}**")

            # Accept image files only in the listed formats.
            uploaded = st.file_uploader(
                f"Upload answer image for Q{i+1} (optional)",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"answer_image_{i}",
            )

            # Preview the uploaded image so the student can verify it.
            if uploaded is not None:
                st.image(
                    uploaded,
                    caption=f"Answer image for Q{i+1}",
                    use_container_width=True
                )

            # The extraction button is disabled until an image is uploaded.
            if st.button(
                f"Extract Text from Image — Q{i+1}",
                key=f"extract_answer_{i}",
                disabled=uploaded is None
            ):
                try:
                    # Call gpt-4o vision through extract_text_from_image().
                    with st.spinner(f"Reading image for Q{i+1}..."):
                        extracted = extract_text_from_image(uploaded)

                    # If the student already typed text, append the extracted text.
                    # Otherwise, put the extracted text into the answer field.
                    existing = st.session_state.get(answer_key, "").strip()
                    st.session_state[answer_key] = (
                        existing + "\n\n" + extracted
                        if existing
                        else extracted
                    )

                    st.success(
                        "Text extracted. Review and edit it below."
                    )

                    # Rerun to refresh the text box with the extracted text.
                    st.rerun()

                except Exception as exc:
                    # Show extraction errors such as invalid images or API issues.
                    st.error(f"Text extraction failed for Q{i+1}.")
                    st.code(f"{type(exc).__name__}: {exc}")

            # This text box is editable. The student can correct OCR mistakes
            # or type the entire answer manually without using an image.
            st.text_area(
                f"Your answer for Q{i+1} (editable)",
                key=answer_key,
                height=140,
                placeholder=(
                    "Type your answer here, or extract it from an image above..."
                )
            )
            st.divider()

        # Remind the student that the OCR result should be checked.
        st.warning(
            "Review the text in every answer box before submitting. "
            "The edited text, not the original image, is evaluated."
        )

        # ----------------------------------------------------
        # 6. SUBMIT ANSWERS AND EVALUATE PART-B
        # ----------------------------------------------------
        if st.button(
            "Submit Examination",
            type="primary",
            use_container_width=True
        ):

            # Collect the selected MCQ option for each question.
            mcq_answers = {
                i: st.session_state.get(f"mcq_answer_{i}")
                for i in range(len(mcqs))
            }

            # Collect each written answer. strip() removes extra spaces
            # at the beginning and end.
            written_answers = {
                i: st.session_state.get(
                    f"written_answer_{i}", ""
                ).strip()
                for i in range(len(written))
            }

            # Save answers before making API calls, so they remain available
            # if a written-answer evaluation fails.
            st.session_state.mcq_answers = mcq_answers
            st.session_state.written_answers = written_answers

            # Keep any evaluations already completed if a previous attempt failed.
            results = list(st.session_state.written_results)

            try:
                # Written grading calls the OpenAI model, so show a progress message.
                with st.spinner("OpenAI is evaluating Part-B answers..."):

                    for i, q in enumerate(written):

                        # Do not grade the same question twice if its result is
                        # already stored from an earlier partial attempt.
                        if i < len(results):
                            continue

                        # Compare this student's answer against the model answer.
                        result = evaluate_written_answer(
                            topic, difficulty, q, written_answers[i]
                        )

                        # Defensively ensure awarded marks stay within the allowed range.
                        maximum = float(q["max_marks"])
                        result["marks_awarded"] = max(
                            0.0,
                            min(
                                maximum,
                                float(result.get("marks_awarded", 0))
                            )
                        )

                        # Store the completed result immediately.
                        results.append(result)
                        st.session_state.written_results = results

                # Mark the exam as submitted only after every answer is evaluated.
                st.session_state.submitted = True
                st.rerun()

            except Exception as exc:
                # Keep completed results and submitted answers so the user can retry.
                st.session_state.written_results = results
                st.error(
                    "Evaluation did not finish. Your answers are saved; "
                    "fix the error and submit again."
                )
                st.code(f"{type(exc).__name__}: {exc}")


# ------------------------------------------------------------
# 7. RESULTS PAGE
# ------------------------------------------------------------

# Show results only when the exam has been generated and successfully submitted.
if st.session_state.questions_generated and st.session_state.submitted:

    mcqs = st.session_state.mcq_questions
    written = st.session_state.written_questions
    mcq_answers = st.session_state.mcq_answers
    written_answers = st.session_state.written_answers
    results = st.session_state.written_results

    # --------------------------------------------------------
    # PART-A SCORE CALCULATION
    # --------------------------------------------------------
    correct_count = 0
    wrong_count = 0
    unanswered_count = 0

    for i, q in enumerate(mcqs):
        selected = mcq_answers.get(i)

        if not selected:
            unanswered_count += 1
        elif selected.upper() == q["correct_answer"]:
            correct_count += 1
        else:
            wrong_count += 1

    # MCQs are worth one mark each, so the number correct is the Part-A score.
    part_a_max = len(mcqs)
    part_a_score = correct_count

    # Part-B maximum marks are the sum of all written question marks.
    part_b_max = sum(int(q["max_marks"]) for q in written)

    # Part-B score is the sum of marks awarded by the AI evaluator.
    part_b_score = sum(
        float(r.get("marks_awarded", 0))
        for r in results
    )

    # Combine both sections to calculate the overall score and percentage.
    total_max = part_a_max + part_b_max
    total_score = part_a_score + part_b_score
    percent = total_score / total_max * 100 if total_max else 0

    st.success("Examination submitted and evaluated.")
    st.header("Final Results")

    # Display important results in metric cards.
    c1, c2, c3 = st.columns(3)
    c1.metric("Marks Obtained", f"{total_score:g} / {total_max}")
    c2.metric("Percentage", f"{percent:.2f}%")
    c3.metric("Part-A Score", f"{part_a_score} / {part_a_max}")

    # The progress bar represents the percentage achieved.
    st.progress(max(0.0, min(1.0, percent / 100)))

    # Show each section's score separately.
    a, b = st.columns(2)
    a.metric("Part-A: MCQ", f"{part_a_score} / {part_a_max}")
    b.metric("Part-B: Written Q&A", f"{part_b_score:g} / {part_b_max}")

    # --------------------------------------------------------
    # PART-A ANSWER REVIEW
    # --------------------------------------------------------
    st.header("Part-A: MCQ Review")
    st.write(
        f"Correct: {correct_count} · Wrong: {wrong_count} · "
        f"Unanswered: {unanswered_count}"
    )

    for i, q in enumerate(mcqs):
        selected = mcq_answers.get(i)
        correct = q["correct_answer"]
        opts = q["options"]

        st.subheader(f"Q{i+1}. {q['question']}")

        # Display the student's choice and the correct option.
        st.write(
            f"Your answer: "
            f"{selected + '. ' + opts[selected] if selected else 'Not answered'}"
        )
        st.write(f"Correct answer: {correct}. {opts[correct]}")

        # Give clear feedback on whether the student earned the mark.
        if selected and selected == correct:
            st.success("Correct · 1 mark")
        else:
            st.error("Incorrect/unanswered · 0 marks")

        # Explain why the correct option is right.
        st.info(
            f"Explanation: {q.get('explanation', 'No explanation provided.')}"
        )
        st.divider()

    # --------------------------------------------------------
    # PART-B WRITTEN ANSWER REVIEW
    # --------------------------------------------------------
    st.header("Part-B: Written Answer Evaluation")

    for i, q in enumerate(written):
        result = results[i]
        maximum = int(q["max_marks"])
        score = float(result.get("marks_awarded", 0))

        st.subheader(f"Q{i+1} · {maximum} marks")
        st.write(q["question"])

        # Show the exact text that was graded, including OCR text edited by the student.
        st.markdown(
            "**Your submitted answer (typed or OCR-extracted and edited):**"
        )
        st.write(written_answers.get(i) or "Not answered.")

        # Display the model answer generated with the written question.
        st.markdown("**Correct/model answer:**")
        st.write(q["expected_answer"])

        # Show the AI-awarded marks and feedback.
        st.metric("Marks awarded", f"{score:g} / {maximum}")
        st.markdown("**AI feedback**")
        st.write(result.get("feedback", "No feedback available."))

        # Strengths identify correct ideas in the student's response.
        if result.get("strengths"):
            st.markdown("**What you did well**")
            for item in result["strengths"]:
                st.write(f"✅ {item}")

        # Improvements explain what could be added or corrected.
        if result.get("improvements"):
            st.markdown("**What to improve**")
            for item in result["improvements"]:
                st.write(f"📌 {item}")

        st.divider()

    # Let the student clear this exam and configure a new one.
    if st.button("Start New Examination", use_container_width=True):
        reset_exam()
        st.rerun()
