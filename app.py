from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'secret_key_here'

# --- Templates ---
login_template = '''
<h2>Login</h2>
<form method="post">
  Username: <input name="username"><br>
  Password: <input name="password" type="password"><br>
  <input type="submit" value="Login">
</form>
'''

dash_template = '''
<h2>Andar Bahar Manual Strategy Assistant</h2>
<p>Choose your strategy, set bet size, and follow recommendations.</p>
<form method="post" action="/set">
  Strategy:
  <select name="strategy">
    <option value="labouchere">Labouchere</option>
    <option value="martingale">Martingale</option>
  </select><br>
  Initial Bet Size: <input name="bet" type="number" value="10"><br>
  Initial Sequence (Labouchere only, comma-separated): <input name="sequence" value="1,2,3"><br>
  <input type="submit" value="Start Session">
</form>
{% if session.get('strategy') %}
  <h3>Strategy: {{ session.strategy }}</h3>
  <p>Next Bet: ₹{{ next_bet }}</p>
  <form method="post" action="/result">
    <input type="submit" name="result" value="Win">
    <input type="submit" name="result" value="Lose">
  </form>
  <p>Current Sequence: {{ session.get('sequence') }}</p>
  <p>Session Log:</p>
  <ul>
    {% for item in session.get('log', []) %}
      <li>{{ item }}</li>
    {% endfor %}
  </ul>
  <form action="/reset">
    <input type="submit" value="Reset Session">
  </form>
{% endif %}
'''

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == '1234':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template_string(login_template)

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    next_bet = calculate_next_bet()
    return render_template_string(dash_template, next_bet=next_bet)

@app.route('/set', methods=['POST'])
def set_strategy():
    session['strategy'] = request.form['strategy']
    session['initial_bet'] = int(request.form['bet'])
    session['sequence'] = [int(x) for x in request.form['sequence'].split(',') if x.strip().isdigit()]
    session['log'] = []
    return redirect(url_for('dashboard'))

@app.route('/result', methods=['POST'])
def result():
    result = request.form['result']
    strategy = session['strategy']
    log = session.get('log', [])
    seq = session.get('sequence', [])
    bet = calculate_next_bet()

    if strategy == 'labouchere':
        if result == 'Win' and len(seq) >= 2:
            seq = seq[1:-1]
            log.append(f"Win: Removed ends. New Seq: {seq}")
        elif result == 'Lose':
            seq.append(bet)
            log.append(f"Lose: Appended {bet}. New Seq: {seq}")
        session['sequence'] = seq

    elif strategy == 'martingale':
        if result == 'Win':
            session['current_bet'] = session['initial_bet']
        else:
            session['current_bet'] = session.get('current_bet', session['initial_bet']) * 2
        log.append(f"{result}: Bet now {session['current_bet']}")

    session['log'] = log
    return redirect(url_for('dashboard'))

@app.route('/reset')
def reset():
    session.pop('strategy', None)
    session.pop('sequence', None)
    session.pop('log', None)
    session.pop('initial_bet', None)
    session.pop('current_bet', None)
    return redirect(url_for('dashboard'))

# --- Helper ---
def calculate_next_bet():
    if session.get('strategy') == 'labouchere':
        seq = session.get('sequence', [])
        return seq[0] + seq[-1] if len(seq) > 1 else (seq[0] if seq else 0)
    elif session.get('strategy') == 'martingale':
        return session.get('current_bet', session.get('initial_bet', 10))
    return 0

# --- Run ---
if __name__ == '__main__':
    app.run(debug=True)
