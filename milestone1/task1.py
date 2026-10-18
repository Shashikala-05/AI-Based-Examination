# ============================================================
# AI-BASED INTELLIGENT EXAMINATION PLATFORM
# Task 1: OpenAI and Gemini Integration Using LangChain
# ============================================================

import os
from pathlib import Path

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


# ============================================================
# 1. LOAD API KEYS
# Load the OpenAI and Gemini API keys from the project's
# root .env file.
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Support either GOOGLE_API_KEY or GEMINI_API_KEY.
GEMINI_API_KEY = (
    os.getenv("GOOGLE_API_KEY")
    or os.getenv("GEMINI_API_KEY")
)

# Check whether the OpenAI API key is available.
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY is missing. Please check your .env file."
    )

# Check whether the Gemini API key is available.
if not GEMINI_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY or GEMINI_API_KEY is missing. "
        "Please check your .env file."
    )

# Display key availability without exposing the actual keys.
print("OpenAI API key loaded:", bool(OPENAI_API_KEY))
print("Gemini API key loaded:", bool(GEMINI_API_KEY))


# ============================================================
# 2. CONFIGURE THE AI MODELS
# Select the models that will generate the responses.
# ============================================================

OPENAI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-3.8-flash"


# ============================================================
# 3. CREATE THE COMMON PROMPT TEMPLATE
# Both models will receive the same question and instructions.
# ============================================================

prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful AI assistant. "
        "Answer accurately, clearly, and in simple language."
    ),
    ("human", "{question}")
])


# ============================================================
# 4. INITIALIZE THE OPENAI MODEL
# Use LangChain to connect to the OpenAI model.
# ============================================================

openai_chat = ChatOpenAI(
    model=OPENAI_MODEL,
    api_key=OPENAI_API_KEY,
    temperature=0.3,
)


# ============================================================
# 5. INITIALIZE THE GEMINI MODEL
# Use LangChain to connect to Google Gemini.
# ============================================================

gemini_chat = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GEMINI_API_KEY,
)


# ============================================================
# 6. CREATE THE LANGCHAIN CHAINS
# Connect the same prompt template to both AI models.
# Each chain generates its own answer to the same question.
# ============================================================

openai_chain = prompt_template | openai_chat

gemini_chain = prompt_template | gemini_chat


# ============================================================
# 7. FORMAT THE RESPONSE
# Display the generated answer as readable text.
# ============================================================

def print_response(content):
    """Print AI-generated content in a readable format."""

    if isinstance(content, str):
        print(content)

    elif isinstance(content, list):
        for item in content:

            if isinstance(item, str):
                print(item)

            elif isinstance(item, dict) and item.get("type") == "text":
                print(item.get("text", ""))

    else:
        print(content)


# ============================================================
# 8. GENERATE AN OPENAI RESPONSE
# Send the user's question to OpenAI and display its answer.
# ============================================================

def ask_openai(question):
    print("\n" + "=" * 65)
    print(f"OPENAI RESPONSE ({OPENAI_MODEL})")
    print("=" * 65)

    try:
        response = openai_chain.invoke({
            "question": question
        })

        print_response(response.content)

    except Exception as error:
        print("OpenAI request failed:", error)


# ============================================================
# 9. GENERATE A GEMINI RESPONSE
# Send the same question to Gemini and display its answer.
# ============================================================

def ask_gemini(question):
    print("\n" + "=" * 65)
    print(f"GOOGLE GEMINI RESPONSE ({GEMINI_MODEL})")
    print("=" * 65)

    try:
        response = gemini_chain.invoke({
            "question": question
        })

        print_response(response.content)

    except Exception as error:
        print("Gemini request failed:", error)


# ============================================================
# 10. GENERATE RESPONSES FROM BOTH MODELS
# Call both models using the same question.
# Each model responds independently.
# ============================================================

def ask_both_models(question):

    # Generate and display the OpenAI response.
    ask_openai(question)

    # Generate and display the Gemini response.
    ask_gemini(question)

    print("\n" + "=" * 65)
    print("BOTH MODEL REQUESTS COMPLETED")
    print("=" * 65)


# ============================================================
# 11. MAIN PROGRAM
# Allow the user to enter multiple prompts.
# Type 'exit' to close the program.
# ============================================================

def main():

    print("\nAI-BASED INTELLIGENT EXAMINATION PLATFORM")
    print("-" * 65)

    print("Framework: LangChain")
    print("AI Providers: OpenAI and Google Gemini")

    print("\nOpenAI Model:", OPENAI_MODEL)
    print("Gemini Model:", GEMINI_MODEL)

    print("\nEnter a prompt to receive answers from both AI models.")
    print("Type 'exit' to stop the program.")

    while True:

        try:
            question = input("\nEnter your prompt: ").strip()

            # Stop the program when the user enters 'exit'.
            if question.lower() == "exit":
                print("Program closed. Goodbye!")
                break

            # Check whether the user entered an empty prompt.
            if not question:
                print("Please enter a prompt.")
                continue

            # Send the same question to both AI models.
            ask_both_models(question)

        except KeyboardInterrupt:
            print("\nProgram stopped.")
            break


# ============================================================
# 12. PROGRAM ENTRY POINT
# Run the main function when task1.py is executed directly.
# ============================================================

if __name__ == "__main__":
    main()