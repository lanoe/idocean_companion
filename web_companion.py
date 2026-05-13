from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from settings import Config, parse_form_to_dict
from ugps_connection import UgpsConnection
#from flask_cors import CORS

import subprocess
import threading
import queue
import signal
import csv
import time
import requests
import json
import os

from datetime import datetime

import random  # Pour simulation

app = Flask(__name__,static_url_path='', static_folder='www', template_folder='www')
app._favicon = "favicon.ico"
#CORS(app)  # Autorise les requêtes CORS depuis n'importe quelle origine

# Variable globale pour gérer le thread des données CSV
background_thread = None
stop_event = threading.Event()
data_lock = threading.Lock()
current_csv_filename = None

# Variable globale pour gérer le processus du script tracking.py
script_process = None
script_queue = queue.Queue()

def read_output():
    global script_process, script_queue
    for line in script_process.stdout:
        script_queue.put(line)
    script_process.wait()
    #script_queue.put(f"Script terminé avec le code {script_process.returncode}")

# Fonction pour récupérer les données CSV
def get_position_data():
    config = Config()
    locatorIp = config.data['WaterLinked UGPS']['IP']
    ugps = UgpsConnection(host="http://"+locatorIp)
    acoustic_data = ugps.get_acoustic_locator_position()
    print(acoustic_data)
    row_acoustic_data = ugps.get_raw_acoustic_locator_position()
    #print(row_acoustic_data)
    locator_data = ugps.get_global_locator_position()
    #print(locator_data)
    master_data = ugps.get_master_topside_position()
    #print(master_data)
    return {
        "master": {"lat": round(master_data["lat"], 8), "lon": round(master_data["lon"], 8)},
        "locator": {"lat": round(locator_data["lat"], 8), "lon": round(locator_data["lon"], 8)},
        "filt": {"x": round(acoustic_data["x"], 2), "y": round(acoustic_data["y"], 2), "z": round(acoustic_data["z"], 2), "std": round(acoustic_data["std"]),
            "rssi0": round(acoustic_data["receiver_rssi"][0], 8), "rssi1": round(acoustic_data["receiver_rssi"][1], 8), "rssi2": round(acoustic_data["receiver_rssi"][2], 8), "rssi3": round(acoustic_data["receiver_rssi"][3], 8),
            "nsd0": round(acoustic_data["receiver_nsd"][0], 8), "nsd1": round(acoustic_data["receiver_nsd"][1], 8), "nsd2": round(acoustic_data["receiver_nsd"][2], 8), "nsd3": round(acoustic_data["receiver_nsd"][3], 8),
            },
        "raw": {"x": round(row_acoustic_data["x"], 2), "y": round(row_acoustic_data["y"], 2), "z": round(row_acoustic_data["z"], 2), "std": round(row_acoustic_data["std"]),
            "rssi0": round(row_acoustic_data["receiver_rssi"][0], 8), "rssi1": round(row_acoustic_data["receiver_rssi"][1], 8), "rssi2": round(row_acoustic_data["receiver_rssi"][2], 8), "rssi3": round(row_acoustic_data["receiver_rssi"][3], 8),
            "nsd0": round(row_acoustic_data["receiver_nsd"][0], 8), "nsd1": round(row_acoustic_data["receiver_nsd"][1], 8), "nsd2": round(row_acoustic_data["receiver_nsd"][2], 8), "nsd3": round(row_acoustic_data["receiver_nsd"][3], 8)
            } 
    }

# Tâche de fond de sauvegarde des données CSV
def background_task():
    global current_data, current_csv_filename
    with open(current_csv_filename, mode='a', newline='') as f:
        writer = csv.writer(f)
        while not stop_event.is_set():
            start = time.time()
            data = get_position_data()
            print(f"Temps API: {time.time() - start:.2f} s")
            timestamp = datetime.now().isoformat()
            with data_lock:
                writer.writerow([
                    timestamp,
                    data["master"]["lat"], data["master"]["lon"],
                    data["locator"]["lat"], data["locator"]["lon"],
                    data["filt"]["x"], data["filt"]["y"], data["filt"]["z"],
                    data["filt"]["std"], data["filt"]["rssi0"], data["filt"]["rssi1"], data["filt"]["rssi2"], data["filt"]["rssi3"],
                    data["filt"]["nsd0"], data["filt"]["nsd1"], data["filt"]["nsd2"], data["filt"]["nsd3"],
                    data["raw"]["x"], data["raw"]["y"], data["raw"]["z"],
                    data["raw"]["std"], data["raw"]["rssi0"], data["raw"]["rssi1"], data["raw"]["rssi2"], data["raw"]["rssi3"],
                    data["raw"]["nsd0"], data["raw"]["nsd1"], data["raw"]["nsd2"], data["raw"]["nsd3"]
                ])
            #time.sleep(0.25)  # 250 ms
            time.sleep(1)  # 1 s
        
@app.route('/')
def index():
    config = Config()
    masterIp = config.data['BlueOS MavLink']['IP']
    locatorIp = config.data['WaterLinked UGPS']['IP']
    return render_template('index.html', master_ip=masterIp, locator_ip=locatorIp, filename=current_csv_filename)

@app.route('/get_master')
def proxy_master():
    config = Config()
    master_ip = config.data['BlueOS MavLink']['IP']
    url = f"http://{master_ip}/mavlink/vehicles/1/components/1/messages/AHRS2"
    #master_ip = config.data['WaterLinked UGPS']['IP']
    #url = f"http://{master_ip}/api/v1/position/master"
    try:
        response = requests.get(url)
        return jsonify(response.json())
    except Exception as e:
        print("error", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/get_locator')
def proxy_locator():
    config = Config()
    locator_ip = config.data['WaterLinked UGPS']['IP']
    ugps = UgpsConnection(host="http://"+locator_ip)
    acoustic_data = ugps.get_acoustic_locator_position()
    locator_data = ugps.get_global_locator_position()
    if acoustic_data == None or locator_data == None:
        return jsonify({"error": "No data"}), 500
    return json.dumps(locator_data | acoustic_data)
    
# for config
@app.route('/config', methods=['GET', 'POST'])
def config_page():
    config = Config()
    if request.method == 'POST':
        # Parse les données du formulaire en dictionnaire imbriqué
        new_data = parse_form_to_dict(request.form)
        # Met à jour la configuration
        config.data = new_data
        config.sauvegarder()
        return redirect(url_for('config_page'))

    # Génération automatique des champs du formulaire
    form_fields = []
    def generate_fields(data, prefix=""):
        for key, value in data.items():
            field_name = f"{prefix}[{key}]" if prefix else key
            if isinstance(value, dict):
                generate_fields(value, field_name)
            else:
                field_type = "checkbox" if isinstance(value, bool) else "number" if isinstance(value, (int, float)) else "text"
                form_fields.append({
                    "name": field_name,
                    "value": value,
                    "type": field_type,
                    "label": key.replace("_", " ").title()
                })
    generate_fields(config.get_all())
    return render_template('config_auto.html', form_fields=form_fields)

# for tracking
@app.route('/tracking')
def tracking_page():
    return render_template('tracking.html')

@app.route('/start_tracking', methods=['POST'])
def start_script():
    global script_process
    if script_process is None or script_process.poll() is not None:
        script_process = subprocess.Popen(
            ["python3", "tracking.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        # Démarre un thread pour lire la sortie
        threading.Thread(target=read_output, daemon=True).start()
        return jsonify({"status": "started", "pid": script_process.pid})
    return jsonify({"status": "already running"})

@app.route('/stop_tracking', methods=['POST'])
def stop_script():
    global script_process
    if script_process and script_process.poll() is None:
        try:
            script_process.send_signal(signal.SIGINT)
            script_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            script_process.kill()
        return jsonify({"status": "stopped"})
    return jsonify({"status": "not running"})

@app.route('/get_script_status', methods=['GET'])
def get_script_status():
    global script_process
    if script_process and script_process.poll() is None:
        return jsonify({"running": True})
    else:
        return jsonify({"running": False})

@app.route('/get_script_output', methods=['GET'])
def get_script_output():
    global script_queue
    output = []
    while not script_queue.empty():
        output.append(script_queue.get())
    return jsonify({"output": output})

# for capture
@app.route('/start', methods=['POST'])
def start():
    global background_thread, stop_event, current_csv_filename
    filename = request.args.get('filename', 'capture')
    if background_thread is None or not background_thread.is_alive():
        stop_event.clear()
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        current_csv_filename = f"data/{filename}_{now}.csv"
        with open(current_csv_filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "m_lat", "m_lon", "l_lat", "l_lon",
                             "x", "y", "z", "std", "rssi0", "rssi1", "rssi2", "rssi3", "nsd0", "nsd1", "nsd2", "nsd3",
                             "x_r", "y_r", "z_r", "std_r", "rssi0_r", "rssi1_r", "rssi2_r", "rssi3_r", "nsd0_r", "nsd1_r", "nsd2_r", "nsd3_r"])
        background_thread = threading.Thread(target=background_task)
        background_thread.start()
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    global stop_event
    stop_event.set()
    return redirect(url_for('index'))

@app.route('/get_status')
def get_status():
    global background_thread
    if background_thread is not None and background_thread.is_alive():
        return jsonify({"running": True})
    else:
        return jsonify({"running": False})

@app.route('/get_filename')
def get_filename():
    global current_csv_filename
    if current_csv_filename is not None:
        return current_csv_filename
    else:
        return "No file"

@app.route('/data')
def list_data():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir):
        return "Le répertoire 'data' n'existe pas."
    scandir = os.listdir(data_dir)
    html = ""
    excludes = {"index.php", "f_.php", "l_.php", ".", ".."}
    for fichier in scandir:
        if fichier not in excludes:
            html += f'<a href="/data/{fichier}">{fichier}</a><br>\n'
    return html

@app.route('/data/<path:filename>')
def get_file(filename):
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    return send_from_directory(data_dir, filename)


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=5000)