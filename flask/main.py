from flask import Flask, render_template, send_from_directory, jsonify, request
from multiprocessing import Process
from glob import glob
from requests import Request, Session
from check_answer import check_answer
from solver import solve
import os
import sys
import time
import json


app = Flask(__name__, static_folder='public/static', template_folder='public')

@app.route('/problems', methods=['GET'])
def problems():
    dat = []
    for file in sorted(glob('public/static/problems/*.json'), key=lambda x: int(x.split('/')[-1][:-5])):
        with open(file) as f:
            dat.append(json.load(f))
    return jsonify(dat)


@app.route('/validate', methods=['POST'])
def validate():
    data = request.data.decode('utf-8')
    try:
        data = json.loads(data)
        valid = check_answer(data['problem'], data['vertices'])
        return jsonify({'valid': valid})
    except:
        return jsonify({'valid': False})


@app.route('/search', methods=['POST'])
def search():
    data = request.data.decode('utf-8')
    try:
        data = json.loads(data)
        print(data)
        res = solve(data['problem'], data['vertices'])
        print(res)
        return jsonify(res)
    except:
        return jsonify([])


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.template_folder, 'favicon.ico')

@app.route('/')
def index():
    return render_template('index.html')

if __name__=='__main__':
    app.run(host='0.0.0.0', port=18150, processes=4, threaded=False)

