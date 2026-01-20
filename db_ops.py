"""
Database operations for Multi-Tenant Lunch Management Platform
Developed by Software Bazaar IT Solutions

Features:
- Super Admin (Platform Owner)
- Multi-Company Support
- Role-based Access (Admin/Member)
- Data Isolation per Company
"""

import json
import os
import hashlib
import secrets
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
import uuid

# Default permissions for new employees
DEFAULT_PERMISSIONS = {
    "can_add_employees": False,
    "can_edit_employees": False,
    "can_delete_employees": False,
    "can_add_entries": True,        # Everyone can add their own entries
    "can_edit_entries": False,      # Edit any entry
    "can_view_all": False,          # View all employees' records
    "can_view_reports": False,
    "can_manage_settings": False,
    "can_invite": False,
}

# Admin gets all permissions
ADMIN_PERMISSIONS = {key: True for key in DEFAULT_PERMISSIONS}

DATA_DIR = "data"
SUPER_ADMIN_FILE = os.path.join(DATA_DIR, "super_admin.json")
COMPANIES_FILE = os.path.join(DATA_DIR, "companies.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

# ==================== SUPER ADMIN ====================
def get_super_admin():
    """Get super admin credentials"""
    if os.path.exists(SUPER_ADMIN_FILE):
        with open(SUPER_ADMIN_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Default super admin - Software Bazaar IT Solutions
    default_admin = {
        "email": "softwarebazaaritsolutions@gmail.com",
        "password_hash": hash_password("mobeen-pmo"),
        "created_at": datetime.now().isoformat()
    }
    save_super_admin(default_admin)
    return default_admin

def save_super_admin(admin_data):
    """Save super admin data"""
    with open(SUPER_ADMIN_FILE, 'w', encoding='utf-8') as f:
        json.dump(admin_data, f, indent=2)

def verify_super_admin(email: str, password: str) -> bool:
    """Verify super admin login"""
    admin = get_super_admin()
    return admin["email"].lower() == email.lower() and verify_password(password, admin["password_hash"])

def update_super_admin_password(new_password: str):
    """Update super admin password"""
    admin = get_super_admin()
    admin["password_hash"] = hash_password(new_password)
    save_super_admin(admin)

# ==================== COMPANIES ====================
def get_all_companies() -> List[Dict]:
    """Get all registered companies (for super admin)"""
    if os.path.exists(COMPANIES_FILE):
        with open(COMPANIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_all_companies(companies: List[Dict]):
    """Save all companies"""
    with open(COMPANIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=2, default=str)

def register_company(name: str, admin_name: str, admin_email: str, password: str) -> Dict:
    """Register a new company"""
    companies = get_all_companies()
    
    # Check if company name exists
    if any(c["name"].lower() == name.lower() for c in companies):
        raise ValueError("Company name already exists")
    
    # Check if email exists
    if any(c["admin_email"].lower() == admin_email.lower() for c in companies):
        raise ValueError("Email already registered")
    
    company = {
        "id": str(uuid.uuid4()),
        "name": name,
        "admin_name": admin_name,
        "admin_email": admin_email,
        "password_hash": hash_password(password),
        "created_at": datetime.now().isoformat(),
        "is_active": True
    }
    
    companies.append(company)
    save_all_companies(companies)
    
    # Initialize company data
    init_company_data(company["id"])
    
    return company

def verify_company_login(email: str, password: str) -> Optional[Dict]:
    """Verify company admin login"""
    companies = get_all_companies()
    for company in companies:
        if company["admin_email"].lower() == email.lower():
            if verify_password(password, company["password_hash"]):
                if company.get("is_active", True):
                    return company
                else:
                    raise ValueError("Company account is deactivated")
    return None

def get_company_by_id(company_id: str) -> Optional[Dict]:
    """Get company by ID"""
    companies = get_all_companies()
    return next((c for c in companies if c["id"] == company_id), None)

def update_company(company_id: str, **kwargs):
    """Update company details"""
    companies = get_all_companies()
    for company in companies:
        if company["id"] == company_id:
            company.update(kwargs)
            break
    save_all_companies(companies)

def toggle_company_status(company_id: str):
    """Toggle company active status (for super admin)"""
    companies = get_all_companies()
    for company in companies:
        if company["id"] == company_id:
            company["is_active"] = not company.get("is_active", True)
            break
    save_all_companies(companies)

def delete_company(company_id: str):
    """Delete a company and its data"""
    companies = get_all_companies()
    companies = [c for c in companies if c["id"] != company_id]
    save_all_companies(companies)
    
    # Delete data file
    file_path = get_company_data_file(company_id)
    if os.path.exists(file_path):
        os.remove(file_path)

def get_company_by_email(email: str) -> Optional[Dict]:
    """Get company by admin email"""
    companies = get_all_companies()
    return next((c for c in companies if c["admin_email"].lower() == email.lower()), None)

def reset_company_password(email: str, new_password: str) -> bool:
    """Reset company password by email"""
    companies = get_all_companies()
    for company in companies:
        if company["admin_email"].lower() == email.lower():
            company["password_hash"] = hash_password(new_password)
            save_all_companies(companies)
            return True
    return False

# ==================== COMPANY DATA MANAGEMENT ====================
def get_company_data_file(company_id: str) -> str:
    """Get the data file path for a company"""
    return os.path.join(DATA_DIR, f"company_{company_id}.json")

def init_company_data(company_id: str):
    """Initialize empty data for a new company"""
    data = {
        "employees": [],
        "members": [],  # Company members with roles
        "daily_records": [],
        "monthly_collections": [],
        "daily_shared_items": [],
        "menu_items": [
            {"id": "roti", "name": "Roti", "price": 20, "unit": "piece", "shared": False},
            {"id": "naan", "name": "Naan", "price": 25, "unit": "piece", "shared": False},
            {"id": "tea", "name": "Tea", "price": 15, "unit": "cup", "shared": False},
            {"id": "rice", "name": "Rice", "price": 0, "unit": "serving", "shared": True},
            {"id": "salan", "name": "Salan", "price": 0, "unit": "serving", "shared": True},
            {"id": "other", "name": "Other", "price": 0, "unit": "item", "shared": True},
        ]
    }
    save_company_data(company_id, data)

def load_company_data(company_id: str) -> Dict:
    """Load company data"""
    file_path = get_company_data_file(company_id)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure tea exists in menu items
            menu_ids = [m["id"] for m in data.get("menu_items", [])]
            if "tea" not in menu_ids:
                data["menu_items"].append(
                    {"id": "tea", "name": "Tea", "price": 15, "unit": "cup", "shared": False}
                )
            # Update tea to fixed price if it was shared
            for item in data["menu_items"]:
                if item["id"] == "tea" and item.get("shared", True):
                    item["shared"] = False
                    if item["price"] == 0:
                        item["price"] = 15
            if "members" not in data:
                data["members"] = []
            return data
    init_company_data(company_id)
    return load_company_data(company_id)

def save_company_data(company_id: str, data: Dict):
    """Save company data"""
    file_path = get_company_data_file(company_id)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

# ==================== MEMBER MANAGEMENT ====================
def add_member(company_id: str, name: str, email: str, password: str, role: str = "member") -> Dict:
    """Add a new member to company"""
    data = load_company_data(company_id)
    
    # Check if email exists
    if any(m["email"].lower() == email.lower() for m in data["members"]):
        raise ValueError("Email already exists in this company")
    
    member = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": role,  # 'admin' or 'member'
        "created_at": datetime.now().isoformat(),
        "is_active": True
    }
    
    data["members"].append(member)
    save_company_data(company_id, data)
    return member

def get_members(company_id: str) -> List[Dict]:
    """Get all members of a company"""
    data = load_company_data(company_id)
    return data.get("members", [])

def verify_member_login(company_id: str, email: str, password: str) -> Optional[Dict]:
    """Verify member login"""
    data = load_company_data(company_id)
    for member in data.get("members", []):
        if member["email"].lower() == email.lower():
            if verify_password(password, member["password_hash"]):
                if member.get("is_active", True):
                    return member
    return None

def update_member(company_id: str, member_id: str, **kwargs):
    """Update member details"""
    data = load_company_data(company_id)
    for member in data["members"]:
        if member["id"] == member_id:
            if "password" in kwargs:
                kwargs["password_hash"] = hash_password(kwargs.pop("password"))
            member.update(kwargs)
            break
    save_company_data(company_id, data)

def delete_member(company_id: str, member_id: str):
    """Delete a member"""
    data = load_company_data(company_id)
    data["members"] = [m for m in data["members"] if m["id"] != member_id]
    save_company_data(company_id, data)

def toggle_member_status(company_id: str, member_id: str):
    """Toggle member active status"""
    data = load_company_data(company_id)
    for member in data["members"]:
        if member["id"] == member_id:
            member["is_active"] = not member.get("is_active", True)
            break
    save_company_data(company_id, data)

# ==================== EMPLOYEE OPERATIONS ====================
def add_employee(company_id: str, name: str, monthly_collection: float = 3000, 
                 email: str = None, password: str = None, permissions: Dict = None,
                 is_admin: bool = False) -> Dict:
    """Add a new employee with optional login credentials"""
    data = load_company_data(company_id)
    
    # Check if email already exists in this company
    if email:
        if any(e.get("email", "").lower() == email.lower() for e in data["employees"]):
            raise ValueError("Email already exists in this company")
    
    employee = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "password_hash": hash_password(password) if password else None,
        "monthly_collection": monthly_collection,
        "permissions": permissions if permissions else (ADMIN_PERMISSIONS.copy() if is_admin else DEFAULT_PERMISSIONS.copy()),
        "is_admin": is_admin,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
    data["employees"].append(employee)
    save_company_data(company_id, data)
    return employee

def get_employees(company_id: str) -> List[Dict]:
    """Get all employees"""
    data = load_company_data(company_id)
    return data.get("employees", [])

def get_employee_by_id(company_id: str, employee_id: str) -> Optional[Dict]:
    """Get employee by ID"""
    data = load_company_data(company_id)
    return next((e for e in data["employees"] if e["id"] == employee_id), None)

def update_employee(company_id: str, employee_id: str, **kwargs):
    """Update employee details"""
    data = load_company_data(company_id)
    for emp in data["employees"]:
        if emp["id"] == employee_id:
            # Handle password hashing
            if "password" in kwargs:
                kwargs["password_hash"] = hash_password(kwargs.pop("password"))
            emp.update(kwargs)
            break
    save_company_data(company_id, data)

def update_employee_permissions(company_id: str, employee_id: str, permissions: Dict):
    """Update employee permissions"""
    data = load_company_data(company_id)
    for emp in data["employees"]:
        if emp["id"] == employee_id:
            emp["permissions"] = permissions
            break
    save_company_data(company_id, data)

def verify_employee_login(email: str, password: str) -> Optional[tuple]:
    """Verify employee login across all companies. Returns (company, employee) or None"""
    companies = get_all_companies()
    for company in companies:
        if not company.get("is_active", True):
            continue
        data = load_company_data(company["id"])
        for emp in data.get("employees", []):
            if emp.get("email", "").lower() == email.lower():
                if emp.get("password_hash") and verify_password(password, emp["password_hash"]):
                    if emp.get("is_active", True):
                        return (company, emp)
                    else:
                        raise ValueError("Account is deactivated")
    return None

def toggle_employee_status(company_id: str, employee_id: str):
    """Toggle employee active status"""
    data = load_company_data(company_id)
    for emp in data["employees"]:
        if emp["id"] == employee_id:
            emp["is_active"] = not emp.get("is_active", True)
            break
    save_company_data(company_id, data)

def delete_employee(company_id: str, employee_id: str):
    """Delete an employee"""
    data = load_company_data(company_id)
    data["employees"] = [e for e in data["employees"] if e["id"] != employee_id]
    data["daily_records"] = [r for r in data["daily_records"] if r["employee_id"] != employee_id]
    data["monthly_collections"] = [c for c in data["monthly_collections"] if c["employee_id"] != employee_id]
    save_company_data(company_id, data)

# ==================== DAILY RECORD OPERATIONS ====================
def add_daily_record(company_id: str, employee_id: str, record_date: date, 
                     roti: int = 0, naan: int = 0, rice: bool = False, 
                     salan: bool = False, tea: bool = False, other: bool = False) -> Dict:
    """Add or update a daily meal record"""
    data = load_company_data(company_id)
    date_str = record_date.strftime("%Y-%m-%d")
    
    # Find existing record
    existing_idx = None
    for idx, record in enumerate(data["daily_records"]):
        if record["employee_id"] == employee_id and record["date"] == date_str:
            existing_idx = idx
            break
    
    record = {
        "id": str(uuid.uuid4()),
        "employee_id": employee_id,
        "date": date_str,
        "roti": roti,
        "naan": naan,
        "rice": rice,
        "salan": salan,
        "tea": tea,
        "other": other,
        "created_at": datetime.now().isoformat()
    }
    
    if existing_idx is not None:
        record["id"] = data["daily_records"][existing_idx]["id"]
        data["daily_records"][existing_idx] = record
    else:
        data["daily_records"].append(record)
    
    save_company_data(company_id, data)
    return record

def get_daily_records(company_id: str, employee_id: str = None, month: int = None, year: int = None) -> List[Dict]:
    """Get daily records with optional filters"""
    data = load_company_data(company_id)
    records = data.get("daily_records", [])
    
    if employee_id:
        records = [r for r in records if r["employee_id"] == employee_id]
    
    if month and year:
        records = [r for r in records if r["date"].startswith(f"{year}-{month:02d}")]
    
    return records

def get_record_for_date(company_id: str, employee_id: str, record_date: date) -> Optional[Dict]:
    """Get record for specific employee and date"""
    data = load_company_data(company_id)
    date_str = record_date.strftime("%Y-%m-%d")
    for record in data["daily_records"]:
        if record["employee_id"] == employee_id and record["date"] == date_str:
            return record
    return None

# ==================== DAILY SHARED ITEMS ====================
def set_daily_shared_item(company_id: str, record_date: date, item_type: str, 
                          total_price: float, description: str = "") -> Dict:
    """Set the daily total price for a shared item"""
    data = load_company_data(company_id)
    date_str = record_date.strftime("%Y-%m-%d")
    
    existing_idx = None
    for idx, item in enumerate(data["daily_shared_items"]):
        if item["date"] == date_str and item["item_type"] == item_type:
            existing_idx = idx
            break
    
    shared_item = {
        "id": str(uuid.uuid4()),
        "date": date_str,
        "item_type": item_type,
        "total_price": total_price,
        "description": description,
        "created_at": datetime.now().isoformat()
    }
    
    if existing_idx is not None:
        shared_item["id"] = data["daily_shared_items"][existing_idx]["id"]
        data["daily_shared_items"][existing_idx] = shared_item
    else:
        data["daily_shared_items"].append(shared_item)
    
    save_company_data(company_id, data)
    return shared_item

def get_daily_shared_item(company_id: str, record_date: date, item_type: str) -> Optional[Dict]:
    """Get the daily shared item price"""
    data = load_company_data(company_id)
    date_str = record_date.strftime("%Y-%m-%d")
    for item in data["daily_shared_items"]:
        if item["date"] == date_str and item["item_type"] == item_type:
            return item
    return None

def get_monthly_shared_items(company_id: str, month: int, year: int) -> List[Dict]:
    """Get all shared items for a month"""
    data = load_company_data(company_id)
    prefix = f"{year}-{month:02d}"
    return [item for item in data["daily_shared_items"] if item["date"].startswith(prefix)]

# ==================== MONTHLY COLLECTIONS ====================
def add_monthly_collection(company_id: str, employee_id: str, month: int, year: int, amount: float) -> Dict:
    """Add or update monthly collection"""
    data = load_company_data(company_id)
    
    existing_idx = None
    for idx, col in enumerate(data["monthly_collections"]):
        if col["employee_id"] == employee_id and col["month"] == month and col["year"] == year:
            existing_idx = idx
            break
    
    collection = {
        "id": str(uuid.uuid4()),
        "employee_id": employee_id,
        "month": month,
        "year": year,
        "amount": amount,
        "collected_at": datetime.now().isoformat()
    }
    
    if existing_idx is not None:
        collection["id"] = data["monthly_collections"][existing_idx]["id"]
        data["monthly_collections"][existing_idx] = collection
    else:
        data["monthly_collections"].append(collection)
    
    save_company_data(company_id, data)
    return collection

def get_monthly_collection(company_id: str, employee_id: str, month: int, year: int) -> Optional[Dict]:
    """Get monthly collection for an employee"""
    data = load_company_data(company_id)
    for col in data["monthly_collections"]:
        if col["employee_id"] == employee_id and col["month"] == month and col["year"] == year:
            return col
    return None

def get_all_monthly_collections(company_id: str, month: int, year: int) -> List[Dict]:
    """Get all collections for a specific month"""
    data = load_company_data(company_id)
    return [c for c in data["monthly_collections"] if c["month"] == month and c["year"] == year]

# ==================== MENU ITEMS ====================
def get_menu_items(company_id: str) -> List[Dict]:
    """Get all menu items with prices"""
    data = load_company_data(company_id)
    return data.get("menu_items", [])

def update_menu_price(company_id: str, item_id: str, new_price: float):
    """Update menu item price"""
    data = load_company_data(company_id)
    for item in data["menu_items"]:
        if item["id"] == item_id:
            item["price"] = new_price
            break
    save_company_data(company_id, data)

# ==================== CALCULATIONS ====================
def calculate_daily_cost(company_id: str, employee_id: str, record_date: date) -> float:
    """Calculate cost for a single day's consumption"""
    record = get_record_for_date(company_id, employee_id, record_date)
    if not record:
        return 0
    
    menu_items = get_menu_items(company_id)
    prices = {item["id"]: item["price"] for item in menu_items}
    
    cost = 0
    
    # Fixed price items (Roti, Naan, Tea)
    cost += record.get("roti", 0) * prices.get("roti", 20)
    cost += record.get("naan", 0) * prices.get("naan", 25)
    
    # Tea - check if it's fixed or shared
    tea_item = next((m for m in menu_items if m["id"] == "tea"), None)
    if record.get("tea", False):
        if tea_item and not tea_item.get("shared", False):
            # Fixed price tea (per cup count stored in tea field as int or True=1)
            tea_count = record.get("tea", 0)
            if isinstance(tea_count, bool):
                tea_count = 1 if tea_count else 0
            cost += tea_count * prices.get("tea", 15)
    
    # Shared items (Rice, Salan, Other)
    all_records = get_daily_records(company_id, month=record_date.month, year=record_date.year)
    date_records = [r for r in all_records if r["date"] == record_date.strftime("%Y-%m-%d")]
    
    for item_type in ["rice", "salan", "other"]:
        if record.get(item_type, False):
            shared_item = get_daily_shared_item(company_id, record_date, item_type)
            if shared_item and shared_item["total_price"] > 0:
                count = sum(1 for r in date_records if r.get(item_type, False))
                if count > 0:
                    cost += shared_item["total_price"] / count
    
    return cost

def calculate_monthly_consumption(company_id: str, employee_id: str, month: int, year: int) -> float:
    """Calculate total consumption for an employee in a month"""
    import calendar
    
    total = 0
    num_days = calendar.monthrange(year, month)[1]
    
    for day in range(1, num_days + 1):
        record_date = date(year, month, day)
        total += calculate_daily_cost(company_id, employee_id, record_date)
    
    return total

def get_monthly_balance(company_id: str, employee_id: str, month: int, year: int) -> float:
    """Get remaining balance for an employee in a month"""
    collection = get_monthly_collection(company_id, employee_id, month, year)
    if not collection:
        employees = get_employees(company_id)
        employee = next((e for e in employees if e["id"] == employee_id), None)
        collected = employee["monthly_collection"] if employee else 0
    else:
        collected = collection["amount"]
    
    consumed = calculate_monthly_consumption(company_id, employee_id, month, year)
    return collected - consumed

# ==================== PLATFORM STATISTICS (Super Admin) ====================
def get_platform_stats() -> Dict:
    """Get platform-wide statistics for super admin"""
    companies = get_all_companies()
    
    total_employees = 0
    total_records = 0
    
    for company in companies:
        data = load_company_data(company["id"])
        total_employees += len(data.get("employees", []))
        total_records += len(data.get("daily_records", []))
    
    return {
        "total_companies": len(companies),
        "active_companies": sum(1 for c in companies if c.get("is_active", True)),
        "total_employees": total_employees,
        "total_records": total_records
    }

# ==================== INVITE SYSTEM ====================
def create_invite_token(company_id: str, email: str, name: str, 
                        monthly_collection: float, permissions: Dict,
                        created_by: str, expires_hours: int = 48) -> Dict:
    """Create an email-gated invite token"""
    data = load_company_data(company_id)
    
    # Check if email already exists
    if any(e.get("email", "").lower() == email.lower() for e in data["employees"]):
        raise ValueError("Email already registered in this company")
    
    # Initialize invites list if not exists
    if "invites" not in data:
        data["invites"] = []
    
    # Check for existing pending invite for this email
    for invite in data["invites"]:
        if invite["email"].lower() == email.lower() and not invite.get("used", False):
            expires = datetime.fromisoformat(invite["expires_at"])
            if expires > datetime.now():
                raise ValueError("An active invite already exists for this email")
    
    token = secrets.token_urlsafe(32)
    invite = {
        "id": str(uuid.uuid4()),
        "token": token,
        "email": email,
        "name": name,
        "monthly_collection": monthly_collection,
        "permissions": permissions,
        "created_by": created_by,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
        "used": False
    }
    
    data["invites"].append(invite)
    save_company_data(company_id, data)
    return invite

def get_invite_by_token(token: str) -> Optional[tuple]:
    """Get invite details by token. Returns (company_id, invite) or None"""
    companies = get_all_companies()
    for company in companies:
        data = load_company_data(company["id"])
        for invite in data.get("invites", []):
            if invite["token"] == token:
                if invite.get("used", False):
                    return None  # Already used
                expires = datetime.fromisoformat(invite["expires_at"])
                if expires < datetime.now():
                    return None  # Expired
                return (company["id"], invite)
    return None

def complete_invite_registration(token: str, password: str) -> Optional[Dict]:
    """Complete registration using invite token. Returns new employee or None"""
    result = get_invite_by_token(token)
    if not result:
        return None
    
    company_id, invite = result
    
    # Create the employee
    try:
        employee = add_employee(
            company_id=company_id,
            name=invite["name"],
            email=invite["email"],
            password=password,
            monthly_collection=invite["monthly_collection"],
            permissions=invite["permissions"]
        )
    except ValueError:
        return None
    
    # Mark invite as used
    data = load_company_data(company_id)
    for inv in data["invites"]:
        if inv["token"] == token:
            inv["used"] = True
            inv["used_at"] = datetime.now().isoformat()
            break
    save_company_data(company_id, data)
    
    return employee

def get_pending_invites(company_id: str) -> List[Dict]:
    """Get all pending (unused, not expired) invites for a company"""
    data = load_company_data(company_id)
    now = datetime.now()
    pending = []
    for invite in data.get("invites", []):
        if not invite.get("used", False):
            expires = datetime.fromisoformat(invite["expires_at"])
            if expires > now:
                pending.append(invite)
    return pending

def delete_invite(company_id: str, invite_id: str):
    """Delete an invite"""
    data = load_company_data(company_id)
    data["invites"] = [i for i in data.get("invites", []) if i["id"] != invite_id]
    save_company_data(company_id, data)

