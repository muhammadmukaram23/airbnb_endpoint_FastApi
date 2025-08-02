from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import time, timedelta
from decimal import Decimal
from app.db import get_connection
from app.Token.verify_api import verify_token
from app.models.properties import PropertyResponse, PropertyCreate, PropertyUpdate
from app.models.users import UserResponse
from app.models.property_categories import PropertyCategoryResponse
import mysql.connector

router = APIRouter(prefix="/property", tags=["property"], dependencies=[Depends(verify_token)])

def db_time_to_python(db_time):
    """Convert database time (timedelta or string) to Python time object"""
    if db_time is None:
        return None
    if isinstance(db_time, timedelta):
        seconds = db_time.total_seconds()
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return time(hour=hours, minute=minutes)
    elif isinstance(db_time, str):
        return time.fromisoformat(db_time)
    return db_time

def db_time_to_python(db_time):
    """Convert database time (timedelta or string) to Python time object"""
    if db_time is None:
        return None
    if isinstance(db_time, timedelta):
        seconds = db_time.total_seconds()
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return time(hour=hours, minute=minutes)
    elif isinstance(db_time, str):
        return time.fromisoformat(db_time)
    return db_time

# Helper function to verify host exists
def verify_host_exists(host_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT user_id FROM users 
            WHERE user_id = %s AND is_host = TRUE
        """, (host_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Host not found or not a host"
            )
    finally:
        cursor.close()
        conn.close()

# Helper function to verify category exists
def verify_category_exists(category_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT category_id FROM property_categories 
            WHERE category_id = %s AND is_active = TRUE
        """, (category_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or inactive"
            )
    finally:
        cursor.close()
        conn.close()

@router.get("/", response_model=List[PropertyResponse])
async def get_properties(
    skip: int = 0,
    limit: int = 100,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    property_type: Optional[str] = None,
    category_id: Optional[int] = None
):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        base_query = """
            SELECT p.*, 
                   u.first_name as host_first_name,
                   u.last_name as host_last_name,
                   pc.category_name
            FROM properties p
            JOIN users u ON p.host_id = u.user_id
            JOIN property_categories pc ON p.category_id = pc.category_id
            WHERE p.is_active = TRUE
        """
        params = []
        
        # Build filters
        filters = []
        if min_price is not None:
            filters.append("p.price_per_night >= %s")
            params.append(float(min_price))
        if max_price is not None:
            filters.append("p.price_per_night <= %s")
            params.append(float(max_price))
        if property_type is not None:
            filters.append("p.property_type = %s")
            params.append(property_type)
        if category_id is not None:
            filters.append("p.category_id = %s")
            params.append(category_id)
        
        if filters:
            base_query += " AND " + " AND ".join(filters)
        
        base_query += " LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(base_query, params)
        properties = cursor.fetchall()
        
        # Convert time fields
        for prop in properties:
            prop['check_in_time'] = db_time_to_python(prop.get('check_in_time'))
            prop['check_out_time'] = db_time_to_python(prop.get('check_out_time'))
        
        return [PropertyResponse(**prop) for prop in properties]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching properties: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(property_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.*, 
                   u.first_name as host_first_name,
                   u.last_name as host_last_name,
                   pc.category_name
            FROM properties p
            JOIN users u ON p.host_id = u.user_id
            JOIN property_categories pc ON p.category_id = pc.category_id
            WHERE p.property_id = %s
        """, (property_id,))
        property = cursor.fetchone()
        if not property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        return PropertyResponse(**property)
    finally:
        cursor.close()
        conn.close()

@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(property: PropertyCreate):
    verify_host_exists(property.host_id)
    verify_category_exists(property.category_id)
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check for duplicate property title for this host
        cursor.execute("""
            SELECT property_id FROM properties 
            WHERE host_id = %s AND title = %s
        """, (property.host_id, property.title))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property with this title already exists for this host"
            )
        
        # Insert new property
        cursor.execute("""
            INSERT INTO properties (
                host_id, category_id, title, description, property_type,
                max_guests, bedrooms, beds, bathrooms, price_per_night,
                cleaning_fee, service_fee_percentage, minimum_nights,
                maximum_nights, check_in_time, check_out_time, instant_book
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            property.host_id,
            property.category_id,
            property.title,
            property.description,
            property.property_type.value,
            property.max_guests,
            property.bedrooms,
            property.beds,
            float(property.bathrooms),
            float(property.price_per_night),
            float(property.cleaning_fee),
            float(property.service_fee_percentage),
            property.minimum_nights,
            property.maximum_nights,
            property.check_in_time.strftime('%H:%M:%S'),
            property.check_out_time.strftime('%H:%M:%S'),
            property.instant_book
        ))
        conn.commit()
        
        # Get the newly created property
        property_id = cursor.lastrowid
        cursor.execute("""
            SELECT p.*, 
                   u.first_name as host_first_name,
                   u.last_name as host_last_name,
                   pc.category_name
            FROM properties p
            JOIN users u ON p.host_id = u.user_id
            JOIN property_categories pc ON p.category_id = pc.category_id
            WHERE p.property_id = %s
        """, (property_id,))
        new_property = cursor.fetchone()
        
        # Convert database time formats to Python time objects
        new_property['check_in_time'] = db_time_to_python(new_property['check_in_time'])
        new_property['check_out_time'] = db_time_to_python(new_property['check_out_time'])
        
        return PropertyResponse(**new_property)
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating property: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(property_id: int, property: PropertyUpdate):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if property exists
        cursor.execute("SELECT * FROM properties WHERE property_id = %s", (property_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Verify relationships if being updated
        if property.host_id is not None:
            verify_host_exists(property.host_id)
        if property.category_id is not None:
            verify_category_exists(property.category_id)
        
        # Build dynamic update query
        update_fields = []
        params = []
        
        if property.host_id is not None:
            update_fields.append("host_id = %s")
            params.append(property.host_id)
        if property.category_id is not None:
            update_fields.append("category_id = %s")
            params.append(property.category_id)
        if property.title is not None:
            update_fields.append("title = %s")
            params.append(property.title)
        if property.description is not None:
            update_fields.append("description = %s")
            params.append(property.description)
        if property.property_type is not None:
            update_fields.append("property_type = %s")
            params.append(property.property_type.value)
        if property.max_guests is not None:
            update_fields.append("max_guests = %s")
            params.append(property.max_guests)
        if property.bedrooms is not None:
            update_fields.append("bedrooms = %s")
            params.append(property.bedrooms)
        if property.beds is not None:
            update_fields.append("beds = %s")
            params.append(property.beds)
        if property.bathrooms is not None:
            update_fields.append("bathrooms = %s")
            params.append(float(property.bathrooms))
        if property.price_per_night is not None:
            update_fields.append("price_per_night = %s")
            params.append(float(property.price_per_night))
        if property.cleaning_fee is not None:
            update_fields.append("cleaning_fee = %s")
            params.append(float(property.cleaning_fee))
        if property.service_fee_percentage is not None:
            update_fields.append("service_fee_percentage = %s")
            params.append(float(property.service_fee_percentage))
        if property.minimum_nights is not None:
            update_fields.append("minimum_nights = %s")
            params.append(property.minimum_nights)
        if property.maximum_nights is not None:
            update_fields.append("maximum_nights = %s")
            params.append(property.maximum_nights)
        if property.check_in_time is not None:
            update_fields.append("check_in_time = %s")
            params.append(property.check_in_time.strftime('%H:%M:%S'))
        if property.check_out_time is not None:
            update_fields.append("check_out_time = %s")
            params.append(property.check_out_time.strftime('%H:%M:%S'))
        if property.instant_book is not None:
            update_fields.append("instant_book = %s")
            params.append(property.instant_book)
        if property.is_active is not None:
            update_fields.append("is_active = %s")
            params.append(property.is_active)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Execute update
        query = f"UPDATE properties SET {', '.join(update_fields)} WHERE property_id = %s"
        params.append(property_id)
        cursor.execute(query, params)
        conn.commit()
        
        # Return updated property with joins
        cursor.execute("""
            SELECT p.*, 
                   u.first_name as host_first_name,
                   u.last_name as host_last_name,
                   pc.category_name
            FROM properties p
            JOIN users u ON p.host_id = u.user_id
            JOIN property_categories pc ON p.category_id = pc.category_id
            WHERE p.property_id = %s
        """, (property_id,))
        updated = cursor.fetchone()
        
        # Convert time fields
        updated['check_in_time'] = db_time_to_python(updated.get('check_in_time'))
        updated['check_out_time'] = db_time_to_python(updated.get('check_out_time'))
        
        return PropertyResponse(**updated)
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating property: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.delete("/{property_id}", status_code=status.HTTP_200_OK)
async def delete_property(property_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Soft delete (recommended instead of actual deletion)
        cursor.execute("""
            UPDATE properties 
            SET is_active = FALSE 
            WHERE property_id = %s
        """, (property_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        conn.commit()
        return {"message": "Property deactivated successfully"}
    finally:
        cursor.close()
        conn.close()