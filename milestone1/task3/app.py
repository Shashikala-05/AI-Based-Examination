import streamlit as st
from mcq_generator import generate_mcqs


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI-Based Examination System",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 2. CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>
        .main-title {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .subtitle {
            text-align: center;
            font-size: 17px;
            margin-bottom: 25px;
        }

        .section-title {
            font-size: 25px;
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 15px;
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 15px;
            opacity: 0.7;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 3. SESSION STATE
# =========================================================

if "questions" not in st.session_state:
    st.session_state.questions = []

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}

if "exam_topic" not in st.session_state:
    st.session_state.exam_topic = ""

if "exam_difficulty" not in st.session_state:
    st.session_state.exam_difficulty = ""

if "exam_number" not in st.session_state:
    st.session_state.exam_number = 0


# =========================================================
# 4. RESET EXAMINATION
# =========================================================

def reset_exam():

    st.session_state.questions = []
    st.session_state.submitted = False
    st.session_state.user_answers = {}

    st.session_state.exam_topic = ""
    st.session_state.exam_difficulty = ""
    st.session_state.exam_number = 0

    # Clear previous radio-button selections
    for key in list(st.session_state.keys()):
        if key.startswith("answer_"):
            del st.session_state[key]


# =========================================================
# 5. APPLICATION HEADER
# =========================================================

st.markdown(
    '<div class="main-title">'
    '📝 AI-Based Examination System'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="subtitle">
        Test your knowledge with AI-generated multiple-choice questions.
        <br>
        Complete your examination, check your marks, and learn from your mistakes.
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# 6. SIDEBAR
# =========================================================

with st.sidebar:

    st.title("🎓 AI Examination")

    st.write(
        "Welcome to your AI-powered examination platform!"
    )

    st.write(
        "Practise different subjects, test your knowledge, "
        "and improve your understanding."
    )

    st.divider()

    st.subheader("📌 How It Works")

    st.markdown(
        """
        **Step 1:** Select your subject.

        **Step 2:** Choose the difficulty level.

        **Step 3:** Generate your questions.

        **Step 4:** Select your answers.

        **Step 5:** Submit your examination.

        **Step 6:** Review your results.
        """
    )

    st.divider()

    st.caption("AI-Based Examination Project | Task 3")


# =========================================================
# 7. EXAMINATION SETUP
# =========================================================

st.markdown(
    '<div class="section-title">'
    '1. Prepare Your Examination'
    '</div>',
    unsafe_allow_html=True
)

st.write(
    "Let's prepare your test. Choose a subject, select your "
    "preferred difficulty, and decide how many questions "
    "you would like to answer."
)


with st.form("exam_setup_form"):

    topics = [
        "Python",
        "Java",
        "C Programming",
        "C++",
        "HTML and CSS",
        "JavaScript",
        "React.js",
        "Node.js",
        "SQL",
        "DBMS",
        "Artificial Intelligence",
        "Machine Learning",
        "Data Science",
        "Computer Networks",
        "Operating Systems",
        "Other"
    ]

    topic = st.selectbox(
        "📚 Select Your Subject",
        topics
    )

    custom_topic = ""

    if topic == "Other":

        custom_topic = st.text_input(
            "Enter Your Subject",
            placeholder="For example, Natural Language Processing"
        )

    col1, col2 = st.columns(2)

    with col1:

        difficulty = st.selectbox(
            "🎯 Difficulty Level",
            ["Easy", "Medium", "Hard"]
        )

    with col2:

        number = st.selectbox(
            "🔢 Number of Questions",
            [5, 10, 15, 20, 25, 30, 40, 50]
        )

    generate_button = st.form_submit_button(
        "🚀 Generate My Examination",
        use_container_width=True
    )


# =========================================================
# 8. GENERATE MCQ QUESTIONS
# =========================================================

if generate_button:

    final_topic = (
        custom_topic.strip()
        if topic == "Other"
        else topic
    )

    if not final_topic:

        st.error("Please enter a subject.")

    else:

        with st.spinner(
            "Your examination is being prepared. "
            "Please wait while AI generates your questions..."
        ):

            try:

                generated_questions = generate_mcqs(
                    topic=final_topic,
                    difficulty=difficulty,
                    number=int(number)
                )

                # Save generated questions
                st.session_state.questions = generated_questions

                # Reset previous examination results
                st.session_state.submitted = False
                st.session_state.user_answers = {}

                # Save examination details
                st.session_state.exam_topic = final_topic
                st.session_state.exam_difficulty = difficulty
                st.session_state.exam_number = int(number)

                # Clear answers from an earlier test
                for key in list(st.session_state.keys()):

                    if key.startswith("answer_"):
                        del st.session_state[key]

                st.success(
                    "Your examination is ready! "
                    "Good luck with your test."
                )

            except Exception as error:

                st.error(
                    "Sorry, we couldn't generate your questions."
                )

                st.write(
                    "Please check your OpenAI API configuration, "
                    "API quota, and internet connection."
                )

                with st.expander("View Technical Error"):

                    st.code(str(error))


# =========================================================
# 9. DISPLAY EXAMINATION
# =========================================================

if st.session_state.questions:

    questions = st.session_state.questions

    st.divider()

    st.markdown(
        '<div class="section-title">'
        '2. Answer Your Questions'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"**Subject:** {st.session_state.exam_topic}"
    )

    st.write(
        f"**Difficulty:** {st.session_state.exam_difficulty}"
    )

    st.write(
        f"**Total Questions:** {len(questions)}"
    )

    st.write("**Marks Per Correct Answer:** 1")

    st.info(
        "Read each question carefully and select one answer. "
        "You can leave a question unanswered if you are unsure."
    )


    # =====================================================
    # 10. ANSWER SELECTION
    # =====================================================

    if not st.session_state.submitted:

        with st.form("answer_sheet_form"):

            for index, question in enumerate(questions):

                st.markdown(
                    f"### Question {index + 1}"
                )

                st.write(question["question"])

                option_labels = [
                    f"{letter}. {question['options'][letter]}"
                    for letter in ["A", "B", "C", "D"]
                ]

                st.radio(
                    "Choose Your Answer",
                    options=option_labels,
                    index=None,
                    key=f"answer_{index}",
                    label_visibility="collapsed"
                )

                st.divider()

            submit_button = st.form_submit_button(
                "✅ Submit My Examination",
                use_container_width=True
            )


        # =================================================
        # 11. PROCESS ANSWERS
        # =================================================

        if submit_button:

            answers = {}

            for index, question in enumerate(questions):

                selected_option = st.session_state.get(
                    f"answer_{index}"
                )

                if selected_option:

                    # Extract the answer letter
                    answers[index] = selected_option[0]

            st.session_state.user_answers = answers

            st.session_state.submitted = True

            st.rerun()


    # =====================================================
    # 12. EVALUATE EXAMINATION
    # =====================================================

    if st.session_state.submitted:

        st.divider()

        st.markdown(
            '<div class="section-title">'
            '3. Your Examination Results'
            '</div>',
            unsafe_allow_html=True
        )

        st.write(
            "Your examination has been evaluated. "
            "Here is your performance summary."
        )

        user_answers = st.session_state.user_answers

        total_questions = len(questions)

        correct_count = 0
        wrong_count = 0
        unanswered_count = 0

        # Compare selected answers with correct answers
        for index, question in enumerate(questions):

            user_answer = user_answers.get(index)

            correct_answer = question["correct_answer"]

            if user_answer is None:

                unanswered_count += 1

            elif user_answer == correct_answer:

                correct_count += 1

            else:

                wrong_count += 1


        # Calculate marks and percentage
        total_marks = total_questions

        marks_obtained = correct_count

        percentage = (
            (marks_obtained / total_marks) * 100
            if total_marks > 0
            else 0
        )


        # =================================================
        # 13. RESULT SUMMARY
        # =================================================

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Total Marks",
                total_marks
            )

        with col2:

            st.metric(
                "Marks Obtained",
                f"{marks_obtained}/{total_marks}"
            )

        with col3:

            st.metric(
                "Correct Answers",
                correct_count
            )

        with col4:

            st.metric(
                "Wrong Answers",
                wrong_count
            )

        st.metric(
            "Unanswered Questions",
            unanswered_count
        )

        st.progress(percentage / 100)

        st.subheader(
            f"Your Final Score: {percentage:.2f}%"
        )


        # Friendly result feedback
        if percentage >= 90:

            st.success(
                "Excellent work! 🌟 "
                "You have performed exceptionally well."
            )

        elif percentage >= 75:

            st.success(
                "Great job! 👏 Keep practising to strengthen your skills."
            )

        elif percentage >= 50:

            st.info(
                "Good effort! Review your mistakes and keep learning."
            )

        else:

            st.warning(
                "Don't give up! Review the correct answers and "
                "try another examination."
            )


        st.divider()


        # =================================================
        # 14. CORRECT ANSWERS AND EXPLANATIONS
        # =================================================

        st.markdown(
            '<div class="section-title">'
            '4. Review Your Answers'
            '</div>',
            unsafe_allow_html=True
        )

        st.write(
            "Let's review each question. You can see your selected "
            "answer, the correct answer, and an explanation."
        )

        for index, question in enumerate(questions):

            user_answer = user_answers.get(index)

            correct_answer = question["correct_answer"]

            with st.container(border=True):

                st.markdown(
                    f"### Question {index + 1}"
                )

                st.write(question["question"])

                # Display the user's answer
                if user_answer is None:

                    st.warning(
                        "Your Answer: Not Answered"
                    )

                elif user_answer == correct_answer:

                    st.success(
                        f"Your Answer: {user_answer}. "
                        f"{question['options'][user_answer]} — Correct!"
                    )

                else:

                    st.error(
                        f"Your Answer: {user_answer}. "
                        f"{question['options'][user_answer]} — Incorrect."
                    )

                # Display the correct answer
                st.info(
                    f"Correct Answer: {correct_answer}. "
                    f"{question['options'][correct_answer]}"
                )

                # Display explanation
                with st.expander("💡 Read the Explanation"):

                    st.write(
                        question.get(
                            "explanation",
                            "No explanation is available."
                        )
                    )


        # =================================================
        # 15. START A NEW EXAMINATION
        # =================================================

        st.divider()

        st.markdown(
            '<div class="section-title">'
            '5. Continue Learning'
            '</div>',
            unsafe_allow_html=True
        )

        st.write(
            "Ready for another challenge? Start a new examination "
            "and practise a different topic or difficulty level."
        )

        if st.button(
            "🔄 Start a New Examination",
            use_container_width=True
        ):

            reset_exam()

            st.rerun()


# =========================================================
# 16. FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        AI-Based Examination System | Task 3
        <br>
        Practise regularly, learn from your mistakes, and keep improving.
    </div>
    """,
    unsafe_allow_html=True
)