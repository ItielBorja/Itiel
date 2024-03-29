from flask import render_template, request, json, Response, send_file, send_from_directory, abort
from . import control
import time
import json
import socket
import sys
import threading
import os
from pathlib import Path
import zipfile
import io
from ..car import Car
from ..camera import Camera
from ..model import Model

variable ='left'
@control.route('/drive', methods=['POST'])
def drive():
    global variable
    direction = variable#obtener direccion AKIIIIIII
    #direction = request.json.get('direction')
    car = Car()
    if not Car.connected:
        return json.dumps({ 'error': 'Driving is not connected' })
    if direction not in 'leftrightforwardback':
        return

    camera = Camera()

    end_driving = car.drive(direction)

    return json.dumps(True)

@control.route('/self-drive', methods=['POST'])
def self_drive():
    on = request.json.get('on')

    model = Model()
    if on:
        model.start()
    else:
        model.end()

    return json.dumps(True)



@control.route('/update-settings', methods=['POST'])
def update_settings():
    config = {
        'forward': {
            'speed': float(request.form['speed-forward']),
            'steering': float(request.form['steering-forward']),
            'duration': float(request.form['duration-forward']),
        },
        'left': {
            'speed': float(request.form['speed-left']),
            'steering': float(request.form['steering-left']),
            'duration': float(request.form['duration-left']),
        },
        'right': {
            'speed': float(request.form['speed-right']),
            'steering': float(request.form['steering-right']),
            'duration': float(request.form['duration-right']),
        },
        'back': {
            'speed': float(request.form['speed-back']),
            'steering': float(request.form['steering-back']),
            'duration': float(request.form['duration-back']),
        },
        'stop': {
            'speed': 0,
            'steering': float(request.form['steering-forward']),
            'duration': 0,
        },
    }
    with open(os.path.join(str(Path(os.path.dirname(__file__)).parent), 'config.json'), 'w') as f:
        json.dump(config, f)
    now = time.strftime('%d/%b/%y %H:%M:%S.{}'.format(str(time.time() % 1)[2:5]))
    print('INFO - - [{}] {}'.format(now, 'Updated car settings'))

    Car.load_config()

    return json.dumps(True)

@control.route('/get-folder-stats', methods=['GET'])
def get_folder_stats():
    foldername = request.args.get('foldername')
    directory = os.path.join(str(Path(os.path.dirname(__file__)).parent.parent), 'data', foldername)
    if not os.path.exists(directory):
        return json.dumps([])

    stats = []
    for label in [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]:
        stats.append({
            'direction': label,
            'count': len(os.listdir(os.path.join(directory, label))),
        })

    return json.dumps(stats)

def zipfolder(foldername, path):
    data = io.BytesIO()
    with zipfile.ZipFile(data, mode='w') as z:
        for label in Path(path).iterdir():
            label_relative_folder = os.path.join(foldername, label.name)
            z.write(str(label), label_relative_folder)
            for image in label.iterdir():
                z.write(str(image), os.path.join(label_relative_folder, image.name))
    data.seek(0)
    return data

@control.route('/get-folder-zip', methods=['GET'])
def get_folder_zip():
    foldername = request.args.get('foldername')
    folderpath = os.path.join(str(Path(os.path.dirname(__file__)).parent.parent), 'data', foldername)
    if not os.path.exists(folderpath):
        abort(404, 'folder does not exist')

    zip = zipfolder(foldername, folderpath)
    return send_file(
        zip,
        mimetype='application/zip',
        as_attachment=True,
        attachment_filename='{}.zip'.format(foldername)
    )


def mainloop(name):
    global variable
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('192.168.43.137', 10000)
    print('starting up on {} port {}'.format(*server_address))
    sock.bind(server_address)
    while True:
        print('\nwaiting to receive message')
        data, address = sock.recvfrom(2000)

        print('received {} bytes from {}'.format(
            len(data), address))
        variable=str(data)
        print(variable)
        sent = sock.sendto(data, address)
        if 'Class' in variable:
            continue
        if 'up' in variable:
            variable='forward'
        elif 'down' in variable:
            variable='back'
        elif 'right' in variable:
            variable='right'
        elif 'left' in variable:
            variable='left'
        else:
            variable='stop'
        drive()

x = threading.Thread(target=mainloop, args=(1,))
x.start()
