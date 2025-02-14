import asyncio
import aiohttp
from flask import Flask, request, render_template_string, jsonify, send_from_directory
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from folium.plugins import MarkerCluster
import os

# API Velib
VELIB_API_URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/records?limit=100"

app = Flask(__name__)

# Crée un dossier static si nécessaire
if not os.path.exists('static'):
    os.makedirs('static')

template_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Recherche de Vélib</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            text-align: center;
            padding: 20px;
        }
        h2 {
            color: #333;
        }
        form {
            background: white;
            padding: 20px;
            display: inline-block;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        input {
            padding: 10px;
            margin: 10px 0;
            width: 80%;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        button {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            border-radius: 5px;
        }
        button:hover {
            background: #218838;
        }
    </style>
</head>
<body>
    <h2>Entrez une adresse pour trouver les stations Vélib les plus proches</h2>
    <form action="/velib" method="get">
        <input type="text" name="address" placeholder="Entrez une adresse" required>
        <button type="submit">Rechercher</button>
    </form>
</body>
</html>
"""


# Helper: Fetch Velib data
async def fetch_velib_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(VELIB_API_URL) as response:
            if response.status == 200:
                data = await response.json()
                if 'results' in data:
                    return data['results']
                else:
                    return {"error": "Réponse inattendue", "response": data}
            else:
                raise Exception(f"Erreur lors de la récupération des données: {response.status}")


# Helper: Geocode address to coordinates
def get_coordinates(address):
    geolocator = Nominatim(user_agent="flask_velib")
    location = geolocator.geocode(address)
    if location:
        return (location.latitude, location.longitude)
    return None


# Helper: Filter stations near user location
def filter_stations_nearby(stations, user_coords, max_distance=500):
    nearby_stations = []
    for station in stations:
        try:
            station_coords = (station['geometry']['coordinates'][1], station['geometry']['coordinates'][0])
            distance = geodesic(user_coords, station_coords).meters
            if distance <= max_distance:
                station['distance'] = distance
                nearby_stations.append(station)
        except KeyError:
            continue
    return sorted(nearby_stations, key=lambda x: x['distance'])


# Route: Homepage
@app.route('/')
def index():
    return render_template_string(template_html)


# Route: Fetch Velib stations near address
@app.route('/velib', methods=['GET'])
def get_velib():
    address = request.args.get('address')
    if not address:
        return jsonify({"error": "Veuillez fournir une adresse"}), 400

    user_coords = get_coordinates(address)
    if not user_coords:
        return jsonify({"error": "Adresse non trouvée"}), 400

    try:
        stations = asyncio.run(fetch_velib_data())
        if isinstance(stations, dict) and "error" in stations:
            return jsonify(stations), 500

        nearby_stations = filter_stations_nearby(stations, user_coords)

        # Create a map
        m = folium.Map(location=user_coords, zoom_start=15)
        marker_cluster = MarkerCluster().add_to(m)

        # Ajouter des marqueurs sur la carte avec des icônes bien visibles
        for station in nearby_stations:
            station_coords = (station['geometry']['coordinates'][1], station['geometry']['coordinates'][0])

            # Icône plus voyante et personnalisée pour chaque station
            folium.Marker(
                location=station_coords,
                popup=(f"Station: {station['fields']['name']}<br>"
                       f"Vélos disponibles: {station['fields'].get('velib_vl', 0)}<br>"
                       f"Distance: {station['distance']:.1f} m"),
                icon=folium.Icon(color='blue', icon='info-sign', prefix='fa')  # Icône Font Awesome
            ).add_to(marker_cluster)

        # Créer un chemin vers le fichier de la carte
        map_file = "velib_mapV2.html"
        map_path = os.path.join('static', map_file)  # Enregistrer la carte dans le dossier static
        m.save(map_path)

        # Retourner l'iframe avec le chemin correct vers la carte HTML
        return f'<h3>Résultats pour {address}</h3><iframe src="/static/{map_file}" width="100%" height="500px"></iframe>'

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
