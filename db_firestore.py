
import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
from datetime import datetime
from typing import Optional, List, Dict

# Check availability
def is_firestore_available() -> bool:
    """Check if Firestore credentials are available"""
    try:
        return "gcp_service_account" in st.secrets
    except:
        return False

# Connection Management
_db_client = None

def get_db():
    """Get or create Firestore client"""
    global _db_client
    if _db_client is None:
        try:
            # Create credentials from secrets
            key_dict = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(key_dict)
            
            # Create client
            _db_client = firestore.Client(credentials=creds, project=key_dict["project_id"])
        except Exception as e:
            st.error(f"Failed to connect to Firestore: {str(e)}")
            return None
    return _db_client

# ==================== SUPER ADMIN ====================
def get_super_admin_firestore() -> Optional[Dict]:
    """Get super admin config"""
    db = get_db()
    if not db: return None
    
    try:
        doc = db.collection("super_admin").document("config").get()
        if doc.exists:
            return doc.to_dict()
        return None
    except:
        return None

def save_super_admin_firestore(admin_data: Dict):
    """Save super admin config"""
    db = get_db()
    if not db: return
    
    try:
        db.collection("super_admin").document("config").set(admin_data)
    except Exception as e:
        st.error(f"Firestore Save Error: {e}")

# ==================== COMPANIES ====================
def get_all_companies_firestore() -> List[Dict]:
    """Get all registered companies"""
    db = get_db()
    if not db: return []
    
    try:
        # We store companies as individual documents in 'companies' collection
        # ID is the doc ID
        docs = db.collection("companies").stream()
        companies = []
        for doc in docs:
            companies.append(doc.to_dict())
        return companies
    except:
        return []

def save_all_companies_firestore(companies: List[Dict]):
    """Save all companies. 
    Note: In Firestore we update/add individually, but to match the interface 
    which passes the FULL list, we should be careful. 
    Ideally we just update the modified one, but db_ops sends the whole list.
    We will sync the list to the collection."""
    db = get_db()
    if not db: return
    
    try:
        # Batch write for efficiency
        batch = db.batch()
        
        # We assume the list contains ALL companies. 
        # Existing companies loop
        for company in companies:
            ref = db.collection("companies").document(company["id"])
            batch.set(ref, company)
            
        # Commit
        batch.commit()
    except Exception as e:
        st.error(f"Firestore Save Error: {e}")

# ==================== COMPANY DATA ====================
def load_company_data_firestore(company_id: str) -> Optional[Dict]:
    """Load company data (employees, records, etc)"""
    db = get_db()
    if not db: return None
    
    try:
        # We store all company data in one large document to match the JSON structure logic
        # Collection: 'company_data', Document: company_id
        doc = db.collection("company_data").document(company_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except:
        return None

def save_company_data_firestore(company_id: str, data: Dict):
    """Save company data"""
    db = get_db()
    if not db: return
    
    try:
        db.collection("company_data").document(company_id).set(data)
    except Exception as e:
        st.error(f"Firestore Save Error: {e}")
        raise e

def delete_company_data_firestore(company_id: str):
    """Delete company data"""
    db = get_db()
    if not db: return
    
    try:
        db.collection("company_data").document(company_id).delete()
    except:
        pass

# ==================== OTP STORE ====================
def get_otp_store_firestore() -> Dict:
    """Get OTP store"""
    db = get_db()
    if not db: return {}
    
    try:
        docs = db.collection("otp_store").stream()
        store = {}
        for doc in docs:
            store[doc.id] = doc.to_dict()
        return store
    except:
        return {}

def save_otp_firestore(email: str, otp_data: Dict):
    """Save single OTP entry"""
    db = get_db()
    if not db: return
    
    try:
        # Use email as document ID
        db.collection("otp_store").document(email).set(otp_data)
    except Exception as e:
        raise e

def delete_otp_firestore(email: str):
    """Delete OTP entry"""
    db = get_db()
    if not db: return
    
    try:
        db.collection("otp_store").document(email).delete()
    except:
        pass
