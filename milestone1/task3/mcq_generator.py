import os
import json
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


# ==========================================
# 1. LOAD OPENAI API KEY
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env", override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found. Check your project's .env file."
    )


# ==========================================
# 2. INITIALIZE OPENAI MODEL
# ==========================================

model = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=OPENAI_API_KEY,
    temperature=0.3,
)


# ==========================================
# 3. CREATE THE MCQ PROMPT
# ==========================================

prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are an experienced teacher and examination question creator.

        Generate multiple-choice examination questions based on the
        topic, difficulty level, and number requested by the user.

        Return the result as valid JSON in this structure:

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
                    "explanation": "Explain why this answer is correct."
                }}
            ]
        }}

        Instructions:
        1. Generate exactly the requested number of questions.
        2. Each question must have four options: A, B, C, and D.
        3. Only one option should be correct.
        4. The correct_answer must contain only A, B, C, or D.
        5. Provide a clear and educational explanation.
        6. Match the selected difficulty level.
        7. Avoid duplicate questions.
        8. Ensure the questions and answer key are factually accurate.
        9. Return only valid JSON, without Markdown code fences.
        """
    ),
    (
        "human",
        """
        Generate an examination using these details:

        Topic: {topic}
        Difficulty: {difficulty}
        Number of questions: {number}
        """
    )
])

mcq_chain = prompt_template | model


# ==========================================
# 4. GENERATE QUESTIONS USING OPENAI
# ==========================================

def generate_mcqs(topic, difficulty, number):

    # Validate the user's input
    if not topic or not topic.strip():
        raise ValueError("Please enter a topic.")

    if difficulty not in ["Easy", "Medium", "Hard"]:
        raise ValueError(
            "Difficulty must be Easy, Medium, or Hard."
        )

    if not isinstance(number, int) or not 1 <= number <= 50:
        raise ValueError(
            "Number of questions must be between 1 and 50."
        )

    # Send the request to OpenAI through LangChain
    response = mcq_chain.invoke({
        "topic": topic.strip(),
        "difficulty": difficulty,
        "number": number
    })

    content = response.content

    # Handle responses containing multiple content blocks
    if isinstance(content, list):
        content = "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict)
        )

    content = str(content).strip()

    # Remove Markdown code fences if present
    content = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        content,
        flags=re.IGNORECASE
    ).strip()

    # Convert the JSON response into Python data
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "OpenAI returned an invalid response. Please try again."
        ) from exc

    questions = data.get("questions")

    if not isinstance(questions, list):
        raise ValueError(
            "OpenAI did not return a valid list of questions."
        )

    if len(questions) != number:
        raise ValueError(
            f"Requested {number} questions, but OpenAI returned "
            f"{len(questions)}. Please generate the test again."
        )

    # Validate each generated question
    for index, question in enumerate(questions, start=1):

        if not isinstance(question, dict):
            raise ValueError(
                f"Question {index} has an invalid format."
            )

        if not str(question.get("question", "")).strip():
            raise ValueError(
                f"Question {index} is missing its question text."
            )

        options = question.get("options")

        if not isinstance(options, dict):
            raise ValueError(
                f"Question {index} has invalid options."
            )

        required_options = ["A", "B", "C", "D"]

        for option in required_options:
            if not str(options.get(option, "")).strip():
                raise ValueError(
                    f"Question {index} is missing option {option}."
                )

        correct_answer = str(
            question.get("correct_answer", "")
        ).strip().upper()

        if correct_answer not in required_options:
            raise ValueError(
                f"Question {index} has an invalid correct answer."
            )

        # Standardize the returned data
        question["question"] = str(
            question["question"]
        ).strip()

        question["options"] = {
            option: str(options[option]).strip()
            for option in required_options
        }

        question["correct_answer"] = correct_answer

        question["explanation"] = str(
            question.get(
                "explanation",
                "No explanation was provided."
            )
        ).strip()

    return questions