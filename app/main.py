from fastapi import FastAPI, Request
from pydantic import BaseModel
import httpx
from .config import settings
from fastapi.middleware.cors import CORSMiddleware
import geocoder
from typing import Optional

class InfoPublic(BaseModel):
    client_ip: str
    location: Optional[str] = None
    greeting: str


app = FastAPI(port=8000)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_temperature(location: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f'https://api.weatherapi.com/v1/current.json?key={settings.weather_api_key}&q={location}&aqi=no')
    return response.json()['current']['temp_c']

async def get_location(ip_address: str):
    g = geocoder.ip(ip_address)
    return g.city

def get_client_ip(request: Request) -> str:
    headers = request.headers
    if 'x-forwarded-for' in headers:
        ip = headers['x-forwarded-for'].split(',')[0]
    else:
        ip = request.client.host
    return ip
    


@app.get('/api/hello', response_model=InfoPublic)
async def hello(visitor_name: str, request: Request):
    client_ip = get_client_ip(request=request)
    location = await get_location(client_ip if client_ip != '127.0.0.1' else 'me')
    
    if location:
        temperature = await get_temperature(location=location)
        greeting = f'Hello, {visitor_name}! The temperature is {temperature} degrees Celsius in {location}.'
    else:
        greeting = f'Hello, {visitor_name}! Sorry, we could not determine the temperature in your location.'

    info = InfoPublic(client_ip=client_ip, location=location, greeting=greeting)
    return info