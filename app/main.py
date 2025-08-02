from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
# from app.routers import airlines,aircraft_types,countries,cities,airports,routes,flights,flight_schedules,flight_prices,users,passenger_profiles,bookings,booking_items,payment_transactions,user_searches,reviews,promotions,user_sessions
from app.routers import users
from app.routers import user_addresses
from app.routers import property_categories
from app.routers import properties
from app.routers import property_addresses
app = FastAPI(
    title="airbnb_system api",
    description="API for airbnb_system",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
# app.include_router(airlines.router)
app.include_router(users.router)
app.include_router(user_addresses.router)
app.include_router(property_categories.router)
app.include_router(properties.router)
app.include_router(property_addresses.router)