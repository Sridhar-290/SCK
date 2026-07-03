from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3
import string
import json
import io

# PDF library compatibility: we perform dynamic imports at runtime inside the
# extraction helper to avoid static import-time errors and to keep Pylance from
# reporting unresolved top-level imports when packages aren't installed.
PdfReader = None


def _extract_text_from_pdf_file(fileobj):
    """Return the extracted text from a PDF file-like object as a single string.
    Tries `pypdf`/`PyPDF2` first; if unavailable, falls back to `pdfminer.six` if
    installed. Raises ImportError if no backend is available.
    """
    # Try pypdf or PyPDF2 dynamically (avoid static imports so Pylance doesn't
    # report missing imports when packages are not installed).
    import importlib
    for candidate in ('pypdf', 'PyPDF2'):
        try:
            mod = importlib.import_module(candidate)
            # both provide PdfReader class
            PdfReaderCls = getattr(mod, 'PdfReader', None)
            if PdfReaderCls is None:
                # older PyPDF2 versions used PdfFileReader
                PdfReaderCls = getattr(mod, 'PdfFileReader', None)
            if PdfReaderCls is None:
                continue

            # Create reader: many libraries accept a file-like object; ensure
            # we pass either the file or a BytesIO of its contents.
            data = None
            try:
                data = fileobj.read()
                try:
                    fileobj.seek(0)
                except Exception:
                    pass
            except Exception:
                try:
                    data = fileobj.stream.read()
                except Exception:
                    data = None

            if data is not None:
                import io as _io
                reader = PdfReaderCls(_io.BytesIO(data))
            else:
                reader = PdfReaderCls(fileobj)

            text = ""
            # iterate pages — support both .pages and getPage/getNumPages
            if hasattr(reader, 'pages'):
                for page in reader.pages:
                    try:
                        t = page.extract_text()
                    except Exception:
                        # older PyPDF2 had extractText()
                        try:
                            t = page.extractText()
                        except Exception:
                            t = None
                    if t:
                        text += t + " "
            else:
                # fallback for PdfFileReader
                try:
                    num = reader.getNumPages()
                    for i in range(num):
                        p = reader.getPage(i)
                        try:
                            t = p.extract_text()
                        except Exception:
                            try:
                                t = p.extractText()
                            except Exception:
                                t = None
                        if t:
                            text += t + " "
                except Exception:
                    # give up on this backend
                    continue

            return text
        except Exception:
            # try next candidate
            continue

    # Fallback: pdfminer.six
    try:
        from pdfminer.high_level import extract_text
    except Exception:
        raise ImportError('No PDF backend available')

    # Read bytes from incoming file-like and pass BytesIO to pdfminer
    data = None
    try:
        data = fileobj.read()
        try:
            fileobj.seek(0)
        except Exception:
            pass
    except Exception:
        try:
            data = fileobj.stream.read()
        except Exception:
            data = None

    if data is None:
        raise ImportError('No PDF data')

    import io as _io
    return extract_text(_io.BytesIO(data))



app = Flask(__name__)
app.secret_key = 'super_secret_key_for_demo_only' # Change this in production
DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- Authentication Decorator ---
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/')
@login_required
def index():
    return render_template('index.html', user_email=session.get('email'))

@app.route('/login', methods=['GET'])
def login_page():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def login_api():
    data = request.get_json()
    email = data.get('email')
    full_name = data.get('full_name')
    action = data.get('action') # 'login' or 'register'

    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    if action == 'register' and not full_name:
        return jsonify({'error': 'Full Name is required for registration'}), 400

    conn = get_db_connection()
    
    if action == 'register':
        try:
            conn.execute('INSERT INTO users (email, full_name) VALUES (?, ?)', (email, full_name))
            conn.commit()
            user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            is_admin = 0
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'User already exists. Please login.'}), 409
    else: # Login
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if not user:
            conn.close()
            return jsonify({'error': 'User not found. Please register first.'}), 401
        user_id = user['id']
        is_admin = user['is_admin']

    conn.close()
    
    session['user_id'] = user_id
    session['email'] = email
    session['is_admin'] = is_admin
    
    redirect_url = url_for('admin_dashboard') if session.get('is_admin') == 1 else url_for('index')
    return jsonify({'message': 'Success', 'redirect': redirect_url})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if session.get('is_admin') != 1:
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    # Fetch all assessments with user details
    query = '''
        SELECT 
            u.email, 
            u.full_name, 
            a.role_name, 
            a.score, 
            a.timestamp 
        FROM assessments a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.timestamp DESC
    '''
    rows = conn.execute(query).fetchall()
    all_records = [dict(row) for row in rows]
    
    users_count = conn.execute('SELECT count(*) FROM users').fetchone()[0]
    total_evals = conn.execute('SELECT count(*) FROM assessments').fetchone()[0]
    
    conn.close()
    
    return render_template('admin.html', 
                          records=all_records, 
                          users_count=users_count, 
                          total_evals=total_evals,
                          user_email=session.get('email'))


@app.route('/roles', methods=['GET'])
@login_required
def get_roles():
    conn = get_db_connection()
    roles = conn.execute('SELECT id, name FROM job_roles').fetchall()
    conn.close()
    return jsonify([dict(role) for role in roles])

@app.route('/history', methods=['GET'])
@login_required
def get_history():
    conn = get_db_connection()
    history = conn.execute('''
        SELECT id, role_name, score, timestamp, result_json 
        FROM assessments 
        WHERE user_id = ? 
        ORDER BY timestamp DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    # Parse the JSON string back to object for the frontend if needed, 
    # or just send the relevant summary fields
    return jsonify([{
        'id': row['id'],
        'role_name': row['role_name'],
        'score': row['score'],
        'timestamp': row['timestamp'],
        'result': json.loads(row['result_json']) if row['result_json'] else {}
    } for row in history])

@app.route('/evaluate', methods=['POST'])
@login_required
def evaluate():
    resume_text = ""
    job_role_id = None

    # Handle Multipart/Form-Data (File Upload)
    if 'resume_file' in request.files:
        file = request.files['resume_file']
        job_role_id = request.form.get('job_role_id')
        
        if file and file.filename.endswith('.pdf'):
            try:
                try:
                    resume_text += _extract_text_from_pdf_file(file)
                except ImportError:
                    return jsonify({"error": "PDF support not available (pypdf, PyPDF2 or pdfminer not installed)."}), 500
                except Exception as e:
                    return jsonify({"error": f"Error reading PDF: {str(e)}"}), 400
            except Exception as e:
                return jsonify({"error": f"Error reading PDF: {str(e)}"}), 400
    
    # Handle JSON or Form Data fallback for raw text
    else:
        # Check if it was sent as form data but no file
        if request.form.get('resume_text'):
            resume_text = request.form.get('resume_text')
            job_role_id = request.form.get('job_role_id')
        else:
            # Check JSON
            data = request.get_json(silent=True)
            if data:
                resume_text = data.get('resume_text', '')
                job_role_id = data.get('job_role_id')

    if not resume_text or not job_role_id:
        return jsonify({"error": "Missing resume content or job_role_id"}), 400

    clean_text = resume_text.lower()
    clean_text = clean_text.translate(str.maketrans('', '', string.punctuation))
    
    conn = get_db_connection()
    keywords = conn.execute('SELECT keyword, importance FROM keywords WHERE job_role_id = ?', (job_role_id,)).fetchall()
    role_info = conn.execute('SELECT name FROM job_roles WHERE id = ?', (job_role_id,)).fetchone()
    role_name = role_info['name'] if role_info else "Unknown Role"

    total_possible = 0
    total_matched = 0
    matched_keywords = []
    missing_keywords = []

    for kw in keywords:
        kw_text = kw['keyword'].lower()
        importance = kw['importance']
        total_possible += importance
        
        if kw_text in clean_text:
            total_matched += importance
            matched_keywords.append(kw['keyword'])
        else:
            missing_keywords.append(kw['keyword'])

    score = round((total_matched / total_possible) * 100) if total_possible > 0 else 0
    
    if score == 100:
        suggestion = f"Excellent! Your resume perfectly matches user requirements for {role_name}."
    elif score > 70:
        suggestion = f"Your resume matches well, but consider adding: {', '.join(missing_keywords[:3])}."
    elif score > 40:
        suggestion = f"Good start, but you are missing some key skills: {', '.join(missing_keywords[:3])}."
    else:
        suggestion = f"Consider highlighting more relevant skills like {', '.join(missing_keywords[:3])} to improve your match."

    result_data = {
        "score": score,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "suggestions": suggestion,
        "resume_preview": resume_text[:200] + "..." # Optional preview
    }

    # Save to history
    conn.execute('''
        INSERT INTO assessments (user_id, job_role_id, role_name, resume_text, score, result_json)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session['user_id'], job_role_id, role_name, resume_text, score, json.dumps(result_data)))
    conn.commit()
    conn.close()

    return jsonify(result_data)

# --- AI Agent Logic (Mocking intelligent extraction with a large keyword DB) ---
# In a real scenario, this would use NLP (Spacy/NLTK) or an LLM API.
SKILLS_DB = {
    'python', 'java', 'javascript', 'c++', 'c#', 'react', 'angular', 'vue', 'node.js', 'django', 'flask',
    'spring', 'hibernate', 'sql', 'mysql', 'postgresql', 'mongodb', 'aws', 'azure', 'gcp', 'docker',
    'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'ci/cd', 'linux', 'bash', 'shell', 'html', 'css',
    'typescript', 'go', 'rust', 'swift', 'kotlin', 'flutter', 'dart', 'tensorflow', 'pytorch', 'pandas',
    'numpy', 'scikit-learn', 'keras', 'hadoop', 'spark', 'kafka', 'tableau', 'power bi', 'excel', 'word',
    'powerpoint', 'jira', 'confluence', 'agile', 'scrum', 'kanban', 'devops', 'machine learning', 'ai',
    'deep learning', 'nlp', 'computervision', 'cybersecurity', 'network', 'firewall', 'tcp/ip', 'dns',
    'http', 'rest', 'graphql', 'soap', 'json', 'xml', 'redis', 'elasticsearch', 'rabbitmq', 'terraform',
    'ansible', 'chef', 'puppet', 'selenium', 'cypress', 'jest', 'mocha', 'junit', 'nunit', 'xunit'
}

@app.route('/analyze_jd', methods=['POST'])
@login_required
def analyze_jd():
    resume_text = ""
    jd_text = ""

    # Handle Multipart/Form-Data (File Upload)
    if 'resume_file' in request.files:
        file = request.files['resume_file']
        jd_text = request.form.get('jd_text', '').lower()
        if file and file.filename.endswith('.pdf'):
            try:
                resume_text += _extract_text_from_pdf_file(file)
                resume_text = resume_text.lower()
            except ImportError:
                return jsonify({"error": "PDF support not available (pypdf, PyPDF2 or pdfminer not installed)."}), 500
            except Exception as e:
                return jsonify({"error": f"Error reading PDF: {str(e)}"}), 400
        
        # Fallback to text input if file logic fails or no file actually selected but form sent
        if not resume_text and request.form.get('resume_text'):
             resume_text = request.form.get('resume_text', '').lower()
             
    else:
        # Handle JSON
        data = request.get_json(silent=True)
        if data:
            resume_text = data.get('resume_text', '').lower()
            jd_text = data.get('jd_text', '').lower()

    if not resume_text or not jd_text:
        return jsonify({'error': 'Both Resume and Job Description are required.'}), 400

    # Clean texts
    resume_clean = resume_text.translate(str.maketrans('', '', string.punctuation))
    jd_clean = jd_text.translate(str.maketrans('', '', string.punctuation))

    # Extract required skills from JD
    # We look for words in JD that exist in our SKILLS_DB
    found_requirements = set()
    for word in jd_clean.split():
        if word in SKILLS_DB:
            found_requirements.add(word)
    
    # Also check for multi-word skills (simple check)
    multi_word_skills = ['machine learning', 'deep learning', 'data analysis', 'artificial intelligence', 
                         'cloud computing', 'project management', 'communication skills']
    for skill in multi_word_skills:
        if skill in jd_clean:
            found_requirements.add(skill)

    if not found_requirements:
        return jsonify({
            'error': 'Could not identify technical skills in the Job Description. Please ensure it is detailed.'
        }), 200

    # Check matches
    matched = []
    missing = []
    
    for skill in found_requirements:
        if skill in resume_clean:
            matched.append(skill)
        else:
            missing.append(skill)

    # Convert to list for JSON
    matched = list(matched)
    missing = list(missing)

    score = round((len(matched) / len(found_requirements)) * 100)
    
    # Generate Agent Insight
    insight = ""
    if score > 80:
        insight = "Excellent fit! You possess most of the required skills. Focus on interview prep."
        lagging = "None significant."
    elif score > 50:
        insight = "Good potential. You have a solid base but need to bridge some gaps."
        lagging = f"Critical missing skills: {', '.join(missing[:5])}."
    else:
        insight = "Significant gap. This role might be a stretch without upskilling."
        lagging = f"Priority learning areas: {', '.join(missing[:5])}."
        
    return jsonify({
        'score': score,
        'matched': matched,
        'missing': missing,
        'insight': insight,
        'lagging': lagging,
        'total_requirements': len(found_requirements)
    })

if __name__ == '__main__':
    import socket
    def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    local_ip = get_local_ip()
    port = 5000
    print(f"\n{'=' * 60}")
    print(f"RESUME MATCHER IS STARTING!")
    print(f"Computer Access: http://127.0.0.1:{port}")
    print(f"Mobile Access:   http://{local_ip}:{port}")
    print(f"{'=' * 60}\n")
    print(f"Instructions for Mobile:")
    print(f"1. Connect your phone to the SAME Wi-Fi as this computer.")
    print(f"2. Open your phone's browser and type: http://{local_ip}:{port}")
    print(f"{'=' * 60}\n")
    app.run(debug=True, host='0.0.0.0', port=port)
