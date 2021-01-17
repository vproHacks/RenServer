from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
import random, requests, os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'HTNPLUSPLUSTIME'
app.config['UPLOAD_FOLDER'] = './uploads/'
socketio = SocketIO(app)

# Change DB System Later
'''
SCHEMA: 
name: str
host: str
code: str
count: int
'''
games = dict()

def generate_code():
    result = ''.join(random.choices(str(1234567890), k=6))
    while result in games:
        result = ''.join(random.choices(str(1234567890), k=6))
    return result

@app.route('/create', methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        data = dict(request.json)
        data['code'] = generate_code()
        games[data['code']] = data
        return data['code']
    return redirect(url_for('index'))

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        code = request.form.get('code')
        if code:
            if code in games:
                return redirect(url_for('game', code=code))
            else:
                flash('Game Does not Exist')
        else:
            flash('Please Enter Code')                        
    return render_template('index.html')

@app.route('/event/<code>', methods=['POST', 'GET'])
def event(code):
    if request.method == 'POST':
        data = request.json
        '''
        Schema:
        image: str (base64 encoded)
        choices: list[dict] (Eg: [{'x': 3, 'y': 4}])
        timeout: int
        '''
        if 'event' not in games[code]:
            games[code]['event'] = []
        games[code]['event'].append({})
        event = games[code]['event'][-1]
        for choice in data['choices']:
            event[f"{choice['x']}:{choice['y']}"] = 0
        event['event'] = dict(data)
        socketio.emit('event', data)
        return str({'status': 'GOOD'})
    return redirect(url_for('index'))

@app.route('/results/<code>', methods=['POST', 'GET'])
def results(code):
    if request.method == 'POST':
        return jsonify(games[code]['event'][-1])
    return redirect(url_for('index'))

@app.route('/end/<code>', methods=['POST', 'GET'])
def end_game(code):
    if request.method == 'POST':
        games.pop(code)
        socketio.emit('game over', {'code': code})
    return redirect(url_for('index'))

@app.route('/game/<code>')
def game(code):
    return render_template('game.html', game=games[code])

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    # pls no abuse :(
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(url_for('index'))
        file = request.files.get('file')
        if file.filename == '':
            return redirect(url_for('index'))
        if file:
            fname = secure_filename(file.filename)
            from uuid import uuid4
            x = uuid4().__str__()[:8]
            fname = f'{x}-{fname}'
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            return jsonify({'url': url_for('file', filename=fname)})
    return 'INVALID'

@app.route('/file/<filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('hello')
def hello(info):
    code = info['code']
    if 'count' in games[code]:
        games[code]['count'] += 1
    else:
        games[code]['count'] = 0
    emit('hello', {'count': games[code]['count']})

@socketio.on('timeout')
def timeout(info):
    code = info['code']
    choice = info['choice']
    if choice:
        # RIP RAM
        games[code]['event'][-1][choice] += 1
    emit('result update', {'event': games[code]['event'][-1]})


def run():
    socketio.run(app)