from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.db import get_connection
from app.models.amenities import AmenityCreate,AmenityUpdate,AmenityInDB, AmenityResponse
from app.Token.verify_api import verify_token
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector

router = APIRouter(prefix="/amenities", tags=["Amenities"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})


@router.get("/", response_model=List[AmenityResponse])
async def get_all_amenities(skip: int = 0, limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM amenities 
            WHERE is_active = TRUE
            LIMIT %s OFFSET %s
        """, (limit, skip))
        amenities = cursor.fetchall()
        return [AmenityResponse(**amenity) for amenity in amenities]
    finally:
        cursor.close()
        conn.close()

@router.get("/{amenity_id}", response_model=AmenityResponse)
async def get_amenity_by_id(amenity_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM amenities 
            WHERE amenity_id = %s
        """, (amenity_id,))
        amenity = cursor.fetchone()
        if not amenity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Amenity not found"
            )
        return AmenityResponse(**amenity)
    finally:
        cursor.close()
        conn.close()

@router.post("/", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED)
async def create_amenity(amenity: AmenityCreate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if amenity name already exists
        cursor.execute("""
            SELECT amenity_name FROM amenities 
            WHERE amenity_name = %s
        """, (amenity.amenity_name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amenity name already exists"
            )
        
        # Insert new amenity
        cursor.execute("""
            INSERT INTO amenities (
                amenity_name, amenity_category, icon_url, 
                description, is_active
            ) VALUES (%s, %s, %s, %s, %s)
        """, (
            amenity.amenity_name,
            amenity.amenity_category,
            amenity.icon_url,
            amenity.description,
            amenity.is_active
        ))
        conn.commit()
        
        # Get the newly created amenity
        amenity_id = cursor.lastrowid
        cursor.execute("""
            SELECT * FROM amenities 
            WHERE amenity_id = %s
        """, (amenity_id,))
        new_amenity = cursor.fetchone()
        return AmenityResponse(**new_amenity)
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating amenity: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()

@router.put("/{amenity_id}", response_model=AmenityResponse)
async def update_amenity(amenity_id: int, amenity: AmenityUpdate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if amenity exists
        cursor.execute("""
            SELECT * FROM amenities 
            WHERE amenity_id = %s
        """, (amenity_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Amenity not found"
            )
        
        # Check if new name conflicts with other amenities
        if amenity.amenity_name is not None:
            cursor.execute("""
                SELECT amenity_id FROM amenities 
                WHERE amenity_name = %s AND amenity_id != %s
            """, (amenity.amenity_name, amenity_id))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Amenity name already in use"
                )
        
        # Build dynamic update
        update_fields = []
        params = []
        
        if amenity.amenity_name is not None:
            update_fields.append("amenity_name = %s")
            params.append(amenity.amenity_name)
        if amenity.amenity_category is not None:
            update_fields.append("amenity_category = %s")
            params.append(amenity.amenity_category)
        if amenity.icon_url is not None:
            update_fields.append("icon_url = %s")
            params.append(amenity.icon_url)
        if amenity.description is not None:
            update_fields.append("description = %s")
            params.append(amenity.description)
        if amenity.is_active is not None:
            update_fields.append("is_active = %s")
            params.append(amenity.is_active)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        query = f"UPDATE amenities SET {', '.join(update_fields)} WHERE amenity_id = %s"
        params.append(amenity_id)
        cursor.execute(query, params)
        conn.commit()
        
        # Return updated amenity
        cursor.execute("""
            SELECT * FROM amenities 
            WHERE amenity_id = %s
        """, (amenity_id,))
        updated = cursor.fetchone()
        return AmenityResponse(**updated)
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating amenity: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()

@router.delete("/{amenity_id}", status_code=status.HTTP_200_OK)
async def delete_amenity(amenity_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Soft delete (recommended approach)
        cursor.execute("""
            UPDATE amenities 
            SET is_active = FALSE 
            WHERE amenity_id = %s
        """, (amenity_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Amenity not found"
            )
        conn.commit()
        return {"message": "Amenity deactivated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting amenity: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()