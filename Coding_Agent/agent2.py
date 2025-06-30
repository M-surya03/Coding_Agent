import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

# --- Load environment variables ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

# --- Configure Gemini API ---
genai.configure(api_key=api_key)

# --- Select Gemini Model ---
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",  # or "gemini-1.5-pro"
    system_instruction=(
        "You are a programming assistant. Only respond to programming-related queries. "
        "Suggest to do you want an output and then ask provide the output of that program."
        "Give clear explanations, code examples in proper code blocks, and avoid any non-programming topics. "
        "If a question is not related to programming, politely say you can only help with code."
    )
)

# --- Language to File Extension Map ---
EXTENSIONS = {
    'python': '.py',
    'c': '.c',
    'cpp': '.cpp',
    'java': '.java',
    'javascript': '.js',
    'html': '.html',
    'css': '.css',
    'bash': '.sh',
    'go': '.go',
    'ruby': '.rb'
}

# --- Save code into a unique file in ./saved_codes/ folder ---
def save_code(code: str, lang: str = 'python'):
    ext = EXTENSIONS.get(lang.lower(), '.txt')
    
    # Ensure the folder exists
    folder = "saved_codes"
    os.makedirs(folder, exist_ok=True)

    # Generate unique filename
    base_name = "output"
    counter = 1
    while True:
        filename = f"{base_name}_{counter}{ext}"
        filepath = os.path.join(folder, filename)
        if not os.path.exists(filepath):
            break
        counter += 1

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code.strip())
    print(f"💾 Code saved to {filepath}")

# --- Extract code and language from triple-backtick blocks ---
def extract_code_and_language(response_text):
    code_blocks = re.findall(r"```(\w+)?\n(.*?)```", response_text, re.DOTALL)
    if code_blocks:
        for lang, code in code_blocks:
            if code:
                save_code(code, lang if lang else 'python')
    else:
        print("⚠️ No code block detected to save.")

# --- Chat Loop ---
def chat_loop():
    print("👨‍💻 Gemini Programming Assistant is ready! Type 'exit' to quit.\n")
    chat = model.start_chat()
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        response = chat.send_message(user_input)
        reply = response.text.strip()
        print(f"\n🤖 Assistant:\n{reply}\n")
        extract_code_and_language(reply)

# --- Entry Point ---
if __name__ == "__main__":
    try:
        chat_loop()
    except KeyboardInterrupt:
        print("\n🔌 Exiting...")
