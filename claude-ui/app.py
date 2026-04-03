from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
DB_PATH = os.path.join(os.path.dirname(__file__), 'conversations.db')

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT 'New Chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/models', methods=['GET'])
def get_models():
    """Fetch available models from Ollama"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.ok:
            models = response.json().get('models', [])
            return jsonify([m['name'] for m in models])
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations ordered by most recent"""
    search = request.args.get('search', '').lower()

    conn = get_db_connection()
    c = conn.cursor()

    if search:
        c.execute('''
            SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at,
                   (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE LOWER(c.title) LIKE ? OR LOWER(m.content) LIKE ?
            ORDER BY c.updated_at DESC
        ''', (f'%{search}%', f'%{search}%'))
    else:
        c.execute('''
            SELECT id, title, created_at, updated_at,
                   (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as message_count
            FROM conversations
            ORDER BY updated_at DESC
        ''')

    conversations = c.fetchall()
    conn.close()

    return jsonify([
        {
            'id': c['id'],
            'title': c['title'],
            'created_at': c['created_at'],
            'updated_at': c['updated_at'],
            'message_count': c['message_count']
        }
        for c in conversations
    ])

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO conversations (title) VALUES (?)', ('New Chat',))
    conv_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': conv_id, 'title': 'New Chat'})

@app.route('/api/conversations/<int:conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    """Delete a conversation and its messages"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM conversations WHERE id = ?', (conv_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/conversations/<int:conv_id>/title', methods=['PUT'])
def update_title(conv_id):
    """Update conversation title"""
    data = request.json
    title = data.get('title', 'New Chat')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
              (title, conv_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/conversations/<int:conv_id>/messages', methods=['GET'])
def get_messages(conv_id):
    """Get all messages for a conversation"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, role, content, model, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at',
              (conv_id,))
    messages = c.fetchall()
    conn.close()

    return jsonify([
        {
            'id': m['id'],
            'role': m['role'],
            'content': m['content'],
            'model': m['model'],
            'created_at': m['created_at']
        }
        for m in messages
    ])

@app.route('/api/conversations/<int:conv_id>/messages', methods=['POST'])
def add_message(conv_id):
    """Add a message and get AI response"""
    data = request.json
    role = data.get('role')
    content = data.get('content')
    model = data.get('model', 'llama3.2')

    # Store user message
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO messages (conversation_id, role, content, model) VALUES (?, ?, ?, ?)',
              (conv_id, role, content, model))

    # Get conversation history
    c.execute('SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at',
              (conv_id,))
    messages = [{'role': m['role'], 'content': m['content']} for m in c.fetchall()]

    # Get AI response from Ollama
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                'model': model,
                'messages': messages,
                'stream': False
            },
            timeout=300
        )

        if response.ok:
            ai_response = response.json()['message']['content']
            c.execute('INSERT INTO messages (conversation_id, role, content, model) VALUES (?, ?, ?, ?)',
                      (conv_id, 'assistant', ai_response, model))

            # Update conversation timestamp
            c.execute('UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (conv_id,))

            # Auto-generate title from first user message if still default
            if len(messages) == 1:
                title = content[:50] + '...' if len(content) > 50 else content
                c.execute('UPDATE conversations SET title = ? WHERE id = ? AND title = ?',
                          (title, conv_id, 'New Chat'))

            conn.commit()
            conn.close()

            return jsonify({'content': ai_response})
        else:
            conn.close()
            return jsonify({'error': f'Ollama error: {response.status_code}'}), 500

    except requests.exceptions.ConnectionError:
        conn.close()
        return jsonify({
            'error': f'Cannot connect to Ollama at {OLLAMA_URL}. Is it running?'
        }), 500
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_conversations():
    """Search across all conversations"""
    data = request.json
    query = data.get('query', '').lower()

    if not query:
        return jsonify([])

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT DISTINCT c.id, c.title, m.content as matched_content, m.role
        FROM conversations c
        JOIN messages m ON c.id = m.conversation_id
        WHERE LOWER(c.title) LIKE ? OR LOWER(m.content) LIKE ?
        ORDER BY c.updated_at DESC
        LIMIT 20
    ''', (f'%{query}%', f'%{query}%'))

    results = c.fetchall()
    conn.close()

    return jsonify([
        {
            'id': r['id'],
            'title': r['title'],
            'matched_content': r['matched_content'][:200] + '...' if len(r['matched_content']) > 200 else r['matched_content'],
            'role': r['role']
        }
        for r in results
    ])

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if Ollama is reachable"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if response.ok:
            return jsonify({'status': 'connected', 'ollama_url': OLLAMA_URL})
        return jsonify({'status': 'error', 'message': 'Ollama returned error'}), 503
    except:
        return jsonify({'status': 'disconnected', 'ollama_url': OLLAMA_URL}), 503

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("Claude Chat UI - Local Edition")
    print("=" * 50)
    print(f"\nOllama URL: {OLLAMA_URL}")
    print("\nPrerequisites:")
    print("  1. Install Ollama: https://ollama.com")
    print("  2. Pull a model: ollama pull llama3.2")
    print("  3. Start Ollama: ollama serve")
    print("\n" + "=" * 50)
    print("Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
