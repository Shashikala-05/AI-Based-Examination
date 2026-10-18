# ============================================================
# TASK 5: OPENAI / LANGCHAIN LOGIC
# ============================================================
# This file contains the functions used by app.py:
#   1. Load the API key from .env.
#   2. Generate Part-A MCQs.
#   3. Generate Part-B written questions and model answers.
#   4. Extract visible text from an uploaded answer image using gpt-4o.
#   5. Evaluate written answers using gpt-4o-mini.
#
# Keep this file in the same folder as app.py.

import os
import json
import re
import base64
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


# ------------------------------------------------------------
# 1. LOAD THE API KEY
# ------------------------------------------------------------

# exam_generator.py is expected in milestone1/task5.
# parents[2] moves up to the main AI-Based Examination folder.
BASE_DIR = Path(__file__).resolve().parents[2]

# Load variables from the .env file in the project root.
load_dotenv(BASE_DIR / ".env", override=True)

API_KEY = os.getenv("OPENAI_API_KEY")

# Stop early with a clear message if the key is missing.
if not API_KEY:
    raise ValueError(
        "OPENAI_API_KEY is missing from the project-root .env file."
    )


# ------------------------------------------------------------
# 2. INITIALIZE THE TWO OPENAI MODELS
# ------------------------------------------------------------

# gpt-4o can accept image input, so it is used to extract text from images.
# VISION_MODEL lets you change the model name through the .env file if needed.
vision_model = ChatOpenAI(
    model=os.getenv("VISION_MODEL", "gpt-4o"),
    api_key=API_KEY,
    temperature=0,  # Lower temperature encourages consistent text extraction.
)

# gpt-4o-mini is used for text-based question generation and grading.
text_model = ChatOpenAI(
    model=os.getenv("TEXT_MODEL", "gpt-4o-mini"),
    api_key=API_KEY,
    temperature=0.2,
)


# ------------------------------------------------------------
# 3. HELPER: PARSE JSON RETURNED BY THE MODEL
# ------------------------------------------------------------

def parse_json(content):
    """Convert the model's JSON text into a Python dictionary/list."""

    # Depending on the response, content may contain multiple text blocks.
    if isinstance(content, list):
        content = "".join(
            str(item.get("text", "")) if isinstance(item, dict) else str(item)
            for item in content
        )

    # Remove optional Markdown fences such as ```json ... ```.
    # The pattern uses \s to match whitespace characters.
    content = re.sub(
        r"^\s*```(?:json)?\s*|\s*```\s*$",
        "",
        str(content).strip(),
        flags=re.IGNORECASE,
    ).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        # Clear error if the response is not valid JSON.
        raise ValueError(
            "The model returned invalid JSON. Please retry."
        ) from exc


# ------------------------------------------------------------
# 4. HELPER: VALIDATE EXAM SETTINGS
# ------------------------------------------------------------

def validate(topic, difficulty):
    """Check topic and difficulty before calling the API."""

    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Please enter an examination topic.")

    if difficulty not in ("Easy", "Medium", "Hard"):
        raise ValueError("Difficulty must be Easy, Medium, or Hard.")


# ------------------------------------------------------------
# 5. OCR: EXTRACT TEXT FROM A STUDENT'S ANSWER IMAGE
# ------------------------------------------------------------

def extract_text_from_image(uploaded_file):
    """
    Read text from an uploaded image using gpt-4o vision.

    The function returns plain text. app.py places that text into an editable
    text box so the student can correct OCR mistakes before grading.
    """

    if uploaded_file is None:
        raise ValueError("Upload an image first.")

    # Pillow opens the uploaded image and converts it to standard RGB format.
    try:
        image = Image.open(uploaded_file).convert("RGB")
    except Exception as exc:
        raise ValueError(
            "Invalid image. Upload PNG, JPG, JPEG, or WEBP."
        ) from exc

    # Resize very large images to keep the request manageable.
    # The image keeps its aspect ratio.
    image.thumbnail((2400, 2400))

    # Convert the image to JPEG bytes.
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=92)

    # OpenAI's image input can be supplied as a base64 data URL.
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    image_data_url = f"data:image/jpeg;base64,{encoded}"

    # Ask the vision model to transcribe only what is visible.
    # It should not fix the student's answer or invent missing words.
    response = vision_model.invoke([
        (
            "system",
            """You are an accurate OCR assistant for student answer sheets.
Extract only visible text. Preserve wording, spelling, paragraphs and lists.
Do not correct, summarize, answer, or add information. Mark unreadable text [unclear].
Return only the extracted text."""
        ),
        (
            "human",
            [
                {
                    "type": "text",
                    "text": "Extract the student's answer text from this image."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_url},
                },
            ],
        ),
    ])

    # Convert the model response to a normal string.
    content = response.content
    if isinstance(content, list):
        content = "\n".join(
            str(item.get("text", ""))
            for item in content
            if isinstance(item, dict)
        )

    extracted_text = str(content).strip()

    if not extracted_text:
        raise ValueError("No readable text was found in the image.")

    return extracted_text


# ------------------------------------------------------------
# 6. PART-A: PROMPT AND CHAIN FOR MCQ GENERATION
# ------------------------------------------------------------

# ChatPromptTemplate separates the instructions from the changing exam settings.
# The doubled braces {{ }} are needed because the prompt itself contains JSON braces.
mcq_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """Generate multiple-choice questions for the topic and difficulty.
Return ONLY JSON:
{{
 "questions":[{{"question":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},
 "correct_answer":"A","explanation":"..."}}]
}}
Generate exactly the requested count. Four non-empty options per question, one correct
answer only, correct_answer must be A/B/C/D, no duplicates, accurate explanations.
Return JSON only."""
    ),
    (
        "human",
        "Topic: {topic}\nDifficulty: {difficulty}\nCount: {number}"
    )
])

# The pipe operator connects the prompt to the OpenAI model.
mcq_chain = mcq_prompt | text_model


# ------------------------------------------------------------
# 7. PART-A: GENERATE AND VALIDATE MCQs
# ------------------------------------------------------------

def generate_mcqs(topic, difficulty, number):
    """Return a list of MCQs with options, correct answer, and explanation."""

    validate(topic, difficulty)

    if not isinstance(number, int) or not 1 <= number <= 30:
        raise ValueError("MCQ count must be between 1 and 30.")

    # Send the selected settings to the prompt and model.
    response = mcq_chain.invoke({
        "topic": topic.strip(),
        "difficulty": difficulty,
        "number": number
    })

    # Turn the model's JSON response into Python data.
    data = parse_json(response.content)
    questions = data.get("questions") if isinstance(data, dict) else None

    # Ensure the model generated exactly the requested number of questions.
    if not isinstance(questions, list) or len(questions) != number:
        raise ValueError(
            "OpenAI returned an unexpected number of MCQs."
        )

    # Validate every question before showing it in the interface.
    for i, question in enumerate(questions, 1):
        if not isinstance(question, dict) or not str(
            question.get("question", "")
        ).strip():
            raise ValueError(f"MCQ {i} is invalid.")

        options = question.get("options")
        if not isinstance(options, dict):
            raise ValueError(f"MCQ {i} has invalid options.")

        # Keep only the expected A/B/C/D options and trim extra spaces.
        question["options"] = {
            letter: str(options.get(letter, "")).strip()
            for letter in "ABCD"
        }

        if not all(question["options"].values()):
            raise ValueError(f"MCQ {i} needs four non-empty options.")

        # Normalize the correct answer to uppercase for reliable comparison.
        question["correct_answer"] = str(
            question.get("correct_answer", "")
        ).strip().upper()

        if (
            question["correct_answer"] not in "ABCD"
            or len(question["correct_answer"]) != 1
        ):
            raise ValueError(f"MCQ {i} has an invalid correct answer.")

        question["explanation"] = str(
            question.get("explanation", "No explanation provided.")
        )

    return questions


# ------------------------------------------------------------
# 8. PART-B: PROMPT AND CHAIN FOR WRITTEN QUESTIONS
# ------------------------------------------------------------

# Each written question includes a model answer and key points.
# The model answer is displayed to the student after submission.
written_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """Generate written questions and accurate model answers.
Return ONLY JSON:
{{
 "questions":[{{"question":"...","expected_answer":"...","max_marks":5,
 "key_points":["point one","point two"]}}]
}}
Generate exactly the requested count. Avoid duplicates, match difficulty, provide useful
key points, and return valid JSON only."""
    ),
    (
        "human",
        "Topic: {topic}\nDifficulty: {difficulty}\nCount: {number}\nMarks each: {marks}"
    )
])

written_chain = written_prompt | text_model


# ------------------------------------------------------------
# 9. PART-B: GENERATE AND VALIDATE WRITTEN QUESTIONS
# ------------------------------------------------------------

def generate_written_questions(topic, difficulty, number, marks_per_question):
    """Create written questions, model answers, key points, and marks."""

    validate(topic, difficulty)

    if not isinstance(number, int) or not 1 <= number <= 20:
        raise ValueError("Written question count must be between 1 and 20.")

    if not isinstance(marks_per_question, int) or not 1 <= marks_per_question <= 20:
        raise ValueError("Marks per written question must be between 1 and 20.")

    # Ask the model to generate the requested number of written questions.
    response = written_chain.invoke({
        "topic": topic.strip(),
        "difficulty": difficulty,
        "number": number,
        "marks": marks_per_question
    })

    data = parse_json(response.content)
    questions = data.get("questions") if isinstance(data, dict) else None

    if not isinstance(questions, list) or len(questions) != number:
        raise ValueError(
            "OpenAI returned an unexpected number of written questions."
        )

    # Validate the question and expected answer, then normalize the fields.
    for i, question in enumerate(questions, 1):
        if not isinstance(question, dict) or not str(
            question.get("question", "")
        ).strip():
            raise ValueError(f"Written question {i} is invalid.")

        if not str(question.get("expected_answer", "")).strip():
            raise ValueError(f"Written question {i} has no model answer.")

        points = question.get("key_points", [])
        question["key_points"] = (
            [str(point) for point in points]
            if isinstance(points, list)
            else []
        )

        # Use the marks selected by the user rather than trusting the model's value.
        question["max_marks"] = marks_per_question

    return questions


# ------------------------------------------------------------
# 10. PART-B: PROMPT AND CHAIN FOR ANSWER EVALUATION
# ------------------------------------------------------------

# The evaluator compares the student's answer with the model answer and key points.
# It can award partial marks when an answer is partly correct.
evaluation_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """Evaluate a student's answer fairly against the question, model answer,
and key points. Accept correct alternative wording and award partial marks. Blank or
incorrect answers get zero. Never exceed maximum marks.
Return ONLY JSON:
{{"marks_awarded":3,"feedback":"...","strengths":["..."],"improvements":["..."]}}"""
    ),
    (
        "human",
        """Topic: {topic}
Difficulty: {difficulty}
Question: {question}
Model answer: {expected_answer}
Key points: {key_points}
Student answer: {student_answer}
Maximum marks: {max_marks}
Evaluate and return JSON."""
    )
])

evaluation_chain = evaluation_prompt | text_model


# ------------------------------------------------------------
# 11. PART-B: EVALUATE ONE WRITTEN ANSWER
# ------------------------------------------------------------

def evaluate_written_answer(topic, difficulty, question, student_answer):
    """
    Return the marks, feedback, strengths, and improvements for one answer.
    The answer passed here is the text box content, including any OCR edits.
    """

    maximum = int(question["max_marks"])
    answer = (student_answer or "").strip()

    # Do not spend an API call on a blank answer.
    if not answer:
        return {
            "marks_awarded": 0,
            "feedback": "No answer was provided.",
            "strengths": [],
            "improvements": ["Attempt the question."]
        }

    # Send the question, model answer, key points, and student answer to the evaluator.
    response = evaluation_chain.invoke({
        "topic": topic,
        "difficulty": difficulty,
        "question": question["question"],
        "expected_answer": question["expected_answer"],
        "key_points": json.dumps(question.get("key_points", [])),
        "student_answer": answer,
        "max_marks": maximum
    })

    result = parse_json(response.content)

    if not isinstance(result, dict):
        raise ValueError("OpenAI returned an invalid evaluation.")

    # Ensure the model returned a numeric mark.
    try:
        marks = float(result["marks_awarded"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "OpenAI returned invalid evaluation marks."
        ) from exc

    # Clamp marks to the range 0..maximum, even if the model returns a bad value.
    result["marks_awarded"] = max(
        0.0,
        min(float(maximum), marks)
    )

    # Ensure these fields always have usable values for the results page.
    result["feedback"] = str(
        result.get("feedback", "No feedback provided.")
    )

    if not isinstance(result.get("strengths"), list):
        result["strengths"] = []

    if not isinstance(result.get("improvements"), list):
        result["improvements"] = []

    return result
