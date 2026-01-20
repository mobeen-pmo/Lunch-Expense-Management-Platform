"""
Firestore Database Adapter for Lunch Management System
Developed by Software Bazaar IT Solutions
"""

import streamlit as st
import json
from datetime import datetime

# Initialize Firestore
_db = None

def get_firestore_client():
    """Get Firestore client, initializing if needed"""
    global _db
    
    if _db is not None:
        return _db
    
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # Check if secrets are available
        if "firebase" not in st.secrets:
            return None
        
        # Check if already initialized
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        
        _db = firestore.client()
        return _db
        
    except Exception as e:
        print(f"Firestore init error: {e}")
        return None


# ==================== DATA OPERATIONS ====================

def load_firestore_data(key_type: str, record_id: str = None):
    """
    Load data from Firestore.
    key_type: 'super_admin', 'companies', 'company_data'
    """
    db = get_firestore_client()
    if not db:
        return None

    try:
        if key_type == "super_admin":
            doc = db.collection("config").document("super_admin").get()
            return doc.to_dict() if doc.exists else None
            
        elif key_type == "companies":
            docs = db.collection("companies").stream()
            return [doc.to_dict() for doc in docs]

        elif key_type == "company_data":
            if not record_id:
                return None
            doc = db.collection("company_data").document(record_id).get()
            return doc.to_dict() if doc.exists else None
            
    except Exception as e:
        print(f"Firestore read error ({key_type}): {e}")
        return None


def save_firestore_data(key_type: str, data, record_id: str = None):
    """
    Save data to Firestore.
    key_type: 'super_admin', 'companies', 'company_data'
    """
    db = get_firestore_client()
    if not db:
        return False

    try:
        if key_type == "super_admin":
            db.collection("config").document("super_admin").set(data)
            return True
            
        elif key_type == "companies":
            # For companies, we store as individual documents
            # First clear existing
            batch = db.batch()
            existing = db.collection("companies").stream()
            for doc in existing:
                batch.delete(doc.reference)
            batch.commit()
            
            # Add new
            for company in data:
                db.collection("companies").document(company["id"]).set(company)
            return True

        elif key_type == "company_data":
            if not record_id:
                return False
            # Add timestamp
            data["_updated_at"] = datetime.now().isoformat()
            db.collection("company_data").document(record_id).set(data)
            return True
            
    except Exception as e:
        print(f"Firestore write error ({key_type}): {e}")
        return False
