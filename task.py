from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Float
import sqlalchemy
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import googlemaps
from geopy.distance import geodesic

app = FastAPI()

DATABASE_URL = 'sqlite:///./database.db'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = sqlalchemy.orm.declarative_base()

gmaps = googlemaps.Client(key='YOUR KEY')

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CityAdd(BaseModel):
    name: str
    # latitude: float
    # longitude: float

class CityResponse(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    distance: float

class NearestCity(BaseModel):
    latitude: float
    longitude: float

@app.get('/')
def index():
    return {'info':'go to localhost/docs'}

# @app.post('/cities/', response_model=CityResponse)
# async def create_city(city:CityAdd, db:Session = Depends(get_db)):
#     db_city = City(**city.model_dump())
#     db.add(db_city)
#     db.commit()
#     db.refresh(db_city)
#     return db_city
@app.post('/cities/')
async def create_city(city_data: CityAdd):
    result = gmaps.geocode(city_data.name)
    if not result:
        raise HTTPException(status_code=404, detail='City not found')

    location = result[0]['geometry']['location']
    latitude = location['lat']
    longitude = location['lng']

    db = SessionLocal()
    db_city = City(name=city_data.name, latitude=latitude, longitude=longitude)
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    db.close()
    return {'city': city_data.name, 'latitude':latitude, 'longitude':longitude}

@app.get('/cities/{city_id}', response_model=CityResponse)
async def get_city(city_id:int, db:Session=Depends(get_db)):
    db_city = db.query(City).filter(City.id==city_id).first()
    if db_city is None:
        raise HTTPException(status_code=404, detail='City not found')
    return db_city

@app.get('/cities/', response_model=CityResponse)
async def get_city_by_name(name:str, db:Session=Depends(get_db)):
    db_city = db.query(City).filter(City.name==name).first()
    if db_city is None:
        raise HTTPException(status_code=404, detail='City not found')
    return db_city

@app.put('/cities/{city_id}', response_model=CityResponse)
async def update_city(city_id:int, city_update:CityAdd, db:Session = Depends(get_db)):
    db_city = db.query(City).filter(City.id==city_id).first()
    if db_city is None:
        raise HTTPException(status_code=404, detail='City not found')

    for key, value in city_update.dict().items():
        setattr(db_city, key, value)

    db.commit()
    return db_city

@app.delete('/cities/{city_id}')
async def delete_city(city_id:int, db: Session=Depends(get_db)):
    db_city = db.query(City).filter(City.id==city_id).first()

    if db_city is None:
        raise HTTPException(status_code=404, detail='city not found')

    db.delete(db_city)
    db.commit()
    return {'message':'City deleted successfully'}

@app.post('/nearest_cities/', response_model=list[CityResponse])
async def get_nearest_cities(nearest_city:NearestCity, db:Session = Depends(get_db)):
    cities = db.query(City).all()

    city_distances = []
    for city in cities:
        distance = geodesic((nearest_city.latitude, nearest_city.longitude), (city.latitude, city.longitude)).kilometers
        city_distances.append({'city':city, 'distance':distance})

    #sort
    sorted_cities = sorted(city_distances, key=lambda x: x['distance'])
    nearest_cities = sorted_cities[:2]

    response_data = []
    for city_data in nearest_cities:
        city = city_data['city']
        response_data.append({
            'id':city.id,
            'name':city.name,
            'latitude':city.latitude,
            'longitude': city.longitude,
            'distance': city_data['distance']
        })
    return response_data

if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host="127.0.0.1", port=8000)









