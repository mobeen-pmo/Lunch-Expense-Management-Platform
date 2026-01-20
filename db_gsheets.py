"""
Google Sheets Database Adapter for Multi-Tenant Lunch Management Platform
Developed by Software Bazaar IT Solutions

This module provides Google Sheets-based storage for production deployment
on platforms like Streamlit Community Cloud where local file storage is not persistent.
"""

import json
import os
import time
from functools import wraps
from typing import Optional, List, Dict
import streamlit as st

# Simple retry decorator for API calls
def retry_on_api_error(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e)
                    # Handle specific API errors
                    if "429" in error_msg or "quota" in error_msg.lower():
                        time.sleep(delay * (2 ** retries))  # Exponential backoff
                        retries += 1
                        if retries == max_retries:
                            st.error(f"System busy. Please try again in a moment. (Rate limit exceeded)")
                            raise e
                    elif "400" in error_msg and "already exists" in error_msg:
                        # Be tolerant if sheet already exists
                        return None 
                    else:
                        raise e
            return None
        return wrapper
    return decorator

# Check if we're running on Streamlit Cloud (has secrets configured)
def is_gsheets_available() -> bool:
    """Check if Google Sheets credentials are available"""
    try:
        return "gcp_service_account" in st.secrets and "gsheets" in st.secrets
    except:
        return False

# Initialize gspread connection only when needed
_client = None
_spreadsheet = None

def get_gspread_client():
    """Get or create gspread client"""
    global _client
    if _client is None:
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=scopes
            )
            _client = gspread.authorize(credentials)
        except Exception as e:
            st.error(f"Failed to connect to Google Sheets: {e}")
            return None
    return _client

def get_spreadsheet():
    """Get or open the spreadsheet"""
    global _spreadsheet
    if _spreadsheet is None:
        client = get_gspread_client()
        if client:
            try:
                spreadsheet_id = st.secrets["gsheets"]["spreadsheet_id"]
                _spreadsheet = client.open_by_key(spreadsheet_id)
            except Exception as e:
                st.error(f"Failed to open spreadsheet: {e}")
                return None
    return _spreadsheet

# Cache spreadsheet instance
@st.cache_resource(ttl=3600)
def get_cached_spreadsheet():
    return get_spreadsheet()

def get_or_create_worksheet(name: str):
    """Get worksheet by name, create if doesn't exist"""
    # Use cached spreadsheet instance if possible, or get fresh one
    spreadsheet = get_cached_spreadsheet() or get_spreadsheet()
    if not spreadsheet:
        return None
    
    try:
        return spreadsheet.worksheet(name)
    except:
        # Worksheet doesn't exist or other error
        try:
            return spreadsheet.add_worksheet(title=name, rows=1000, cols=20)
        except Exception as create_error:
            error_msg = str(create_error)
            
            # If it says it exists, try getting it again (race condition)
            if "already exists" in error_msg:
                try:
                    return spreadsheet.worksheet(name)
                except:
                    pass
            
            if "403" in error_msg or "permission" in error_msg.lower():
                st.error("""
                    ⚠️ **Google Sheets Permission Error**
                    
                    Please share your spreadsheet with:
                    `lunch-db-bot@lunch-expense.iam.gserviceaccount.com`
                    
                    Give it **Editor** access.
                """)
            elif "429" in error_msg:
                st.warning("High traffic - slowing down requests...")
                time.sleep(2)
            
            return None

# ==================== SUPER ADMIN ====================
def get_super_admin_gsheets() -> Optional[Dict]:
    """Get super admin from Google Sheets"""
    ws = get_or_create_worksheet("super_admin")
    if not ws:
        return None
    
    try:
        records = ws.get_all_records()
        if records:
            return records[0]
        return None
    except:
        return None

def save_super_admin_gsheets(admin_data: Dict):
    """Save super admin to Google Sheets"""
    ws = get_or_create_worksheet("super_admin")
    if not ws:
        return
    
    # Clear and write
    ws.clear()
    ws.append_row(["email", "password_hash", "created_at"])
    ws.append_row([
        admin_data.get("email", ""),
        admin_data.get("password_hash", ""),
        admin_data.get("created_at", datetime.now().isoformat())
    ])

# ==================== COMPANIES ====================
def get_all_companies_gsheets() -> List[Dict]:
    """Get all companies from Google Sheets"""
    ws = get_or_create_worksheet("companies")
    if not ws:
        return []
    
    try:
        records = ws.get_all_records()
        # Convert is_active string to boolean
        for r in records:
            if isinstance(r.get("is_active"), str):
                r["is_active"] = r["is_active"].lower() == "true"
        return records
    except:
        return []

def save_all_companies_gsheets(companies: List[Dict]):
    """Save all companies to Google Sheets"""
    ws = get_or_create_worksheet("companies")
    if not ws:
        return
    
    # Clear and rewrite
    ws.clear()
    
    if not companies:
        ws.append_row(["id", "name", "admin_name", "admin_email", "password_hash", "created_at", "is_active"])
        return
    
    # Header
    headers = ["id", "name", "admin_name", "admin_email", "password_hash", "created_at", "is_active"]
    ws.append_row(headers)
    
    # Data rows
    for company in companies:
        row = [
            company.get("id", ""),
            company.get("name", ""),
            company.get("admin_name", ""),
            company.get("admin_email", ""),
            company.get("password_hash", ""),
            company.get("created_at", ""),
            str(company.get("is_active", True))
        ]
        ws.append_row(row)

# ==================== COMPANY DATA ====================
def load_company_data_gsheets(company_id: str) -> Optional[Dict]:
    """Load company data from Google Sheets"""
    ws = get_or_create_worksheet("company_data")
    if not ws:
        return None
    
    try:
        records = ws.get_all_records()
        for r in records:
            if r.get("company_id") == company_id:
                return json.loads(r.get("data_json", "{}"))
        return None
    except:
        return None

def save_company_data_gsheets(company_id: str, data: Dict):
    """Save company data to Google Sheets"""
    ws = get_or_create_worksheet("company_data")
    if not ws:
        return
    
    try:
        # Find existing row
        records = ws.get_all_records()
        row_idx = None
        for idx, r in enumerate(records):
            if r.get("company_id") == company_id:
                row_idx = idx + 2  # +2 for header and 1-indexing
                break
        
        data_json = json.dumps(data, default=str)
        
        if row_idx:
            # Update existing
            ws.update_cell(row_idx, 2, data_json)
            ws.update_cell(row_idx, 3, datetime.now().isoformat())
        else:
            # Check if header exists
            try:
                header = ws.row_values(1)
                if not header:
                    ws.append_row(["company_id", "data_json", "updated_at"])
            except:
                ws.append_row(["company_id", "data_json", "updated_at"])
            
            # Add new row
            ws.append_row([company_id, data_json, datetime.now().isoformat()])
    except Exception as e:
        st.error(f"Error saving company data: {e}")

def delete_company_data_gsheets(company_id: str):
    """Delete company data from Google Sheets"""
    ws = get_or_create_worksheet("company_data")
    if not ws:
        return
    
    try:
        records = ws.get_all_records()
        for idx, r in enumerate(records):
            if r.get("company_id") == company_id:
                ws.delete_rows(idx + 2)  # +2 for header and 1-indexing
                break
    except:
        pass

# ==================== OTP STORE ====================
def get_otp_store_gsheets() -> Dict:
    """Get OTP store from Google Sheets"""
    ws = get_or_create_worksheet("otp_store")
    if not ws:
        return {}
    
    try:
        records = ws.get_all_records()
        otp_store = {}
        for r in records:
            email = r.get("email", "")
            if email:
                otp_store[email] = {
                    "otp": r.get("otp", ""),
                    "created_at": r.get("created_at", ""),
                    "expires_at": r.get("expires_at", "")
                }
        return otp_store
    except:
        return {}

def save_otp_gsheets(email: str, otp_data: Dict):
    """Save OTP to Google Sheets"""
    ws = get_or_create_worksheet("otp_store")
    if not ws:
        return
    
    try:
        # Find existing row for this email
        records = ws.get_all_records()
        row_idx = None
        for idx, r in enumerate(records):
            if r.get("email", "").lower() == email.lower():
                row_idx = idx + 2
                break
        
        if row_idx:
            # Update existing
            ws.update_cell(row_idx, 2, otp_data.get("otp", ""))
            ws.update_cell(row_idx, 3, otp_data.get("created_at", ""))
            ws.update_cell(row_idx, 4, otp_data.get("expires_at", ""))
        else:
            # Check header
            try:
                header = ws.row_values(1)
                if not header:
                    ws.append_row(["email", "otp", "created_at", "expires_at"])
            except:
                ws.append_row(["email", "otp", "created_at", "expires_at"])
            
            # Add new
            ws.append_row([
                email,
                otp_data.get("otp", ""),
                otp_data.get("created_at", ""),
                otp_data.get("expires_at", "")
            ])
    except Exception as e:
        st.error(f"Error saving OTP: {e}")

def delete_otp_gsheets(email: str):
    """Delete OTP from Google Sheets"""
    ws = get_or_create_worksheet("otp_store")
    if not ws:
        return
    
    try:
        records = ws.get_all_records()
        for idx, r in enumerate(records):
            if r.get("email", "").lower() == email.lower():
                ws.delete_rows(idx + 2)
                break
    except:
        pass
