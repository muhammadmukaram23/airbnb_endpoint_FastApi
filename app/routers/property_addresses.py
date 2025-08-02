from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import time, timedelta
from decimal import Decimal
from app.db import get_connection
from app.Token.verify_api import verify_token
from app.models.property_addresses import PropertyAddressCreate,PropertyAddressUpdate,PropertyAddressResponse,PropertyAddressInDB
from app.models.properties import PropertyResponse,PropertyInDB
import mysql.connector


router = APIRouter(prefix="/property_addreses", tags=["property_addreses"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

def verify_property_exists(property_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT property_id FROM properties WHERE property_id = %s", (property_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
    finally:
        cursor.close()
        conn.close()

@router.get("/", response_model=List[PropertyAddressResponse])
async def get_all_addresses(skip: int = 0, limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM property_addresses 
            LIMIT %s OFFSET %s
        """, (limit, skip))
        addresses = cursor.fetchall()
        return [PropertyAddressResponse(**addr) for addr in addresses]
    finally:
        cursor.close()
        conn.close()

@router.get("/{address_id}", response_model=PropertyAddressResponse)
async def get_address_by_id(address_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM property_addresses 
            WHERE address_id = %s
        """, (address_id,))
        address = cursor.fetchone()
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        return PropertyAddressResponse(**address)
    finally:
        cursor.close()
        conn.close()

@router.post("/", response_model=PropertyAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(address: PropertyAddressCreate):
    verify_property_exists(address.property_id)
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            INSERT INTO property_addresses (
                property_id, street_address, city, state_province,
                postal_code, country, latitude, longitude, neighborhood
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            address.property_id,
            address.street_address,
            address.city,
            address.state_province,
            address.postal_code,
            address.country,
            float(address.latitude) if address.latitude else None,
            float(address.longitude) if address.longitude else None,
            address.neighborhood
        ))
        conn.commit()
        
        address_id = cursor.lastrowid
        cursor.execute("""
            SELECT * FROM property_addresses 
            WHERE address_id = %s
        """, (address_id,))
        new_address = cursor.fetchone()
        return PropertyAddressResponse(**new_address)
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        cursor.close()
        conn.close()

@router.put("/{address_id}", response_model=PropertyAddressResponse)
async def update_address(address_id: int, address: PropertyAddressUpdate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if address exists
        cursor.execute("SELECT * FROM property_addresses WHERE address_id = %s", (address_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        # Build dynamic update
        update_fields = []
        params = []
        
        if address.street_address is not None:
            update_fields.append("street_address = %s")
            params.append(address.street_address)
        if address.city is not None:
            update_fields.append("city = %s")
            params.append(address.city)
        if address.state_province is not None:
            update_fields.append("state_province = %s")
            params.append(address.state_province)
        if address.postal_code is not None:
            update_fields.append("postal_code = %s")
            params.append(address.postal_code)
        if address.country is not None:
            update_fields.append("country = %s")
            params.append(address.country)
        if address.latitude is not None:
            update_fields.append("latitude = %s")
            params.append(float(address.latitude))
        if address.longitude is not None:
            update_fields.append("longitude = %s")
            params.append(float(address.longitude))
        if address.neighborhood is not None:
            update_fields.append("neighborhood = %s")
            params.append(address.neighborhood)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        query = f"UPDATE property_addresses SET {', '.join(update_fields)} WHERE address_id = %s"
        params.append(address_id)
        cursor.execute(query, params)
        conn.commit()
        
        # Return updated address
        cursor.execute("SELECT * FROM property_addresses WHERE address_id = %s", (address_id,))
        updated = cursor.fetchone()
        return PropertyAddressResponse(**updated)
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        cursor.close()
        conn.close()

@router.delete("/{address_id}", status_code=status.HTTP_200_OK)
async def delete_address(address_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM property_addresses WHERE address_id = %s", (address_id,))
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        conn.commit()
        return {"message": "Address deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        cursor.close()
        conn.close()