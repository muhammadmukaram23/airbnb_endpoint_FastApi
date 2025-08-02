from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.db import get_connection
from app.models.users import UserResponse
from app.models.user_addresses import UserAddressCreate,UserAddressInDB,UserAddressUpdate,UserAddressResponse
from app.Token.verify_api import verify_token
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector
router = APIRouter(prefix="/user_addresses", tags=["User_addresses"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

def verify_user_exists(user_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    finally:
        cursor.close()
        conn.close()


@router.get("/", response_model=List[UserAddressResponse])
async def get_all_addresses(skip: int = 0, limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM user_addresses 
            LIMIT %s OFFSET %s
        """, (limit, skip))
        addresses = cursor.fetchall()
        return [UserAddressResponse(**addr) for addr in addresses]
    finally:
        cursor.close()
        conn.close()


@router.get("/{address_id}", response_model=UserAddressResponse)
async def get_address_by_id(address_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM user_addresses 
            WHERE address_id = %s
        """, (address_id,))
        address = cursor.fetchone()
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        return UserAddressResponse(**address)
    finally:
        cursor.close()
        conn.close()

@router.post("/", response_model=UserAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(address: UserAddressCreate):
    verify_user_exists(address.user_id)
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # If setting as primary, unset any existing primary addresses
        if address.is_primary:
            cursor.execute("""
                UPDATE user_addresses 
                SET is_primary = FALSE 
                WHERE user_id = %s
            """, (address.user_id,))
        
        cursor.execute("""
            INSERT INTO user_addresses (
                user_id, address_type, street_address, 
                city, state_province, postal_code, 
                country, is_primary
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            address.user_id, address.address_type.value, address.street_address,
            address.city, address.state_province, address.postal_code,
            address.country, address.is_primary
        ))
        conn.commit()
        
        # Get the newly created address
        address_id = cursor.lastrowid
        cursor.execute("""
            SELECT * FROM user_addresses 
            WHERE address_id = %s
        """, (address_id,))
        new_address = cursor.fetchone()
        return UserAddressResponse(**new_address)
    finally:
        cursor.close()
        conn.close()

@router.put("/{address_id}", response_model=UserAddressResponse)
async def update_address(address_id: int, address: UserAddressUpdate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get existing address to check user_id
        cursor.execute("""
            SELECT * FROM user_addresses 
            WHERE address_id = %s
        """, (address_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        # If setting as primary, unset any existing primary addresses
        if address.is_primary is True:
            cursor.execute("""
                UPDATE user_addresses 
                SET is_primary = FALSE 
                WHERE user_id = %s AND address_id != %s
            """, (existing['user_id'], address_id))
        
        # Build dynamic update query
        update_fields = []
        values = []
        
        if address.address_type is not None:
            update_fields.append("address_type = %s")
            values.append(address.address_type.value)
        if address.street_address is not None:
            update_fields.append("street_address = %s")
            values.append(address.street_address)
        if address.city is not None:
            update_fields.append("city = %s")
            values.append(address.city)
        if address.state_province is not None:
            update_fields.append("state_province = %s")
            values.append(address.state_province)
        if address.postal_code is not None:
            update_fields.append("postal_code = %s")
            values.append(address.postal_code)
        if address.country is not None:
            update_fields.append("country = %s")
            values.append(address.country)
        if address.is_primary is not None:
            update_fields.append("is_primary = %s")
            values.append(address.is_primary)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Execute update
        query = f"""
            UPDATE user_addresses 
            SET {', '.join(update_fields)} 
            WHERE address_id = %s
        """
        values.append(address_id)
        cursor.execute(query, values)
        conn.commit()
        
        # Return updated address
        cursor.execute("""
            SELECT * FROM user_addresses 
            WHERE address_id = %s
        """, (address_id,))
        updated = cursor.fetchone()
        return UserAddressResponse(**updated)
    finally:
        cursor.close()
        conn.close()

@router.delete("/{address_id}", status_code=status.HTTP_200_OK)
async def delete_address(address_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM user_addresses 
            WHERE address_id = %s
        """, (address_id,))
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        conn.commit()
        return {"message": "Address deleted successfully"}
    finally:
        cursor.close()
        conn.close()