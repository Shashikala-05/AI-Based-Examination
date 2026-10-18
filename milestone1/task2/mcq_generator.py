# ============================================================
# AI-BASED EXAMINATION PLATFORM
# Task 2: AI-Powered MCQ Generation
# ============================================================

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# ============================================================
# 1. LOAD API KEY
# Load the Gemini API key from the root .env file.
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env", override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing. Check your root .env file."
    )

# ============================================================
# 2. CREATE THE AI MODEL
# Initialize Gemini to generate examination questions.
# ============================================================

model = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.3,
)

# Use a prompt template to maintain a consistent MCQ format.
prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert examination question setter.
        Generate accurate multiple-choice questions.
        Follow the requested topic and difficulty.
        Each question must have exactly four options,
        exactly one correct answer, and a clear explanation.
        Return only valid JSON without Markdown code fences."""
    ),
    (
        "human",
        """Generate {number} MCQs about {topic}.
        Difficulty: {difficulty}.

        Return a JSON object with this structure:
        {{
          "questions": [
            {{
              "question": "Question text",
              "options": {{
                "A": "First option",
                "B": "Second option",
                "C": "Third option",
                "D": "Fourth option"
              }},
              "correct_answer": "A",
              "explanation": "Explanation of the correct answer"
            }}
          ]
        }}

        The correct_answer must be one of A, B, C, or D.
        Generate exactly the requested number of questions."""
    )
])

# Connect the prompt template to the Gemini model.
mcq_chain = prompt_template | model

# ============================================================
# 3. GENERATE MCQS
# Send the selected topic, difficulty, and question count
# to Gemini and convert its JSON response into Python data.
# ============================================================

def generate_mcqs(topic, difficulty, number):
    # Validate the input before making an API request.
    if not topic or not topic.strip():
        raise ValueError("Please enter a topic.")

    if difficulty not in ["Easy", "Medium", "Hard"]:
        raise ValueError("Select Easy, Medium, or Hard.")

    if not isinstance(number, int) or not 1 <= number <= 50:
        raise ValueError("Number of questions must be between 1 and 50.")

    # Generate the questions using the selected settings.
    response = mcq_chain.invoke({
        "topic": topic.strip(),
        "difficulty": difficulty,
        "number": number,
    })

    # Extract the response text.
    content = response.content

    if isinstance(content, list):
        content = "".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )

    # Parse the response as JSON.
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError(
            "The AI returned an invalid response. Please try again."
        ) from error

    questions = data.get("questions", [])

    # Check that the model generated the requested number of questions.
    if len(questions) != number:
        raise ValueError(
            f"Expected {number} questions, but received {len(questions)}. "
            "Please generate again."
        )

    # Check the structure of each question.
    for question in questions:
        if not isinstance(question.get("question"), str):
            raise ValueError("An MCQ is missing its question text.")

        options = question.get("options")

        if not isinstance(options, dict) or set(options.keys()) != {
            "A", "B", "C", "D"
        }:
            raise ValueError("Each MCQ must contain options A, B, C, and D.")

        if question.get("correct_answer") not in ["A", "B", "C", "D"]:
            raise ValueError("An MCQ has an invalid correct answer.")

        if not isinstance(question.get("explanation"), str):
            raise ValueError("An MCQ is missing its explanation.")

    return questions