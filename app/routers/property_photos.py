from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import time, timedelta
from decimal import Decimal
from app.db import get_connection
from app.Token.verify_api import verify_token
from app.models.property_photos import PropertyPhotoCreate,PropertyPhotoUpdate,PropertyPhotoInDB,PropertyPhotoResponse
from app.models.properties import PropertyResponse, PropertyCreate, PropertyUpdate
import mysql.connector

router = APIRouter(prefix="/property_photos", tags=["property_photos"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})

@router.get("/", response_model=List[PropertyPhotoResponse])
async def get_all_property_photos(skip: int = 0, limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT photo_id, property_id, photo_url, caption, 
                   is_cover_photo, display_order, uploaded_at
            FROM property_photos
            ORDER BY display_order
            LIMIT %s OFFSET %s
        """, (limit, skip))
        photos = cursor.fetchall()
        return [PropertyPhotoResponse(**photo) for photo in photos]
    finally:
        cursor.close()
        conn.close()
@router.get("/{photo_id}", response_model=PropertyPhotoResponse)
async def get_property_photo_by_id(photo_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT photo_id, property_id, photo_url, caption, 
                   is_cover_photo, display_order, uploaded_at
            FROM property_photos
            WHERE photo_id = %s
        """, (photo_id,))
        photo = cursor.fetchone()
        
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property photo not found"
            )
        return PropertyPhotoResponse(**photo)
    finally:
        cursor.close()
        conn.close()

@router.post("/", response_model=PropertyPhotoResponse, status_code=status.HTTP_201_CREATED)
async def create_property_photo(photo_data: PropertyPhotoCreate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            INSERT INTO property_photos 
            (property_id, photo_url, caption, is_cover_photo, display_order, uploaded_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            photo_data.property_id,
            photo_data.photo_url,
            photo_data.caption,
            photo_data.is_cover_photo,
            photo_data.display_order
        ))
        conn.commit()
        
        # Get the newly created photo
        photo_id = cursor.lastrowid
        cursor.execute("""
            SELECT photo_id, property_id, photo_url, caption, 
                   is_cover_photo, display_order, uploaded_at
            FROM property_photos
            WHERE photo_id = %s
        """, (photo_id,))
        new_photo = cursor.fetchone()
        
        return PropertyPhotoResponse(**new_photo)
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {err}"
        )
    finally:
        cursor.close()
        conn.close()

@router.put("/{photo_id}", response_model=PropertyPhotoResponse)
async def update_property_photo(photo_id: int, photo_data: PropertyPhotoUpdate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # First check if photo exists
        cursor.execute("SELECT photo_id FROM property_photos WHERE photo_id = %s", (photo_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property photo not found"
            )
        
        # Build dynamic update query
        update_fields = []
        values = []
        
        if photo_data.photo_url is not None:
            update_fields.append("photo_url = %s")
            values.append(photo_data.photo_url)
        if photo_data.caption is not None:
            update_fields.append("caption = %s")
            values.append(photo_data.caption)
        if photo_data.is_cover_photo is not None:
            update_fields.append("is_cover_photo = %s")
            values.append(photo_data.is_cover_photo)
        if photo_data.display_order is not None:
            update_fields.append("display_order = %s")
            values.append(photo_data.display_order)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        query = f"UPDATE property_photos SET {', '.join(update_fields)} WHERE photo_id = %s"
        values.append(photo_id)
        
        cursor.execute(query, values)
        conn.commit()
        
        # Get the updated photo
        cursor.execute("""
            SELECT photo_id, property_id, photo_url, caption, 
                   is_cover_photo, display_order, uploaded_at
            FROM property_photos
            WHERE photo_id = %s
        """, (photo_id,))
        updated_photo = cursor.fetchone()
        
        return PropertyPhotoResponse(**updated_photo)
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {err}"
        )
    finally:
        cursor.close()
        conn.close()

@router.delete("/{photo_id}", status_code=status.HTTP_200_OK)
async def delete_property_photo(photo_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # First check if photo exists
        cursor.execute("SELECT photo_id FROM property_photos WHERE photo_id = %s", (photo_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property photo not found"
            )
        
        cursor.execute("DELETE FROM property_photos WHERE photo_id = %s", (photo_id,))
        conn.commit()
        
        return {"message": "Property photo deleted successfully"}
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {err}"
        )
    finally:
        cursor.close()
        conn.close()