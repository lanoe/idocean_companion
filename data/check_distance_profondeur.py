import sys
import csv
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def main(csv_file):
    # Initialisation des listes
    timestamps = []
    x_coords = []
    y_coords = []
    z_coords = []  # Pour la profondeur
    distances = []
    times_in_seconds = []

    # Lecture du fichier CSV
    with open(csv_file, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # On saute l'en-tête
        for row in reader:
            timestamp = row[0]
            x = float(row[5])  # 6ème colonne (index 5)
            y = float(row[6])  # 7ème colonne (index 6)
            z = float(row[7])  # 8ème colonne (index 7)
            timestamps.append(timestamp)
            x_coords.append(x)
            y_coords.append(y)
            z_coords.append(z)
            # Calcul de la distance par rapport à l'origine (0,0)
            distance = np.sqrt(x**2 + y**2)
            distances.append(distance)

    # Conversion des timestamps en objets datetime
    datetime_objects = [datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f") for ts in timestamps]

    # Calcul du temps en secondes depuis le premier timestamp
    start_time = datetime_objects[0]
    for dt in datetime_objects:
        delta = dt - start_time
        times_in_seconds.append(delta.total_seconds())

    # Création des graphiques
    plt.figure(figsize=(14, 6))

    # Graphique 1 : Distance en fonction du temps
    plt.subplot(2, 1, 1)
    plt.plot(times_in_seconds, distances, marker='o', linestyle='-', color='b')
    plt.title("Distance en fonction du temps")
    plt.xlabel("Temps (secondes)")
    plt.ylabel("Distance (m)")  # <-- Modifié pour indiquer les mètres
    plt.grid(True)

    # Graphique 2 : Profondeur (z) en fonction du temps
    plt.subplot(2, 1, 2)
    plt.plot(times_in_seconds, z_coords, marker='o', linestyle='-', color='g')
    plt.title("Profondeur en fonction du temps")
    plt.xlabel("Temps (secondes)")
    plt.ylabel("Profondeur (m)")  # <-- Modifié pour indiquer les mètres
    plt.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <fichier.csv>")
        sys.exit(1)
    main(sys.argv[1])
