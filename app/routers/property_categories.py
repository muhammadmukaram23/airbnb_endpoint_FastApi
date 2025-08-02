from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
from app.db import get_connection
from app.models.property_categories import PropertyCategoryCreate,PropertyCategoryInDB,PropertyCategoryUpdate,PropertyCategoryResponse
from app.Token.verify_api import verify_token
from datetime import datetime
from typing import List
from passlib.context import CryptContext
import mysql.connector

router = APIRouter(prefix="/property_categories", tags=["property_categories"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})




@router.get("/", response_model=List[PropertyCategoryResponse])
async def get_all_categories(skip: int = 0, limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM property_categories 
            LIMIT %s OFFSET %s
        """, (limit, skip))
        categories = cursor.fetchall()
        return [PropertyCategoryResponse(**cat) for cat in categories]
    finally:
        cursor.close()
        conn.close()

@router.get("/{category_id}", response_model=PropertyCategoryResponse)
async def get_category_by_id(category_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM property_categories 
            WHERE category_id = %s
        """, (category_id,))
        category = cursor.fetchone()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        return PropertyCategoryResponse(**category)
    finally:
        cursor.close()
        conn.close()

@router.post("/", response_model=PropertyCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(category: PropertyCategoryCreate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if category name already exists
        cursor.execute("""
            SELECT category_name FROM property_categories 
            WHERE category_name = %s
        """, (category.category_name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name already exists"
            )
        
        # Insert new category
        cursor.execute("""
            INSERT INTO property_categories (
                category_name, description, icon_url, is_active
            ) VALUES (%s, %s, %s, %s)
        """, (
            category.category_name,
            category.description,
            str(category.icon_url) if category.icon_url else None,
            category.is_active
        ))
        conn.commit()
        
        # Get the newly created category
        category_id = cursor.lastrowid
        cursor.execute("""
            SELECT * FROM property_categories 
            WHERE category_id = %s
        """, (category_id,))
        new_category = cursor.fetchone()
        return PropertyCategoryResponse(**new_category)
    finally:
        cursor.close()
        conn.close()

@router.put("/{category_id}", response_model=PropertyCategoryResponse)
async def update_category(category_id: int, category: PropertyCategoryUpdate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if category exists
        cursor.execute("""
            SELECT * FROM property_categories 
            WHERE category_id = %s
        """, (category_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check if new name conflicts with other categories
        if category.category_name is not None:
            cursor.execute("""
                SELECT category_id FROM property_categories 
                WHERE category_name = %s AND category_id != %s
            """, (category.category_name, category_id))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category name already in use"
                )
        
        # Build dynamic update query
        update_fields = []
        values = []
        
        if category.category_name is not None:
            update_fields.append("category_name = %s")
            values.append(category.category_name)
        if category.description is not None:
            update_fields.append("description = %s")
            values.append(category.description)
        if category.icon_url is not None:
            update_fields.append("icon_url = %s")
            values.append(str(category.icon_url))
        if category.is_active is not None:
            update_fields.append("is_active = %s")
            values.append(category.is_active)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Execute update
        query = f"""
            UPDATE property_categories 
            SET {', '.join(update_fields)} 
            WHERE category_id = %s
        """
        values.append(category_id)
        cursor.execute(query, values)
        conn.commit()
        
        # Return updated category
        cursor.execute("""
            SELECT * FROM property_categories 
            WHERE category_id = %s
        """, (category_id,))
        updated = cursor.fetchone()
        return PropertyCategoryResponse(**updated)
    finally:
        cursor.close()
        conn.close()

@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM property_categories 
            WHERE category_id = %s
        """, (category_id,))
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        conn.commit()
        return {"message": "Category deleted successfully"}
    finally:
        cursor.close()
        conn.close()