from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import time, timedelta
from decimal import Decimal
from app.db import get_connection
from app.Token.verify_api import verify_token
from app.models.house_rules import HouseRuleCreate,HouseRuleUpdate,HouseRuleInDB,HouseRuleResponse
from app.models.properties import PropertyResponse, PropertyCreate, PropertyUpdate
import mysql.connector

router = APIRouter(prefix="/house_rules", tags=["House_rules"], dependencies=[Depends(verify_token)],  # Applies to all endpoints
    responses={401: {"description": "Unauthorized"}})


# Utility function to check if property exists
def check_property_exists(conn, property_id: int):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM properties WHERE property_id = %s", (property_id,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()

@router.get("/", response_model=List[HouseRuleResponse])
async def get_all_house_rules(property_id: int, skip: int = 0, limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if property exists first
        if not check_property_exists(conn, property_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        cursor.execute("""
            SELECT rule_id, property_id, rule_text, created_at
            FROM house_rules
            WHERE property_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (property_id, limit, skip))
        rules = cursor.fetchall()
        return [HouseRuleResponse(**rule) for rule in rules]
    finally:
        cursor.close()
        conn.close()

@router.post("/", response_model=HouseRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_house_rule(rule_data: HouseRuleCreate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if property exists first
        if not check_property_exists(conn, rule_data.property_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        cursor.execute("""
            INSERT INTO house_rules 
            (property_id, rule_text)
            VALUES (%s, %s)
        """, (
            rule_data.property_id,
            rule_data.rule_text
        ))
        conn.commit()
        
        rule_id = cursor.lastrowid
        cursor.execute("""
            SELECT rule_id, property_id, rule_text, created_at
            FROM house_rules
            WHERE rule_id = %s
        """, (rule_id,))
        new_rule = cursor.fetchone()
        
        return HouseRuleResponse(**new_rule)
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {err}"
        )
    finally:
        cursor.close()
        conn.close()

# [Keep the existing get_house_rule_by_id, update_house_rule, and delete_house_rule endpoints]
# They don't need property existence checks since they work with rule_id directly

# Example of how to modify the PUT endpoint if you want to verify the property_id matches
@router.put("/{rule_id}", response_model=HouseRuleResponse)
async def update_house_rule(rule_id: int, rule_data: HouseRuleUpdate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # First get the existing rule to verify property_id
        cursor.execute("""
            SELECT property_id FROM house_rules WHERE rule_id = %s
        """, (rule_id,))
        existing_rule = cursor.fetchone()
        
        if not existing_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="House rule not found"
            )

        # If you want to verify the property exists (optional)
        if not check_property_exists(conn, existing_rule['property_id']):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )

        cursor.execute("""
            UPDATE house_rules 
            SET rule_text = %s
            WHERE rule_id = %s
        """, (
            rule_data.rule_text,
            rule_id
        ))
        conn.commit()
        
        cursor.execute("""
            SELECT rule_id, property_id, rule_text, created_at
            FROM house_rules
            WHERE rule_id = %s
        """, (rule_id,))
        updated_rule = cursor.fetchone()
        
        return HouseRuleResponse(**updated_rule)
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {err}"
        )
    finally:
        cursor.close()
        conn.close()

@router.get("/{rule_id}", response_model=HouseRuleResponse)
async def get_house_rule_by_id(rule_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT rule_id, property_id, rule_text, created_at
            FROM house_rules
            WHERE rule_id = %s
        """, (rule_id,))
        rule = cursor.fetchone()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="House rule not found"
            )
        return HouseRuleResponse(**rule)
    finally:
        cursor.close()
        conn.close()

@router.delete("/{rule_id}", status_code=status.HTTP_200_OK)
async def delete_house_rule(rule_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # First get the rule to verify it exists and get property_id
        cursor.execute("""
            SELECT property_id FROM house_rules WHERE rule_id = %s
        """, (rule_id,))
        rule = cursor.fetchone()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="House rule not found"
            )

        # Optional: Verify the associated property exists
        if not check_property_exists(conn, rule['property_id']):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated property not found"
            )

        # Delete the rule
        cursor.execute("DELETE FROM house_rules WHERE rule_id = %s", (rule_id,))
        conn.commit()
        
        return {
            "status": "success",
            "message": "House rule deleted successfully",
            "rule_id": rule_id
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