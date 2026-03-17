# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS
# from dotenv import load_dotenv
# import subprocess, tempfile, os, json, requests as req_lib
# from datetime import datetime
# import random

# load_dotenv()

# app = Flask(__name__, static_folder='.')
# CORS(app, origins=['*'])

# JUDGE_SECRET   = os.environ.get('JUDGE_SECRET', 'judge123')
# ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# # ── AI CONFIG ─────────────────────────────────────────────────────────
# # Loaded from ai_config.json (managed by admin panel)
# def load_ai_config():
#     if not os.path.exists('ai_config.json'):
#         default = {
#             'enabled': False,
#             'api_keys': [],
#             'current_key_index': 0,
#             'total_calls': 0,
#             'model': 'llama3-8b-8192'
#         }
#         save_ai_config(default)
#         return default
#     with open('ai_config.json', 'r') as f:
#         return json.load(f)

# def save_ai_config(data):
#     with open('ai_config.json', 'w') as f:
#         json.dump(data, f, indent=2)

# @app.after_request
# def after_request(response):
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
#     response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
#     return response

# # ── FILE HELPERS ──────────────────────────────────────────────────────
# def load_questions():
#     with open('questions.json', 'r', encoding='utf-8') as f:
#         return json.load(f)

# def load_submissions():
#     if not os.path.exists('submissions.json'):
#         return []
#     with open('submissions.json', 'r', encoding='utf-8') as f:
#         content = f.read().strip()
#         if not content:
#             return []
#         return json.loads(content)

# def save_submission(entry):
#     submissions = load_submissions()
#     submissions.append(entry)
#     with open('submissions.json', 'w', encoding='utf-8') as f:
#         json.dump(submissions, f, indent=2, ensure_ascii=False)

# def load_failed_attempts():
#     if not os.path.exists('failed_attempts.json'):
#         return {}
#     with open('failed_attempts.json', 'r', encoding='utf-8') as f:
#         content = f.read().strip()
#         return json.loads(content) if content else {}

# def save_failed_attempts(data):
#     with open('failed_attempts.json', 'w', encoding='utf-8') as f:
#         json.dump(data, f, indent=2)

# def load_unlock_requests():
#     if not os.path.exists('unlock_requests.json'):
#         return []
#     with open('unlock_requests.json', 'r', encoding='utf-8') as f:
#         content = f.read().strip()
#         return json.loads(content) if content else []

# def save_unlock_requests(data):
#     with open('unlock_requests.json', 'w', encoding='utf-8') as f:
#         json.dump(data, f, indent=2)

# def load_tab_violations():
#     if not os.path.exists('tab_violations.json'):
#         return []
#     with open('tab_violations.json', 'r', encoding='utf-8') as f:
#         content = f.read().strip()
#         return json.loads(content) if content else []

# def save_tab_violations(data):
#     with open('tab_violations.json', 'w', encoding='utf-8') as f:
#         json.dump(data, f, indent=2)

# # ── RUN PYTHON ────────────────────────────────────────────────────────
# def run_python(code, stdin_input=''):
#     with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8') as f:
#         f.write(code)
#         fname = f.name
#     try:
#         env = os.environ.copy()
#         env['PYTHONIOENCODING'] = 'utf-8'
#         env['PYTHONUTF8'] = '1'
#         result = subprocess.run(
#             ['python', fname],
#             input=stdin_input,
#             capture_output=True,
#             text=True,
#             timeout=5,
#             encoding='utf-8',
#             env=env
#         )
#         os.unlink(fname)
#         return result.stdout.strip(), result.stderr.strip(), result.returncode
#     except subprocess.TimeoutExpired:
#         os.unlink(fname)
#         return '', 'TimeoutError: Code took too long', 1
#     except Exception as e:
#         os.unlink(fname)
#         return '', str(e), 1

# # ── RUN TEST CASES ────────────────────────────────────────────────────
# def run_test_cases(code, test_cases):
#     results = []
#     all_passed = True

#     for i, tc in enumerate(test_cases):
#         stdin_input = tc.get('input', '')
#         expected    = tc.get('expected', '').strip()
#         stdout, stderr, exitcode = run_python(code, stdin_input)
#         actual  = stdout.strip()
#         passed  = (actual == expected) and (exitcode == 0)

#         if not passed:
#             all_passed = False

#         results.append({
#             'test_case':  i + 1,
#             'passed':     passed,
#             'input':      stdin_input,
#             'expected':   expected,
#             'actual':     actual,
#             'stderr':     stderr,
#             'exitcode':   exitcode,
#         })

#     return all_passed, results

# # ── GROQ AI REVIEW ────────────────────────────────────────────────────
# def groq_review(code, question_title, question_desc, test_results):
#     config = load_ai_config()

#     if not config.get('enabled') or not config.get('api_keys'):
#         return None

#     # Rotate through API keys
#     keys      = config['api_keys']
#     key_index = config.get('current_key_index', 0) % len(keys)
#     api_key   = keys[key_index]

#     # Rotate to next key for next call
#     config['current_key_index'] = (key_index + 1) % len(keys)
#     config['total_calls']       = config.get('total_calls', 0) + 1
#     save_ai_config(config)

#     prompt = f"""You are a code reviewer for a coding competition. Review this solution.

# Question: {question_title}
# Description: {question_desc}

# Submitted Code (Python):
# {code}

# Test Results: {len([r for r in test_results if r['passed']])}/{len(test_results)} passed

# Respond ONLY with a JSON object, no other text:
# {{
#   "quality_score": <number 1-10>,
#   "approach": "<one of: optimal, acceptable, brute_force, hardcoded, suspicious>",
#   "is_legitimate": <true or false>,
#   "reason": "<one sentence explanation>",
#   "flag": <true if suspicious or hardcoded, false otherwise>
# }}"""

#     try:
#         response = req_lib.post(
#             'https://api.groq.com/openai/v1/chat/completions',
#             headers={
#                 'Authorization': f'Bearer {api_key}',
#                 'Content-Type': 'application/json'
#             },
#             json={
#                 'model': config.get('model', 'llama3-8b-8192'),
#                 'messages': [{'role': 'user', 'content': prompt}],
#                 'max_tokens': 200,
#                 'temperature': 0.1,
#             },
#             timeout=10
#         )

#         if response.status_code == 200:
#             text = response.json()['choices'][0]['message']['content'].strip()
#             # Clean up JSON
#             text = text.replace('```json', '').replace('```', '').strip()
#             return json.loads(text)
#         else:
#             # Try next key on failure
#             config['current_key_index'] = (key_index + 1) % len(keys)
#             save_ai_config(config)
#             return None

#     except Exception as e:
#         print(f'Groq error: {e}')
#         return None

# # ── ROUTES ────────────────────────────────────────────────────────────

# @app.route('/ping')
# def ping():
#     return 'pong', 200

# @app.route('/')
# def index():
#     return send_from_directory('.', 'login.html')

# @app.route('/ide')
# def ide():
#     return send_from_directory('.', 'index.html')

# @app.route('/<path:path>')
# def static_files(path):
#     return send_from_directory('.', path)

# # ── RUN CODE ──────────────────────────────────────────────────────────
# @app.route('/run', methods=['POST'])
# def run_code():
#     code  = request.json.get('code', '')
#     stdin = request.json.get('stdin', '')
#     if len(code) > 5000:
#         return jsonify({'stdout': '', 'stderr': 'Code too large', 'exitCode': 1})
#     stdout, stderr, exitcode = run_python(code, stdin)
#     return jsonify({'stdout': stdout, 'stderr': stderr, 'exitCode': exitcode})

# # ── QUESTIONS ─────────────────────────────────────────────────────────
# @app.route('/questions', methods=['GET'])
# def get_questions():
#     questions = load_questions()
#     safe = {}
#     for qid, q in questions.items():
#         safe[qid] = {
#             'title':       q['title'],
#             'description': q['description'],
#             'expected':    q.get('test_cases', [{}])[0].get('expected', q.get('expected', '')),
#             'has_input':   any(tc.get('input', '') for tc in q.get('test_cases', [])),
#         }
#     return jsonify(safe)

# # ── SUBMIT ────────────────────────────────────────────────────────────
# @app.route('/submit', methods=['POST'])
# def submit_code():
#     data       = request.json
#     name       = data.get('name', '').strip()
#     roll       = data.get('roll', name).strip()
#     qid        = data.get('question', '')
#     code       = data.get('code', '')
#     start_time = data.get('startTime', None)

#     if not name:
#         return jsonify({'success': False, 'error': 'Team name required'})
#     if not qid:
#         return jsonify({'success': False, 'error': 'No question selected'})
#     if len(code) > 5000:
#         return jsonify({'success': False, 'error': 'Code too large'})

#     questions = load_questions()
#     if qid not in questions:
#         return jsonify({'success': False, 'error': 'Invalid question'})

#     # Check duplicate
#     existing = load_submissions()
#     if any(s['name'] == name and s['question'] == qid for s in existing):
#         return jsonify({'success': False, 'error': f'Already solved {qid}!'})

#     q          = questions[qid]
#     test_cases = q.get('test_cases', [{'input': '', 'expected': q.get('expected', '')}])

#     # Run all test cases
#     all_passed, test_results = run_test_cases(code, test_cases)

#     time_taken = None
#     if start_time:
#         time_taken = round((datetime.now().timestamp() * 1000 - start_time) / 1000, 1)

#     # Run Groq AI review if enabled and all passed
#     ai_review = None
#     if all_passed:
#         ai_review = groq_review(code, q['title'], q['description'], test_results)

#     if all_passed:
#         entry = {
#             'name':        name,
#             'roll':        roll,
#             'question':    qid,
#             'title':       q['title'],
#             'timeTaken':   time_taken,
#             'submittedAt': datetime.now().strftime('%H:%M:%S'),
#             'code':        code,
#             'testsPassed': len([r for r in test_results if r['passed']]),
#             'testsTotal':  len(test_results),
#         }
#         if ai_review:
#             entry['aiScore']    = ai_review.get('quality_score')
#             entry['aiApproach'] = ai_review.get('approach')
#             entry['aiFlagged']  = ai_review.get('flag', False)
#             entry['aiReason']   = ai_review.get('reason', '')
#         save_submission(entry)

#     return jsonify({
#         'success':     True,
#         'passed':      all_passed,
#         'test_results': test_results,
#         'timeTaken':   time_taken,
#         'ai_review':   ai_review,
#     })

# # ── LEADERBOARD ───────────────────────────────────────────────────────
# @app.route('/leaderboard', methods=['GET'])
# def leaderboard():
#     return jsonify(load_submissions())

# @app.route('/clear', methods=['POST'])
# def clear_leaderboard():
#     secret = request.json.get('secret', '')
#     if secret != JUDGE_SECRET:
#         return jsonify({'success': False, 'error': 'Invalid secret'})
#     with open('submissions.json', 'w', encoding='utf-8') as f:
#         json.dump([], f)
#     return jsonify({'success': True})

# # ── ADMIN VERIFY ──────────────────────────────────────────────────────
# @app.route('/admin/verify', methods=['POST'])
# def verify_admin():
#     password = request.json.get('password', '')
#     if password != ADMIN_PASSWORD:
#         return jsonify({'success': False, 'error': 'Wrong password'})
#     return jsonify({'success': True})

# # ── AI CONFIG ROUTES ──────────────────────────────────────────────────
# @app.route('/ai/config', methods=['GET'])
# def get_ai_config():
#     config = load_ai_config()
#     # Don't expose full API keys
#     safe = {
#         'enabled':       config.get('enabled', False),
#         'total_calls':   config.get('total_calls', 0),
#         'key_count':     len(config.get('api_keys', [])),
#         'current_key':   config.get('current_key_index', 0) + 1,
#         'model':         config.get('model', 'llama3-8b-8192'),
#     }
#     return jsonify(safe)

# @app.route('/ai/toggle', methods=['POST'])
# def toggle_ai():
#     secret  = request.json.get('secret', '')
#     enabled = request.json.get('enabled', False)
#     if secret != JUDGE_SECRET:
#         return jsonify({'success': False, 'error': 'Invalid secret'})
#     config = load_ai_config()
#     config['enabled'] = enabled
#     save_ai_config(config)
#     return jsonify({'success': True, 'enabled': enabled})

# @app.route('/ai/keys', methods=['POST'])
# def update_ai_keys():
#     secret = request.json.get('secret', '')
#     keys   = request.json.get('keys', [])
#     if secret != JUDGE_SECRET:
#         return jsonify({'success': False, 'error': 'Invalid secret'})
#     config = load_ai_config()
#     config['api_keys']           = [k.strip() for k in keys if k.strip()]
#     config['current_key_index']  = 0
#     save_ai_config(config)
#     return jsonify({'success': True, 'key_count': len(config['api_keys'])})

# @app.route('/ai/reset-counter', methods=['POST'])
# def reset_ai_counter():
#     secret = request.json.get('secret', '')
#     if secret != JUDGE_SECRET:
#         return jsonify({'success': False, 'error': 'Invalid secret'})
#     config = load_ai_config()
#     config['total_calls'] = 0
#     save_ai_config(config)
#     return jsonify({'success': True})

# # ── LOGIN ATTEMPT TRACKING ────────────────────────────────────────────
# @app.route('/login/attempt', methods=['POST'])
# def login_attempt():
#     roll   = request.json.get('roll', '').strip()
#     failed = load_failed_attempts()
#     if roll not in failed:
#         failed[roll] = {'count': 0, 'locked': False, 'requested_unlock': False}
#     failed[roll]['count'] += 1
#     if failed[roll]['count'] >= 3:
#         failed[roll]['locked'] = True
#     save_failed_attempts(failed)
#     remaining = max(0, 3 - failed[roll]['count'])
#     return jsonify({'locked': failed[roll]['locked'], 'attempts': failed[roll]['count'], 'remaining': remaining})

# @app.route('/login/status', methods=['POST'])
# def login_status():
#     roll   = request.json.get('roll', '').strip()
#     failed = load_failed_attempts()
#     info   = failed.get(roll, {'count': 0, 'locked': False})
#     return jsonify({'locked': info.get('locked', False), 'attempts': info.get('count', 0), 'remaining': max(0, 3 - info.get('count', 0)), 'requested_unlock': info.get('requested_unlock', False)})

# @app.route('/login/success', methods=['POST'])
# def login_success():
#     roll   = request.json.get('roll', '').strip()
#     failed = load_failed_attempts()
#     if roll in failed:
#         del failed[roll]
#         save_failed_attempts(failed)
#     return jsonify({'success': True})

# # ── UNLOCK REQUESTS ───────────────────────────────────────────────────
# @app.route('/unlock/request', methods=['POST'])
# def request_unlock():
#     data      = request.json
#     roll      = data.get('roll', '').strip()
#     team_name = data.get('team_name', '').strip()
#     failed    = load_failed_attempts()
#     if roll in failed:
#         failed[roll]['requested_unlock'] = True
#         save_failed_attempts(failed)
#     requests_list = load_unlock_requests()
#     requests_list = [r for r in requests_list if r['roll'] != roll]
#     requests_list.append({'roll': roll, 'team_name': team_name, 'requested_at': datetime.now().strftime('%H:%M:%S'), 'status': 'pending'})
#     save_unlock_requests(requests_list)
#     return jsonify({'success': True})

# @app.route('/unlock/requests', methods=['GET'])
# def get_unlock_requests():
#     return jsonify(load_unlock_requests())

# @app.route('/unlock/approve', methods=['POST'])
# def approve_unlock():
#     data   = request.json
#     secret = data.get('secret', '')
#     roll   = data.get('roll', '').strip()
#     if secret != JUDGE_SECRET:
#         return jsonify({'success': False, 'error': 'Invalid secret'})
#     failed = load_failed_attempts()
#     if roll in failed:
#         del failed[roll]
#         save_failed_attempts(failed)
#     requests_list = load_unlock_requests()
#     for r in requests_list:
#         if r['roll'] == roll:
#             r['status'] = 'approved'
#     save_unlock_requests(requests_list)
#     return jsonify({'success': True})

# @app.route('/unlock/check', methods=['POST'])
# def check_unlock():
#     roll          = request.json.get('roll', '').strip()
#     requests_list = load_unlock_requests()
#     for r in requests_list:
#         if r['roll'] == roll and r['status'] == 'approved':
#             return jsonify({'approved': True})
#     return jsonify({'approved': False})

# # ── TAB VIOLATION ─────────────────────────────────────────────────────
# @app.route('/tab/violation', methods=['POST'])
# def tab_violation():
#     data     = request.json
#     roll     = data.get('roll', '')
#     name     = data.get('name', '')
#     count    = data.get('count', 0)
#     is_final = data.get('isFinal', False)
#     time     = data.get('time', '')
#     violations = load_tab_violations()
#     existing   = next((v for v in violations if v['roll'] == roll), None)
#     if existing:
#         existing['count']    = count
#         existing['isFinal']  = is_final
#         existing['lastTime'] = time
#     else:
#         violations.append({'roll': roll, 'name': name, 'count': count, 'isFinal': is_final, 'lastTime': time, 'locked': False})
#     save_tab_violations(violations)
#     return jsonify({'success': True})

# @app.route('/tab/lock', methods=['POST'])
# def tab_lock():
#     data = request.json
#     roll = data.get('roll', '')
#     name = data.get('name', '')
#     failed = load_failed_attempts()
#     failed[roll] = {'count': 3, 'locked': True, 'requested_unlock': False, 'reason': 'tab_switching'}
#     save_failed_attempts(failed)
#     violations = load_tab_violations()
#     for v in violations:
#         if v['roll'] == roll:
#             v['locked'] = True
#     save_tab_violations(violations)
#     requests_list = load_unlock_requests()
#     requests_list = [r for r in requests_list if r['roll'] != roll]
#     requests_list.append({'roll': roll, 'team_name': name, 'requested_at': datetime.now().strftime('%H:%M:%S'), 'status': 'pending', 'reason': 'tab_switching'})
#     save_unlock_requests(requests_list)
#     return jsonify({'success': True})

# @app.route('/tab/violations', methods=['GET'])
# def get_tab_violations():
#     return jsonify(load_tab_violations())

# if __name__ == '__main__':
#     port  = int(os.environ.get('PORT', 5000))
#     debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
#     app.run(host='0.0.0.0', port=port, debug=debug)


from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import subprocess, tempfile, os, json, requests as req_lib
from datetime import datetime
import random

load_dotenv()

app = Flask(__name__, static_folder='.')
CORS(app, origins=['*'])

JUDGE_SECRET   = os.environ.get('JUDGE_SECRET', 'judge123')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# ── AI CONFIG ─────────────────────────────────────────────────────────
# Loaded from ai_config.json (managed by admin panel)
def load_ai_config():
    if not os.path.exists('ai_config.json'):
        default = {
            'enabled': False,
            'api_keys': [],
            'current_key_index': 0,
            'total_calls': 0,
            'model': 'llama-3.3-70b-versatile'
        }
        save_ai_config(default)
        return default
    with open('ai_config.json', 'r') as f:
        return json.load(f)

def save_ai_config(data):
    with open('ai_config.json', 'w') as f:
        json.dump(data, f, indent=2)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

# ── FILE HELPERS ──────────────────────────────────────────────────────
def load_questions():
    with open('questions.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_submissions():
    if not os.path.exists('submissions.json'):
        return []
    with open('submissions.json', 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)

def save_submission(entry):
    submissions = load_submissions()
    submissions.append(entry)
    with open('submissions.json', 'w', encoding='utf-8') as f:
        json.dump(submissions, f, indent=2, ensure_ascii=False)

def load_failed_attempts():
    if not os.path.exists('failed_attempts.json'):
        return {}
    with open('failed_attempts.json', 'r', encoding='utf-8') as f:
        content = f.read().strip()
        return json.loads(content) if content else {}

def save_failed_attempts(data):
    with open('failed_attempts.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_unlock_requests():
    if not os.path.exists('unlock_requests.json'):
        return []
    with open('unlock_requests.json', 'r', encoding='utf-8') as f:
        content = f.read().strip()
        return json.loads(content) if content else []

def save_unlock_requests(data):
    with open('unlock_requests.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_tab_violations():
    if not os.path.exists('tab_violations.json'):
        return []
    with open('tab_violations.json', 'r', encoding='utf-8') as f:
        content = f.read().strip()
        return json.loads(content) if content else []

def save_tab_violations(data):
    with open('tab_violations.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

# ── RUN PYTHON ────────────────────────────────────────────────────────
def run_python(code, stdin_input=''):
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8') as f:
        f.write(code)
        fname = f.name
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        result = subprocess.run(
            ['python', fname],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=5,
            encoding='utf-8',
            env=env
        )
        os.unlink(fname)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        os.unlink(fname)
        return '', 'TimeoutError: Code took too long', 1
    except Exception as e:
        os.unlink(fname)
        return '', str(e), 1

# ── STRIP INPUT PROMPTS ───────────────────────────────────────────────
def strip_input_prompts(code):
    """Replace input("prompt") with input() so prompts don't appear in stdout."""
    import re
    # Replace input("...") or input('...') with input()
    code = re.sub(r'input\s*\(["\'][^"\']*["\']\)', 'input()', code)
    return code

# ── RUN TEST CASES ────────────────────────────────────────────────────
def run_test_cases(code, test_cases):
    results = []
    all_passed = True
    # Strip input prompts so they don't pollute stdout during test runs
    clean_code = strip_input_prompts(code)

    for i, tc in enumerate(test_cases):
        stdin_input = tc.get('input', '')
        expected    = tc.get('expected', '').strip()
        stdout, stderr, exitcode = run_python(clean_code, stdin_input)
        actual  = stdout.strip()
        passed  = (actual == expected) and (exitcode == 0)

        if not passed:
            all_passed = False

        results.append({
            'test_case':  i + 1,
            'passed':     passed,
            'input':      stdin_input,
            'expected':   expected,
            'actual':     actual,
            'stderr':     stderr,
            'exitcode':   exitcode,
        })

    return all_passed, results

# ── GROQ AI REVIEW ────────────────────────────────────────────────────
def groq_review(code, question_title, question_desc, test_results):
    config = load_ai_config()
    print(f'Groq review called — enabled: {config.get("enabled")}, keys: {len(config.get("api_keys", []))}')  # ← ADD
    if not config.get('enabled') or not config.get('api_keys'):
        return None

    # Rotate through API keys
    keys      = config['api_keys']
    key_index = config.get('current_key_index', 0) % len(keys)
    api_key   = keys[key_index]

    # Rotate to next key for next call
    config['current_key_index'] = (key_index + 1) % len(keys)
    config['total_calls']       = config.get('total_calls', 0) + 1
    save_ai_config(config)

    prompt = f"""You are a code reviewer for a coding competition. Review this solution.

Question: {question_title}
Description: {question_desc}

Submitted Code (Python):
{code}

Test Results: {len([r for r in test_results if r['passed']])}/{len(test_results)} passed

Respond ONLY with a JSON object, no other text:
{{
  "quality_score": <number 1-10>,
  "approach": "<one of: optimal, acceptable, brute_force, hardcoded, suspicious>",
  "is_legitimate": <true or false>,
  "reason": "<one sentence explanation>",
  "flag": <true if suspicious or hardcoded, false otherwise>
}}"""

    try:
        response = req_lib.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': config.get('model', 'llama-3.3-70b-versatile'),
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 200,
                'temperature': 0.1,
            },
            timeout=10
        )

        if response.status_code == 200:
            text = response.json()['choices'][0]['message']['content'].strip()
            print(f'Groq raw response: {text}')  # ← ADD THIS
            text = text.replace('```json', '').replace('```', '').strip()
            try:
                return json.loads(text)
            except Exception as e:
                print(f'Groq JSON parse error: {e}')  # ← ADD THIS
                return None
        else:
            print(f'Groq HTTP error: {response.status_code} {response.text}')  # ← ADD THIS
            config['current_key_index'] = (key_index + 1) % len(keys)
            save_ai_config(config)
            return None

    except Exception as e:
        import traceback
        print(f'Groq error: {e}')
        traceback.print_exc()
        return None

# ── ROUTES ────────────────────────────────────────────────────────────

@app.route('/ping')
def ping():
    return 'pong', 200

@app.route('/')
def index():
    return send_from_directory('.', 'login.html')

@app.route('/ide')
def ide():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# ── RUN CODE ──────────────────────────────────────────────────────────
@app.route('/run', methods=['POST'])
def run_code():
    code  = request.json.get('code', '')
    stdin = request.json.get('stdin', '')
    blocked_keywords = [
    "print(", "input(", "for ", "while ", "if ",
    "import ", "def ", "class ", "lambda ",
    "open(", "exec(", "eval("
    ]
    if any(k in code for k in blocked_keywords):
        return jsonify({
            'stdout': '',
            'stderr': 'Only EmojiLang syntax allowed.',
            'exitCode': 1
        })
    clean_code = strip_input_prompts(code)
    if len(code) > 5000:
        return jsonify({'stdout': '', 'stderr': 'Code too large', 'exitCode': 1})
    stdout, stderr, exitcode = run_python(clean_code, stdin)
    return jsonify({'stdout': stdout, 'stderr': stderr, 'exitCode': exitcode})

# ── QUESTIONS ─────────────────────────────────────────────────────────
@app.route('/questions', methods=['GET'])
def get_questions():
    questions = load_questions()
    safe = {}
    
    for qid, q in questions.items():
        safe[qid] = {
            'title':       q['title'],
            'description': q['description'],
            'expected':    q.get('test_cases', [{}])[0].get('expected', q.get('expected', '')),
            'has_input':   any(tc.get('input', '') for tc in q.get('test_cases', [])),
        }
    response = jsonify(safe)
    response.headers['Cache-Control'] = 'no-store'
    return response

# ── SUBMIT ────────────────────────────────────────────────────────────
@app.route('/submit', methods=['POST'])
def submit_code():
    data       = request.json
    name       = data.get('name', '').strip()
    roll       = data.get('roll', name).strip()
    qid        = data.get('question', '')
    code       = data.get('code', '')
    start_time = data.get('startTime', None)
    if not name:
        return jsonify({'success': False, 'error': 'Team name required'})
    if not qid:
        return jsonify({'success': False, 'error': 'No question selected'})
    if len(code) > 5000:
        return jsonify({'success': False, 'error': 'Code too large'})

    questions = load_questions()
    if qid not in questions:
        return jsonify({'success': False, 'error': 'Invalid question'})

    # Check duplicate
    existing = load_submissions()
    if any(s['name'] == name and s['question'] == qid for s in existing):
        return jsonify({'success': False, 'error': f'Already solved {qid}!'})

    q          = questions[qid]
    test_cases = q.get('test_cases', [{'input': '', 'expected': q.get('expected', '')}])

    # Run all test cases
    all_passed, test_results = run_test_cases(code, test_cases)

    time_taken = None
    if start_time:
        time_taken = round((datetime.now().timestamp() * 1000 - start_time) / 1000, 1)

    # Run Groq AI review if enabled and all passed
    ai_review = None
    if all_passed:
        ai_review = groq_review(code, q['title'], q['description'], test_results)
        print(f'AI review result: {ai_review}')

    if all_passed:
        entry = {
            'name':        name,
            'roll':        roll,
            'question':    qid,
            'title':       q['title'],
            'timeTaken':   time_taken,
            'submittedAt': datetime.now().strftime('%H:%M:%S'),
            'code':        code,
            'testsPassed': len([r for r in test_results if r['passed']]),
            'testsTotal':  len(test_results),
        }
        if ai_review:
            entry['aiScore']    = ai_review.get('quality_score')
            entry['aiApproach'] = ai_review.get('approach')
            entry['aiFlagged']  = ai_review.get('flag', False)
            entry['aiReason']   = ai_review.get('reason', '')
        save_submission(entry)

    return jsonify({
        'success':     True,
        'passed':      all_passed,
        'test_results': test_results,
        'timeTaken':   time_taken,
        'ai_review':   ai_review,
    })

# ── LEADERBOARD ───────────────────────────────────────────────────────
@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    return jsonify(load_submissions())

@app.route('/clear', methods=['POST'])
def clear_leaderboard():
    secret = request.json.get('secret', '')
    if secret != JUDGE_SECRET:
        return jsonify({'success': False, 'error': 'Invalid secret'})
    with open('submissions.json', 'w', encoding='utf-8') as f:
        json.dump([], f)
    return jsonify({'success': True})

# ── ADMIN VERIFY ──────────────────────────────────────────────────────
@app.route('/admin/verify', methods=['POST'])
def verify_admin():
    password = request.json.get('password', '')
    if password != ADMIN_PASSWORD:
        return jsonify({'success': False, 'error': 'Wrong password'})
    return jsonify({'success': True})

# ── AI CONFIG ROUTES ──────────────────────────────────────────────────
@app.route('/ai/config', methods=['GET'])
def get_ai_config():
    config = load_ai_config()
    # Don't expose full API keys
    safe = {
        'enabled':       config.get('enabled', False),
        'total_calls':   config.get('total_calls', 0),
        'key_count':     len(config.get('api_keys', [])),
        'current_key':   config.get('current_key_index', 0) + 1,
        'model': config.get('model', 'llama-3.3-70b-versatile'),  # ← change here,
    }
    return jsonify(safe)

@app.route('/ai/toggle', methods=['POST'])
def toggle_ai():
    secret  = request.json.get('secret', '')
    enabled = request.json.get('enabled', False)
    if secret != JUDGE_SECRET:
        return jsonify({'success': False, 'error': 'Invalid secret'})
    config = load_ai_config()
    config['enabled'] = enabled
    save_ai_config(config)
    return jsonify({'success': True, 'enabled': enabled})

@app.route('/ai/keys', methods=['POST'])
def update_ai_keys():
    secret = request.json.get('secret', '')
    keys   = request.json.get('keys', [])
    if secret != JUDGE_SECRET:
        return jsonify({'success': False, 'error': 'Invalid secret'})
    config = load_ai_config()
    config['api_keys']           = [k.strip() for k in keys if k.strip()]
    config['current_key_index']  = 0
    save_ai_config(config)
    return jsonify({'success': True, 'key_count': len(config['api_keys'])})

@app.route('/ai/reset-counter', methods=['POST'])
def reset_ai_counter():
    secret = request.json.get('secret', '')
    if secret != JUDGE_SECRET:
        return jsonify({'success': False, 'error': 'Invalid secret'})
    config = load_ai_config()
    config['total_calls'] = 0
    save_ai_config(config)
    return jsonify({'success': True})

# ── LOGIN ATTEMPT TRACKING ────────────────────────────────────────────
@app.route('/login/attempt', methods=['POST'])
def login_attempt():
    roll   = request.json.get('roll', '').strip()
    failed = load_failed_attempts()
    if roll not in failed:
        failed[roll] = {'count': 0, 'locked': False, 'requested_unlock': False}
    failed[roll]['count'] += 1
    if failed[roll]['count'] >= 3:
        failed[roll]['locked'] = True
    save_failed_attempts(failed)
    remaining = max(0, 3 - failed[roll]['count'])
    return jsonify({'locked': failed[roll]['locked'], 'attempts': failed[roll]['count'], 'remaining': remaining})

@app.route('/login/status', methods=['POST'])
def login_status():
    roll   = request.json.get('roll', '').strip()
    failed = load_failed_attempts()
    info   = failed.get(roll, {'count': 0, 'locked': False})
    return jsonify({'locked': info.get('locked', False), 'attempts': info.get('count', 0), 'remaining': max(0, 3 - info.get('count', 0)), 'requested_unlock': info.get('requested_unlock', False)})

@app.route('/login/success', methods=['POST'])
def login_success():
    roll   = request.json.get('roll', '').strip()
    failed = load_failed_attempts()
    if roll in failed:
        del failed[roll]
        save_failed_attempts(failed)
    return jsonify({'success': True})

# ── UNLOCK REQUESTS ───────────────────────────────────────────────────
@app.route('/unlock/request', methods=['POST'])
def request_unlock():
    data      = request.json
    roll      = data.get('roll', '').strip()
    team_name = data.get('team_name', '').strip()
    failed    = load_failed_attempts()
    if roll in failed:
        failed[roll]['requested_unlock'] = True
        save_failed_attempts(failed)
    requests_list = load_unlock_requests()
    requests_list = [r for r in requests_list if r['roll'] != roll]
    requests_list.append({'roll': roll, 'team_name': team_name, 'requested_at': datetime.now().strftime('%H:%M:%S'), 'status': 'pending'})
    save_unlock_requests(requests_list)
    return jsonify({'success': True})

@app.route('/unlock/requests', methods=['GET'])
def get_unlock_requests():
    return jsonify(load_unlock_requests())

@app.route('/unlock/approve', methods=['POST'])
def approve_unlock():
    data   = request.json
    secret = data.get('secret', '')
    roll   = data.get('roll', '').strip()
    if secret != JUDGE_SECRET:
        return jsonify({'success': False, 'error': 'Invalid secret'})
    failed = load_failed_attempts()
    if roll in failed:
        del failed[roll]
        save_failed_attempts(failed)
    requests_list = load_unlock_requests()
    for r in requests_list:
        if r['roll'] == roll:
            r['status'] = 'approved'
    save_unlock_requests(requests_list)
    return jsonify({'success': True})

@app.route('/unlock/check', methods=['POST'])
def check_unlock():
    roll          = request.json.get('roll', '').strip()
    requests_list = load_unlock_requests()
    for r in requests_list:
        if r['roll'] == roll and r['status'] == 'approved':
            return jsonify({'approved': True})
    return jsonify({'approved': False})

# ── TAB VIOLATION ─────────────────────────────────────────────────────
@app.route('/tab/violation', methods=['POST'])
def tab_violation():
    data     = request.json
    roll     = data.get('roll', '')
    name     = data.get('name', '')
    count    = data.get('count', 0)
    is_final = data.get('isFinal', False)
    time     = data.get('time', '')
    violations = load_tab_violations()
    existing   = next((v for v in violations if v['roll'] == roll), None)
    if existing:
        existing['count']    = count
        existing['isFinal']  = is_final
        existing['lastTime'] = time
    else:
        violations.append({'roll': roll, 'name': name, 'count': count, 'isFinal': is_final, 'lastTime': time, 'locked': False})
    save_tab_violations(violations)
    return jsonify({'success': True})

@app.route('/tab/lock', methods=['POST'])
def tab_lock():
    data = request.json
    roll = data.get('roll', '')
    name = data.get('name', '')
    failed = load_failed_attempts()
    failed[roll] = {'count': 3, 'locked': True, 'requested_unlock': False, 'reason': 'tab_switching'}
    save_failed_attempts(failed)
    violations = load_tab_violations()
    for v in violations:
        if v['roll'] == roll:
            v['locked'] = True
    save_tab_violations(violations)
    requests_list = load_unlock_requests()
    requests_list = [r for r in requests_list if r['roll'] != roll]
    requests_list.append({'roll': roll, 'team_name': name, 'requested_at': datetime.now().strftime('%H:%M:%S'), 'status': 'pending', 'reason': 'tab_switching'})
    save_unlock_requests(requests_list)
    return jsonify({'success': True})

@app.route('/tab/violations', methods=['GET'])
def get_tab_violations():
    return jsonify(load_tab_violations())

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)