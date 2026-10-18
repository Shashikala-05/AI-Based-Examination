import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


# --------------------------------------------------
# 1. LOAD OPENAI API KEY
# --------------------------------------------------

# This file is expected at milestone1/task4/exam_generator.py.
# parents[2] points to the AI-Based Examination project root.
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env", override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY is missing. Add it to the .env file "
        "in the AI-Based Examination project root."
    )


# --------------------------------------------------
# 2. INITIALIZE OPENAI MODEL THROUGH LANGCHAIN
# --------------------------------------------------

model = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=OPENAI_API_KEY,
    temperature=0.2,
)


# --------------------------------------------------
# 3. JSON PARSER
# --------------------------------------------------

def parse_json_response(content):
    """Parse JSON returned by the model, including fenced JSON."""

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
            else:
                parts.append(str(block))
        content = "".join(parts)

    content = str(content).strip()
    content = re.sub(
        r"^\s*```(?:json)?\s*|\s*```\s*$",
        "",
        content,
        flags=re.IGNORECASE,
    ).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "OpenAI returned invalid JSON. Please generate again."
        ) from exc


def _validate_topic_and_difficulty(topic, difficulty):
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Please enter a topic.")

    if difficulty not in ("Easy", "Medium", "Hard"):
        raise ValueError("Difficulty must be Easy, Medium, or Hard.")


# --------------------------------------------------
# 4. PART-A: MCQ GENERATION
# --------------------------------------------------

mcq_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an experienced teacher and examination creator.
Generate multiple-choice questions for the given topic and difficulty.

Return ONLY valid JSON in this exact structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correct_answer": "A",
      "explanation": "Why the correct option is correct"
    }}
  ]
}}

Rules:
1. Generate exactly the requested number of questions.
2. Every question must have exactly four non-empty options A, B, C, and D.
3. Only one option must be correct.
4. correct_answer must be A, B, C, or D.
5. Explanations must be educational and accurate.
6. Avoid duplicate questions.
7. Match the requested difficulty.
8. Return JSON only, with no Markdown fences.
"""
    ),
    (
        "human",
        "Topic: {topic}\nDifficulty: {difficulty}\nNumber of questions: {number}"
    ),
])

mcq_chain = mcq_prompt | model


def generate_mcqs(topic, difficulty, number):
    _validate_topic_and_difficulty(topic, difficulty)

    if not isinstance(number, int) or not 1 <= number <= 30:
        raise ValueError("MCQ count must be between 1 and 30.")

    response = mcq_chain.invoke({
        "topic": topic.strip(),
        "difficulty": difficulty,
        "number": number,
    })
    data = parse_json_response(response.content)
    questions = data.get("questions") if isinstance(data, dict) else None

    if not isinstance(questions, list) or len(questions) != number:
        raise ValueError(
            f"Expected {number} MCQs. OpenAI returned an invalid number "
            "of questions. Please generate the examination again."
        )

    required_options = ("A", "B", "C", "D")

    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise ValueError(f"MCQ {index} is invalid.")

        question_text = str(question.get("question", "")).strip()
        options = question.get("options")
        correct = str(question.get("correct_answer", "")).strip().upper()

        if not question_text:
            raise ValueError(f"MCQ {index} has no question text.")

        if not isinstance(options, dict):
            raise ValueError(f"MCQ {index} has invalid options.")

        cleaned_options = {
            letter: str(options.get(letter, "")).strip()
            for letter in required_options
        }

        if not all(cleaned_options.values()):
            raise ValueError(f"MCQ {index} must have four non-empty options.")

        if correct not in required_options:
            raise ValueError(f"MCQ {index} has an invalid correct answer.")

        question["question"] = question_text
        question["options"] = cleaned_options
        question["correct_answer"] = correct
        question["explanation"] = str(
            question.get("explanation", "No explanation provided.")
        )

    return questions


# --------------------------------------------------
# 5. PART-B: WRITTEN QUESTION GENERATION
# --------------------------------------------------

written_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an experienced teacher creating a written examination.
Create questions that require students to explain concepts in their own words.

Return ONLY valid JSON in this exact structure:
{{
  "questions": [
    {{
      "question": "Written question text",
      "expected_answer": "Accurate model answer",
      "max_marks": 5,
      "key_points": [
        "Important point one",
        "Important point two",
        "Important point three"
      ]
    }}
  ]
}}

Rules:
1. Generate exactly the requested number of questions.
2. Match the requested difficulty.
3. Avoid duplicate questions.
4. Model answers must be accurate and sufficiently detailed.
5. Include useful key points for grading.
6. max_marks must be a positive integer.
7. Return valid JSON only, without Markdown fences.
"""
    ),
    (
        "human",
        "Topic: {topic}\nDifficulty: {difficulty}\n"
        "Number of questions: {number}\n"
        "Marks per question: {marks_per_question}"
    ),
])

written_chain = written_prompt | model


def generate_written_questions(topic, difficulty, number, marks_per_question):
    _validate_topic_and_difficulty(topic, difficulty)

    if not isinstance(number, int) or not 1 <= number <= 20:
        raise ValueError("Written question count must be between 1 and 20.")

    if (
        not isinstance(marks_per_question, int)
        or not 1 <= marks_per_question <= 20
    ):
        raise ValueError("Marks per written question must be between 1 and 20.")

    response = written_chain.invoke({
        "topic": topic.strip(),
        "difficulty": difficulty,
        "number": number,
        "marks_per_question": marks_per_question,
    })
    data = parse_json_response(response.content)
    questions = data.get("questions") if isinstance(data, dict) else None

    if not isinstance(questions, list) or len(questions) != number:
        raise ValueError(
            f"Expected {number} written questions. OpenAI returned an invalid "
            "number of questions. Please generate the examination again."
        )

    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise ValueError(f"Written question {index} is invalid.")

        question_text = str(question.get("question", "")).strip()
        expected_answer = str(question.get("expected_answer", "")).strip()

        if not question_text:
            raise ValueError(f"Written question {index} has no question text.")

        if not expected_answer:
            raise ValueError(
                f"Written question {index} has no model answer."
            )

        key_points = question.get("key_points", [])
        if not isinstance(key_points, list):
            key_points = []

        question["question"] = question_text
        question["expected_answer"] = expected_answer
        question["max_marks"] = marks_per_question
        question["key_points"] = [
            str(point) for point in key_points
        ]

    return questions


# --------------------------------------------------
# 6. PART-B: WRITTEN ANSWER EVALUATION
# --------------------------------------------------

evaluation_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a fair, constructive examination evaluator.
Compare the student's answer with the question, model answer, and key points.

Award marks for correct understanding, relevant details, and valid alternative
wording. Do not require the student to use exactly the same words as the model
answer. Do not award marks for incorrect or irrelevant statements.

Return ONLY valid JSON in this structure:
{{
  "marks_awarded": 3,
  "feedback": "Brief explanation of the mark awarded",
  "strengths": ["Correct point included by the student"],
  "improvements": ["Important missing or incorrect point"]
}}

Rules:
1. marks_awarded must be a number between 0 and max_marks.
2. A blank or entirely incorrect answer receives zero.
3. Award partial marks for partially correct answers.
4. Never award more than max_marks.
5. Be fair to different correct ways of explaining a concept.
6. Return valid JSON only.
"""
    ),
    (
        "human",
        """
Topic: {topic}
Difficulty: {difficulty}

Question:
{question}

Expected/model answer:
{expected_answer}

Important key points:
{key_points}

Student answer:
{student_answer}

Maximum marks:
{max_marks}

Evaluate the student's answer and return the result as JSON.
"""
    ),
])

evaluation_chain = evaluation_prompt | model


def evaluate_written_answer(topic, difficulty, question, student_answer):
    """Evaluate one written answer and return marks and feedback."""

    max_marks = int(question["max_marks"])
    student_answer = (student_answer or "").strip()

    if not student_answer:
        return {
            "marks_awarded": 0,
            "feedback": "No answer was provided.",
            "strengths": [],
            "improvements": ["Attempt the question."],
        }

    response = evaluation_chain.invoke({
        "topic": topic,
        "difficulty": difficulty,
        "question": question["question"],
        "expected_answer": question["expected_answer"],
        "key_points": json.dumps(question.get("key_points", [])),
        "student_answer": student_answer,
        "max_marks": max_marks,
    })

    result = parse_json_response(response.content)

    if not isinstance(result, dict):
        raise ValueError("OpenAI returned an invalid evaluation.")

    try:
        marks_awarded = float(result["marks_awarded"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "OpenAI returned invalid evaluation marks."
        ) from exc

    marks_awarded = max(0.0, min(float(max_marks), marks_awarded))

    result["marks_awarded"] = marks_awarded
    result["feedback"] = str(
        result.get("feedback", "No feedback provided.")
    )

    if not isinstance(result.get("strengths"), list):
        result["strengths"] = []

    if not isinstance(result.get("improvements"), list):
        result["improvements"] = []

    return result
