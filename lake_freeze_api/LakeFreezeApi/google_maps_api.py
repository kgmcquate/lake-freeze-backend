import googlemaps
from datetime import datetime
import os, boto3, json

from data_models import Lake
from database import engine
from sqlmodel import Session

# Geocoding an address
# geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')



api_key_secret_arn = os.environ.get("GOOGLEMAPS_API_KEY_SECRET" , "arn:aws:secretsmanager:us-east-1:117819748843:secret:google-maps-api-credentials-5jAl05")


print("getting google maps secret")
api_secret = json.loads(
        boto3.client("secretsmanager", 'us-east-1')
        .get_secret_value(SecretId=api_key_secret_arn)
        ["SecretString"]
)

gmaps = googlemaps.Client(key=api_secret["key"])

def update_latitude_and_longitude(lakes: list[Lake]):
    
    
    with Session(engine) as session:
        for lake in lakes:
            
            address = f"{lake.lake_name} Lake, {lake.state_or_province}, {lake.country}"
            result = gmaps.geocode(address=address)

            lat = result[0]['geometry']['location']['lat']
            long = result[0]['geometry']['location']['lng']
            lake.latitude = lat
            lake.longitude = long
            session.add(lake)
        session.commit()
