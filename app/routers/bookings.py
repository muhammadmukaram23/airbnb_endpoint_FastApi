from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import time, timedelta
from decimal import Decimal
from app.db import get_connection
from app.Token.verify_api import verify_token
from app.models.bookings import BookingStatus,PaymentStatus,BookingCreate,BookingResponse,BookingUpdate,BookingInDB
from app.models.properties import PropertyResponse, PropertyCreate, PropertyUpdate
from app.models.users import UserCreate,UserUpdate,UserResponse,UserInDB

import mysql.connector

router = APIRouter(prefix="/bookings", tags=["bookings"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})


# Utility functions
async def check_property_exists(conn, property_id: int):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM properties WHERE property_id = %s", (property_id,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()

async def check_user_exists(conn, user_id: int):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()

# Endpoints
@router.get("/", response_model=List[BookingResponse])
async def get_all_bookings(
    property_id: Optional[int] = None,
    guest_id: Optional[int] = None,
    status: Optional[BookingStatus] = None,
    skip: int = 0,
    limit: int = 100
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        base_query = """
            SELECT booking_id, property_id, guest_id, check_in_date, check_out_date,
                   num_guests, total_nights, base_price, cleaning_fee, service_fee,
                   taxes, total_amount, booking_status, payment_status,
                   special_requests, cancellation_reason, cancelled_at,
                   created_at, updated_at
            FROM bookings
            WHERE 1=1
        """
        params = []
        
        if property_id:
            base_query += " AND property_id = %s"
            params.append(property_id)
        if guest_id:
            base_query += " AND guest_id = %s"
            params.append(guest_id)
        if status:
            base_query += " AND booking_status = %s"
            params.append(status.value)
            
        base_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(base_query, params)
        bookings = cursor.fetchall()
        return [BookingResponse(**booking) for booking in bookings]
    finally:
        cursor.close()
        conn.close()

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking_by_id(booking_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT booking_id, property_id, guest_id, check_in_date, check_out_date,
                   num_guests, total_nights, base_price, cleaning_fee, service_fee,
                   taxes, total_amount, booking_status, payment_status,
                   special_requests, cancellation_reason, cancelled_at,
                   created_at, updated_at
            FROM bookings
            WHERE booking_id = %s
        """, (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        return BookingResponse(**booking)
    finally:
        cursor.close()
        conn.close()

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(booking_data: BookingCreate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Validate property and guest exist
        if not await check_property_exists(conn, booking_data.property_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
            
        if not await check_user_exists(conn, booking_data.guest_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest user not found"
            )
        
        # Calculate total nights
        total_nights = (booking_data.check_out_date - booking_data.check_in_date).days
        
        cursor.execute("""
            INSERT INTO bookings (
                property_id, guest_id, check_in_date, check_out_date,
                num_guests, total_nights, base_price, cleaning_fee,
                service_fee, taxes, total_amount, booking_status,
                payment_status, special_requests
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            booking_data.property_id,
            booking_data.guest_id,
            booking_data.check_in_date,
            booking_data.check_out_date,
            booking_data.num_guests,
            total_nights,
            booking_data.base_price,
            booking_data.cleaning_fee,
            booking_data.service_fee,
            booking_data.taxes,
            booking_data.total_amount,
            booking_data.booking_status.value,
            booking_data.payment_status.value,
            booking_data.special_requests
        ))
        conn.commit()
        
        booking_id = cursor.lastrowid
        cursor.execute("""
            SELECT * FROM bookings WHERE booking_id = %s
        """, (booking_id,))
        new_booking = cursor.fetchone()
        
        return BookingResponse(**new_booking)
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {err}"
        )
    finally:
        cursor.close()
        conn.close()

@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: int,
    booking_data: BookingUpdate
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if booking exists
        cursor.execute("SELECT booking_id FROM bookings WHERE booking_id = %s", (booking_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Build dynamic update query
        update_fields = []
        params = []
        
        if booking_data.check_in_date is not None:
            update_fields.append("check_in_date = %s")
            params.append(booking_data.check_in_date)
        if booking_data.check_out_date is not None:
            update_fields.append("check_out_date = %s")
            params.append(booking_data.check_out_date)
        if booking_data.num_guests is not None:
            update_fields.append("num_guests = %s")
            params.append(booking_data.num_guests)
        if booking_data.base_price is not None:
            update_fields.append("base_price = %s")
            params.append(booking_data.base_price)
        if booking_data.cleaning_fee is not None:
            update_fields.append("cleaning_fee = %s")
            params.append(booking_data.cleaning_fee)
        if booking_data.service_fee is not None:
            update_fields.append("service_fee = %s")
            params.append(booking_data.service_fee)
        if booking_data.taxes is not None:
            update_fields.append("taxes = %s")
            params.append(booking_data.taxes)
        if booking_data.total_amount is not None:
            update_fields.append("total_amount = %s")
            params.append(booking_data.total_amount)
        if booking_data.booking_status is not None:
            update_fields.append("booking_status = %s")
            params.append(booking_data.booking_status.value)
        if booking_data.payment_status is not None:
            update_fields.append("payment_status = %s")
            params.append(booking_data.payment_status.value)
        if booking_data.special_requests is not None:
            update_fields.append("special_requests = %s")
            params.append(booking_data.special_requests)
        if booking_data.cancellation_reason is not None:
            update_fields.append("cancellation_reason = %s")
            params.append(booking_data.cancellation_reason)
            update_fields.append("cancelled_at = CURRENT_TIMESTAMP")
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        query = f"UPDATE bookings SET {', '.join(update_fields)} WHERE booking_id = %s"
        params.append(booking_id)
        
        cursor.execute(query, params)
        conn.commit()
        
        # Fetch updated booking
        cursor.execute("SELECT * FROM bookings WHERE booking_id = %s", (booking_id,))
        updated_booking = cursor.fetchone()
        
        return BookingResponse(**updated_booking)
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {err}"
        )
    finally:
        cursor.close()
        conn.close()

@router.delete("/{booking_id}", status_code=status.HTTP_200_OK)
async def delete_booking(booking_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if booking exists
        cursor.execute("SELECT booking_id FROM bookings WHERE booking_id = %s", (booking_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        cursor.execute("DELETE FROM bookings WHERE booking_id = %s", (booking_id,))
        conn.commit()
        
        return {
            "status": "success",
            "message": "Booking deleted successfully",
            "booking_id": booking_id
        }
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {err}"
        )
    finally:
        cursor.close()
        conn.close()