from flask import Flask, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'HTNPLUSPLUSTIME'
socketio = SocketIO(app)

# Change DB System Later
'''
SCHEMA: 
name: str
host: str
code: str
count: int
'''
games = {
    ''''123456': {
        'name': 'Doki Doki Literature Club',
        'host': 'vpro8725',
        'code': '123456'
    }'''
}

def generate_code():
    result = random.choices(str(1234567890), k=6)
    while result in games:
        result = random.choices(str(1234567890), k=6)
    return result

@app.route('/create', methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        data = dict(request.json)
        data['code'] = generate_code()
        games[data['code']] = data
        return str({'code': data['code']})
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
        return str(games[code]['event'][-1])
    return redirect(url_for('index'))

@app.route('/game/<code>')
def game(code):
    return render_template('game.html', game=games[code])

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