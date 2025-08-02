from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.db import get_connection
from app.models.users import UserCreate,UserUpdate,UserResponse,UserInDB
from app.Token.verify_api import verify_token
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})



@router.get("/", response_model=List[UserResponse])
async def get_users(skip: int = 0, limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM users LIMIT %s OFFSET %s", (limit, skip))
        users = cursor.fetchall()
        return [UserResponse(**user) for user in users]
    finally:
        cursor.close()
        conn.close()

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserResponse(**user)
    finally:
        cursor.close()
        conn.close()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if email already exists
        cursor.execute("SELECT email FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Insert new user
        query = """
        INSERT INTO users (
            email, password_hash, first_name, last_name, phone, 
            date_of_birth, profile_picture_url, bio, is_host, 
            is_verified, government_id_verified
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            user.email, user.password_hash, user.first_name, user.last_name,
            user.phone, user.date_of_birth, user.profile_picture_url, user.bio,
            user.is_host, user.is_verified, user.government_id_verified
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        # Get the newly created user
        user_id = cursor.lastrowid
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        new_user = cursor.fetchone()
        
        return UserResponse(**new_user)
    finally:
        cursor.close()
        conn.close()


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        existing_user = cursor.fetchone()
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Build dynamic update query
        update_fields = []
        values = []
        
        if user.email is not None:
            # Check if new email is already taken by another user
            cursor.execute(
                "SELECT user_id FROM users WHERE email = %s AND user_id != %s",
                (user.email, user_id)
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use by another user"
                )
            update_fields.append("email = %s")
            values.append(user.email)
        
        # Add other fields
        fields_to_update = [
            ("first_name", user.first_name),
            ("last_name", user.last_name),
            ("phone", user.phone),
            ("date_of_birth", user.date_of_birth),
            ("profile_picture_url", user.profile_picture_url),
            ("bio", user.bio),
            ("is_host", user.is_host),
            ("is_verified", user.is_verified),
            ("government_id_verified", user.government_id_verified),
            ("password_hash", user.password_hash)
        ]
        
        for field, value in fields_to_update:
            if value is not None:
                update_fields.append(f"{field} = %s")
                values.append(value)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Execute update
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s"
        values.append(user_id)
        cursor.execute(query, values)
        conn.commit()
        
        # Return updated user
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        updated_user = cursor.fetchone()
        return UserResponse(**updated_user)
    finally:
        cursor.close()
        conn.close()

@router.delete("/{user_id}", status_code=status.HTTP_200_OK, response_model=dict)
async def delete_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        conn.commit()
        return {"message": "User deleted successfully"}
    finally:
        cursor.close()
        conn.close()