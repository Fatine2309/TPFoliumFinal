import asyncio
import aiohttp
import pymongo
from datetime import datetime
from pymongo import MongoClient

# Configuration MongoDB
MONGO_URI = "mongodb://localhost:27017/"  # Modifiez ceci selon votre configuration MongoDB

# Connexion à MongoDB
try:
    client = pymongo.MongoClient(MONGO_URI)  # Initialise le client MongoDB
    print("MongoDB connection established successfully!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit()  # Quitter si la connexion échoue

# Base de données et collection MongoDB
db = client['velibdb2']  # Nom de la base de données
collection = db['velib_collection']  # Nom de la collection

# URL de l'API Velib
url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/records?limit=20"

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

                # Insertion des données dans MongoDB
                collection.insert_many(records)
                print(f"{len(records)} records inserted at {datetime.now()}")

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