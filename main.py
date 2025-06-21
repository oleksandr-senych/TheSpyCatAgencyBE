from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers import cats, missions
import httpx
from store import valid_breeds

import models
from database import engine, Base
Base.metadata.create_all(bind=engine)







@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.thecatapi.com/v1/breeds")
        response.raise_for_status()
        breeds_data = response.json()
        global valid_breeds
        valid_breeds.clear()
        valid_breeds.extend([breed["name"] for breed in breeds_data])
    print(f"Loaded {len(valid_breeds)} cat breeds")
    
    yield  

app = FastAPI(lifespan=lifespan)




app.include_router(cats.router, prefix="/cats", tags=["Cats"])
app.include_router(missions.router, prefix="/missions", tags=["Missions"])
