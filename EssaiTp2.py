import asyncio
import aiohttp
from datetime import datetime
import webbrowser
import folium
from folium.plugins import MarkerCluster


# URL de l'API Velib
url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/records?limit=100"

# Fonction pour récupérer les données de l'API Velib
async def fetch_velib_data(session):
    try:
        # Faire la requête à l'API
        async with session.get(url) as response:
            print("Response status:", response.status)

            # Vérifier si la requête a réussi
            if response.status == 200:
                data = await response.json()
                print("Data fetched:", data)
                records = data['results']  # Extraire les enregistrements

                # Ajouter un horodatage à chaque enregistrement
                for record in records:
                    record['timestamp'] = datetime.now()

                # Filtrer pour les stations Vélib situées à Paris
                # tablo_velib = [record for record in records if record.get("nom_arrondissement_communes") == "Paris"]
                tablo_velib = [record for record in records]


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
                print(f"Failed to fetch data. Status code: {response.status}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Fonction principale pour exécuter la tâche toutes les minutes
async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            await fetch_velib_data(session)
            await asyncio.sleep(60)  # Attendre 60 secondes avant de rafraîchir

# Exécution de la fonction principale
if __name__ == "__main__":
    asyncio.run(main())