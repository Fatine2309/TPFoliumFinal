from pymongo import MongoClient
import webbrowser
import folium
from folium.plugins import MarkerCluster


# Fonction de connexion à MongoDB
def connect_mongodb():
    try:
        client = MongoClient('localhost', 27017)
        print('Connexion réussie à MongoDB!')
    except Exception as e:
        print('Échec de connexion à MongoDB:', e)
        return None
    return client


# Connexion à MongoDB
client = connect_mongodb()
if client:
    # Accéder à la base de données et à la collection
    db = client.velibdb
    collection = db.velibCol

    # Filtrer pour les stations Vélib situées à Paris
    tablo_velib = collection.find({"nom_arrondissement_communes": "Paris"})

    # Coordonnées de Paris pour centrer la carte
    coord_paris = [48.8566, 2.3522]

    # Créer une carte Folium
    m = folium.Map(location=coord_paris, zoom_start=13)

    # Ajouter un MarkerCluster pour regrouper les marqueurs
    marker_cluster = MarkerCluster().add_to(m)

    # Ajouter un marqueur pour chaque station Vélib
    for doc_velib in tablo_velib:
        try:
            # Extraire les coordonnées de la station
            coord_station_velib = [
                doc_velib['coordonnees_geo']['lat'],
                doc_velib['coordonnees_geo']['lon']
            ]
            # Extraire le nom de la station
            nom_station = doc_velib.get('name', 'Station inconnue')

            # Ajouter le marqueur au cluster avec popup
            folium.Marker(
                location=coord_station_velib,
                popup=nom_station
            ).add_to(marker_cluster)
        except KeyError as e:
            print(f"Erreur avec les données de la station : {e}")

    # Sauvegarder la carte au format HTML
    m.save("map.html")

    # Ouvrir la carte dans le navigateur
    webbrowser.open("map.html")
else:
    print("Impossible de se connecter à MongoDB. Script arrêté.")
