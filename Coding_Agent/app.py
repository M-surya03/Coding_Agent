from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
import json

# --- Load environment variables ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

# --- Configure Gemini API ---
genai.configure(api_key=api_key)

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

# --- Select Gemini Model ---
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",  # or "gemini-1.5-pro"
    system_instruction=(
        "You are a programming assistant chatbot. Only respond to programming-related queries. "
        "Give clear, concise explanations with code examples when needed. "
        "Format code using proper markdown code blocks with language specification. "
        "If a question is not related to programming, politely say you can only help with coding topics. "
        "Keep responses conversational and helpful for beginners."
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

# --- Global chat session ---
chat_session = model.start_chat()

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
    return filepath

# --- Extract code and language from triple-backtick blocks ---
def extract_code_and_language(response_text):
    saved_files = []
    code_blocks = re.findall(r"```(\w+)?\n(.*?)```", response_text, re.DOTALL)
    if code_blocks:
        for lang, code in code_blocks:
            if code.strip():
                filepath = save_code(code, lang if lang else 'python')
                saved_files.append({
                    'language': lang if lang else 'python',
                    'filepath': filepath,
                    'filename': os.path.basename(filepath)
                })
    return saved_files

# --- Routes ---
@app.route('/')
def index():
    """Serve the main chatbot page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages from frontend"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Send message to Gemini
        response = chat_session.send_message(user_message)
        bot_reply = response.text.strip()
        
        # Extract and save any code blocks
        saved_files = extract_code_and_language(bot_reply)
        
        # Format response for frontend
        return jsonify({
            'response': bot_reply,
            'saved_files': saved_files,
            'success': True
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': 'Sorry, I encountered an error processing your request.',
            'success': False
        }), 500

@app.route('/api/saved-codes')
def list_saved_codes():
    """List all saved code files"""
    try:
        folder = "saved_codes"
        if not os.path.exists(folder):
            return jsonify({'files': []})
        
        files = []
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                # Get file extension to determine language
                ext = os.path.splitext(filename)[1]
                lang = next((k for k, v in EXTENSIONS.items() if v == ext), 'text')
                
                files.append({
                    'filename': filename,
                    'language': lang,
                    'size': os.path.getsize(filepath)
                })
        
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/<filename>')
def get_code_file(filename):
    """Get content of a specific saved code file"""
    try:
        folder = "saved_codes"
        filepath = os.path.join(folder, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'filename': filename,
            'content': content,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Coding Assistant API is running'})

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# --- Run App ---
if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('saved_codes', exist_ok=True)
    
    print("🚀 Starting Coding Assistant Flask App...")
    print("📁 Make sure to put your HTML file in the 'templates' folder as 'index.html'")
    print("🔑 Make sure your .env file contains GOOGLE_API_KEY")
    
    app.run(debug=True, host='0.0.0.0', port=5000)