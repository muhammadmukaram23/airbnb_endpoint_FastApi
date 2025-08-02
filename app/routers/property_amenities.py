from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import time, timedelta
from decimal import Decimal
from app.db import get_connection
from app.Token.verify_api import verify_token
from app.models.property_amenities import PropertyAmenityCreate,PropertyAmenityResponse,PropertyAmenityUpdate
from app.models.properties import PropertyInDB,PropertyResponse
from app.models.amenities import AmenityInDB,AmenityResponse
import mysql.connector

router = APIRouter(prefix="/property_amenities", tags=["property_amenities"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
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

def verify_amenity_exists(amenity_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT amenity_id FROM amenities WHERE amenity_id = %s AND is_active = TRUE", (amenity_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Amenity not found or inactive"
            )
    finally:
        cursor.close()
        conn.close()

@router.post("/", response_model=PropertyAmenityResponse, status_code=status.HTTP_201_CREATED)
async def add_amenity_to_property(pa: PropertyAmenityCreate):
    verify_property_exists(pa.property_id)
    verify_amenity_exists(pa.amenity_id)
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if association already exists
        cursor.execute("""
            SELECT * FROM property_amenities 
            WHERE property_id = %s AND amenity_id = %s
        """, (pa.property_id, pa.amenity_id))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This amenity is already associated with the property"
            )
        
        # Create new association
        cursor.execute("""
            INSERT INTO property_amenities (property_id, amenity_id)
            VALUES (%s, %s)
        """, (pa.property_id, pa.amenity_id))
        conn.commit()
        
        return PropertyAmenityResponse(**pa.dict())
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding amenity to property: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()

@router.put("/", response_model=PropertyAmenityResponse)
async def update_property_amenity(
    property_id: int,
    update_data: PropertyAmenityUpdate
):
    conn = None
    cursor = None
    try:
        # Verify property exists
        verify_property_exists(property_id)
        
        # Verify both old and new amenities exist
        verify_amenity_exists(update_data.old_amenity_id)
        verify_amenity_exists(update_data.new_amenity_id)
        
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if the old association exists
        cursor.execute("""
            SELECT * FROM property_amenities 
            WHERE property_id = %s AND amenity_id = %s
        """, (property_id, update_data.old_amenity_id))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The specified amenity is not currently associated with this property"
            )
        
        # Check if new association already exists
        cursor.execute("""
            SELECT * FROM property_amenities 
            WHERE property_id = %s AND amenity_id = %s
        """, (property_id, update_data.new_amenity_id))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The new amenity is already associated with this property"
            )
        
        # Remove old amenity
        cursor.execute("""
            DELETE FROM property_amenities 
            WHERE property_id = %s AND amenity_id = %s
        """, (property_id, update_data.old_amenity_id))
        
        # Add new amenity
        cursor.execute("""
            INSERT INTO property_amenities (property_id, amenity_id)
            VALUES (%s, %s)
        """, (property_id, update_data.new_amenity_id))
        
        conn.commit()
        
        # Get the updated association with amenity details
        cursor.execute("""
            SELECT pa.*, a.amenity_name, a.amenity_category, a.icon_url
            FROM property_amenities pa
            JOIN amenities a ON pa.amenity_id = a.amenity_id
            WHERE pa.property_id = %s AND pa.amenity_id = %s
        """, (property_id, update_data.new_amenity_id))
        
        updated = cursor.fetchone()
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated association"
            )
            
        return PropertyAmenityResponse(**updated)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating property amenity: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/property/{property_id}", response_model=List[PropertyAmenityResponse])
async def get_property_amenities(property_id: int):
    verify_property_exists(property_id)
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT pa.*, a.amenity_name, a.amenity_category, a.icon_url
            FROM property_amenities pa
            JOIN amenities a ON pa.amenity_id = a.amenity_id
            WHERE pa.property_id = %s AND a.is_active = TRUE
        """, (property_id,))
        amenities = cursor.fetchall()
        return amenities
    finally:
        cursor.close()
        conn.close()

@router.delete("/", status_code=status.HTTP_200_OK)
async def remove_amenity_from_property(property_id: int, amenity_id: int):
    verify_property_exists(property_id)
    verify_amenity_exists(amenity_id)
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM property_amenities 
            WHERE property_id = %s AND amenity_id = %s
        """, (property_id, amenity_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Amenity not associated with this property"
            )
        conn.commit()
        return {"message": "Amenity removed from property successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing amenity from property: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()