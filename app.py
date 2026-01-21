"""
Lunch Expense Management Platform
Developed by Software Bazaar IT Solutions

Multi-tenant SaaS application for managing employee lunch collections
- Super Admin Dashboard (Hidden - Secret URL)
- Company Registration with OTP Verification
- Role-based Access (Admin/Member)
- +1/-1 buttons for Roti/Naan/Tea
- Tea as fixed price item
- Clean numbers (no decimals)
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import plotly.express as px
import plotly.graph_objects as go
import base64
import os

from db_ops import (
    # Super Admin
    verify_super_admin, get_super_admin, update_super_admin_password,
    get_all_companies, get_platform_stats, toggle_company_status, delete_company,
    # Company
    register_company, verify_company_login, get_company_by_id, update_company,
    get_company_by_email, reset_company_password, verify_password,
    # Employees
    add_employee, get_employees, get_employee_by_id, update_employee, delete_employee,
    verify_employee_login, update_employee_permissions, toggle_employee_status,
    # Invites
    create_invite_token, get_invite_by_token, complete_invite_registration,
    get_pending_invites, delete_invite,
    # Permissions
    DEFAULT_PERMISSIONS, ADMIN_PERMISSIONS,
    # Daily Records
    add_daily_record, get_daily_records, get_record_for_date,
    # Shared Items
    set_daily_shared_item, get_daily_shared_item, get_monthly_shared_items,
    # Collections
    add_monthly_collection, get_monthly_collection, get_all_monthly_collections,
    # Menu
    get_menu_items, update_menu_price,
    # Calculations
    calculate_daily_cost, calculate_monthly_consumption, get_monthly_balance,
    load_company_data
)
from config import DEFAULT_MONTHLY_COLLECTION

# Try to import email service
try:
    from email_service import (
        send_registration_otp, verify_otp, send_welcome_email_notification,
        send_password_reset_otp, send_employee_invite, send_employee_welcome, EMAIL_CONFIG
    )
    EMAIL_ENABLED = bool(EMAIL_CONFIG.get("app_password"))
except ImportError:
    EMAIL_ENABLED = False

# Page configuration
st.set_page_config(
    page_title="Lunch Expense Management Platform - Software Bazaar",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "company_id" not in st.session_state:
    st.session_state.company_id = None
if "company_name" not in st.session_state:
    st.session_state.company_name = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "employee_id" not in st.session_state:
    st.session_state.employee_id = None
if "permissions" not in st.session_state:
    st.session_state.permissions = {}
if "show_my_records_only" not in st.session_state:
    st.session_state.show_my_records_only = True
if "registration_step" not in st.session_state:
    st.session_state.registration_step = 1
if "reg_data" not in st.session_state:
    st.session_state.reg_data = {}
if "reset_step" not in st.session_state:
    st.session_state.reset_step = 1

# Check for super admin access via URL parameter
query_params = st.query_params
show_super_admin = query_params.get("admin", "") == "softwarbazaar2026"
invite_token = query_params.get("invite", "")

# Function to load logo
def get_logo_base64():
    logo_path = os.path.join(os.path.dirname(__file__), "logo.jpg")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_base64 = get_logo_base64()

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(46, 204, 113, 0.3);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        margin: 5px 0;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        background: linear-gradient(135deg, #2ecc71, #1e3a5f);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 5px;
    }
    .main-header {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1e3a5f, #2ecc71, #f39c12);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 10px 0;
        margin-bottom: 20px;
    }
    .logo-container {
        text-align: center;
        padding: 10px;
        margin-bottom: 10px;
    }
    .logo-container img {
        max-width: 120px;
        border-radius: 10px;
    }
    .shared-item-box {
        background: linear-gradient(135deg, rgba(243, 156, 18, 0.1), rgba(46, 204, 113, 0.1));
        border: 1px solid rgba(243, 156, 18, 0.3);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .badge-success {
        background: linear-gradient(135deg, #059669, #10b981);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
    }
    .badge-danger {
        background: linear-gradient(135deg, #dc2626, #ef4444);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
    }
    .badge-admin {
        background: linear-gradient(135deg, #7c3aed, #a855f7);
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.75rem;
    }
    .counter-btn {
        display: inline-block;
        width: 30px;
        height: 30px;
        line-height: 30px;
        text-align: center;
        background: linear-gradient(135deg, #1e3a5f, #2ecc71);
        color: white;
        border-radius: 50%;
        cursor: pointer;
        font-weight: bold;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def metric_card(label, value, icon=""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{icon} {value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def format_pkr(amount):
    """Format amount as PKR without decimals"""
    return f"PKR {int(amount):,}"

def logout():
    for key in list(st.session_state.keys()):
        if key not in ['logged_in']:
            del st.session_state[key]
    st.session_state.logged_in = False
    st.session_state.user_type = None
    st.session_state.company_id = None
    st.session_state.company_name = None
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.employee_id = None
    st.session_state.permissions = {}
    st.session_state.show_my_records_only = True
    st.rerun()

def has_permission(permission_name: str) -> bool:
    """Check if current user has a specific permission"""
    # Super admin and company admin have all permissions
    if st.session_state.user_type in ["super_admin", "company_admin"]:
        return True
    # Check employee permissions
    permissions = st.session_state.get("permissions", {})
    return permissions.get(permission_name, False)


# ==================== LOGIN PAGE ====================
def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if logo_base64:
            st.markdown(f"""
            <div class="logo-container">
                <img src="data:image/jpeg;base64,{logo_base64}" alt="Software Bazaar Logo">
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<h1 class="main-header">🍽️ Lunch Expense Management Platform</h1>', unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>by Software Bazaar IT Solutions<br><small>Founded by Mirza M Mobeen</small></p>", unsafe_allow_html=True)
        
        # Handle Invite Link
        if invite_token:
            st.info("👋 You've been invited! Set up your password to join.")
            result = get_invite_by_token(invite_token)
            
            if result:
                company_id, invite = result
                st.markdown(f"### Join {invite['name']}")
                st.caption(f"Email: {invite['email']}")
                
                with st.form("invite_setup"):
                    p1 = st.text_input("Create Password", type="password")
                    p2 = st.text_input("Confirm Password", type="password")
                    
                    if st.form_submit_button("Complete Registration", use_container_width=True):
                        if p1 != p2:
                            st.error("Passwords don't match")
                        elif len(p1) < 6:
                            st.error("Password must be at least 6 characters")
                        else:
                            emp = complete_invite_registration(invite_token, p1)
                            if emp:
                                st.success("Registration successful! You can now login.")
                                
                                # Send welcome email
                                if EMAIL_ENABLED:
                                    company = get_company_by_id(company_id)
                                    send_employee_welcome(invite["email"], company["name"], invite["name"])
                                
                                st.query_params.clear()
                                # st.rerun() # Wait for user to read success
                            else:
                                st.error("Registration failed. Token might be expired.")
            else:
                st.error("Invalid or expired invite link")
                if st.button("Go to Login"):
                    st.query_params.clear()
                    st.rerun()
            return
        
        # Determine tabs based on Super Admin visibility
        tabs = ["🔑 Login", "📝 Register Company", "🔐 Reset Password"]
        if show_super_admin:
            tabs.append("⚡ Super Admin")
            
        current_tabs = st.tabs(tabs)
        
        # ===== UNIFIED LOGIN TAB =====
        with current_tabs[0]:
            st.subheader("Welcome Back")
            with st.form("unified_login"):
                email = st.text_input("Email", placeholder="you@company.com")
                password = st.text_input("Password", type="password")
                remember = st.checkbox("Remember me")
                
                if st.form_submit_button("Login", use_container_width=True):
                    # DEBUG: Show what data is available
                    import db_ops
                    all_companies = db_ops.get_all_companies()
                    st.info(f"DEBUG: Found {len(all_companies)} companies in database")
                    if all_companies:
                        st.info(f"DEBUG: Company emails: {[c.get('admin_email', 'no-email') for c in all_companies]}")
                    
                    # 1. Try Company Admin Login
                    try:
                        company = verify_company_login(email, password)
                        if company:
                            st.session_state.logged_in = True
                            st.session_state.user_type = "company_admin"
                            st.session_state.company_id = company["id"]
                            st.session_state.company_name = company["name"]
                            st.session_state.user_role = "admin"
                            st.session_state.user_name = company["admin_name"]
                            st.session_state.permissions = ADMIN_PERMISSIONS
                            st.session_state.show_my_records_only = False
                            st.success("Logged in as Company Admin!")
                            st.rerun()
                            return # Stop execution
                    except ValueError as e:
                        st.error(str(e))
                        return # Stop if deactivated
                    except Exception as e:
                        st.error(f"DEBUG: Company login error: {e}")

                    # 2. Try Employee Login if Company failed
                    try:
                        result = verify_employee_login(email, password)
                        if result:
                            company, emp = result
                            st.session_state.logged_in = True
                            st.session_state.user_type = "employee"
                            st.session_state.company_id = company["id"]
                            st.session_state.company_name = company["name"]
                            st.session_state.user_role = "employee"
                            st.session_state.user_name = emp["name"]
                            st.session_state.employee_id = emp["id"]
                            st.session_state.permissions = emp.get("permissions", {})
                            st.session_state.show_my_records_only = True
                            
                            if emp.get("is_admin", False):
                                st.session_state.user_role = "admin"
                                st.session_state.user_type = "company_admin" # Treat aligned admins same as company login
                            
                            st.success(f"Welcome back, {emp['name']}!")
                            st.rerun()
                            return
                    except ValueError as e:
                        st.error(str(e))
                        return
                    except Exception as e:
                        st.error(f"DEBUG: Employee login error: {e}")

                    # 3. Both failed
                    st.error("Invalid email or password")
        
        # ===== REGISTER TAB =====
        with current_tabs[1]:
            st.subheader("Register Your Company")
            
            if st.session_state.registration_step == 1:
                # Step 1: Enter details
                with st.form("register_step1"):
                    company_name = st.text_input("Company Name", placeholder="ABC Company")
                    admin_name = st.text_input("Admin Name", placeholder="John Doe")
                    admin_email = st.text_input("Admin Email", placeholder="admin@abc.com")
                    reg_password = st.text_input("Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
                    
                    if st.form_submit_button("Send OTP", use_container_width=True):
                        if not all([company_name, admin_name, admin_email, reg_password]):
                            st.error("All fields are required")
                        elif reg_password != confirm_password:
                            st.error("Passwords don't match")
                        elif len(reg_password) < 6:
                            st.error("Password must be at least 6 characters")
                        elif get_company_by_email(admin_email):
                            st.error("Email already registered")
                        else:
                            # Store data and send OTP
                            st.session_state.reg_data = {
                                "company_name": company_name,
                                "admin_name": admin_name,
                                "admin_email": admin_email,
                                "password": reg_password
                            }
                            
                            if EMAIL_ENABLED:
                                success, otp = send_registration_otp(admin_email, company_name)
                                if success:
                                    st.session_state.registration_step = 2
                                    st.success(f"OTP sent to {admin_email}!")
                                    st.rerun()
                                else:
                                    st.warning("Could not send OTP. Registering directly...")
                                    try:
                                        company = register_company(company_name, admin_name, admin_email, reg_password)
                                        st.success(f"Company '{company_name}' registered! You can now login.")
                                        st.session_state.registration_step = 1
                                        st.session_state.reg_data = {}
                                    except ValueError as e:
                                        st.error(str(e))
                            else:
                                # Email not configured, register directly
                                try:
                                    company = register_company(company_name, admin_name, admin_email, reg_password)
                                    st.success(f"Company '{company_name}' registered! You can now login.")
                                except ValueError as e:
                                    st.error(str(e))
            
            elif st.session_state.registration_step == 2:
                # Step 2: Verify OTP
                st.info(f"OTP sent to: {st.session_state.reg_data.get('admin_email', '')}")
                
                with st.form("verify_otp"):
                    otp_input = st.text_input("Enter 6-digit OTP", max_chars=6)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Verify & Register", use_container_width=True):
                            if verify_otp(st.session_state.reg_data["admin_email"], otp_input, "registration"):
                                try:
                                    data = st.session_state.reg_data
                                    company = register_company(
                                        data["company_name"],
                                        data["admin_name"],
                                        data["admin_email"],
                                        data["password"]
                                    )
                                    # Send welcome email
                                    if EMAIL_ENABLED:
                                        send_welcome_email_notification(
                                            data["admin_email"],
                                            data["company_name"],
                                            data["admin_name"]
                                        )
                                    st.success(f"Company '{data['company_name']}' registered! You can now login.")
                                    st.session_state.registration_step = 1
                                    st.session_state.reg_data = {}
                                    st.rerun()
                                except ValueError as e:
                                    st.error(str(e))
                            else:
                                st.error("Invalid or expired OTP")
                
                if st.button("← Back"):
                    st.session_state.registration_step = 1
                    st.rerun()
        
        # ===== PASSWORD RESET TAB =====
        with current_tabs[2]:
            st.subheader("Reset Password")
            
            if st.session_state.reset_step == 1:
                with st.form("reset_step1"):
                    reset_email = st.text_input("Email", placeholder="admin@company.com")
                    
                    if st.form_submit_button("Send Reset OTP", use_container_width=True):
                        company = get_company_by_email(reset_email)
                        if company:
                            if EMAIL_ENABLED:
                                success, otp = send_password_reset_otp(reset_email, company["admin_name"])
                                if success:
                                    st.session_state.reset_email = reset_email
                                    st.session_state.reset_step = 2
                                    st.success(f"OTP sent to {reset_email}")
                                    st.rerun()
                                else:
                                    st.error("Could not send OTP. Please try again.")
                            else:
                                st.error("Email service not configured. Contact admin.")
                        else:
                            st.error("Email not found")
            
            elif st.session_state.reset_step == 2:
                st.info(f"OTP sent to: {st.session_state.get('reset_email', '')}")
                
                with st.form("reset_step2"):
                    reset_otp = st.text_input("Enter OTP", max_chars=6)
                    new_pass = st.text_input("New Password", type="password")
                    confirm_pass = st.text_input("Confirm Password", type="password")
                    
                    if st.form_submit_button("Reset Password", use_container_width=True):
                        if new_pass != confirm_pass:
                            st.error("Passwords don't match")
                        elif len(new_pass) < 6:
                            st.error("Password must be at least 6 characters")
                        elif verify_otp(st.session_state.reset_email, reset_otp, "password_reset"):
                            if reset_company_password(st.session_state.reset_email, new_pass):
                                st.success("Password reset successfully! You can now login.")
                                st.session_state.reset_step = 1
                                st.rerun()
                        else:
                            st.error("Invalid or expired OTP")
                
                if st.button("← Back", key="reset_back"):
                    st.session_state.reset_step = 1
                    st.rerun()
        
        # ===== SUPER ADMIN TAB (Hidden by default) =====
        if show_super_admin:
            with current_tabs[3]:
                st.subheader("🔐 Super Admin Login")
                st.caption("Platform administrators only")
                with st.form("super_admin_login"):
                    sa_email = st.text_input("Email", placeholder="admin@softwarebazaar.com")
                    sa_password = st.text_input("Password", type="password", key="sa_pass")
                    
                    if st.form_submit_button("Login as Super Admin", use_container_width=True):
                        if verify_super_admin(sa_email, sa_password):
                            st.session_state.logged_in = True
                            st.session_state.user_type = "super_admin"
                            st.session_state.user_name = "Super Admin"
                            st.success("Super Admin login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")


# ==================== SUPER ADMIN DASHBOARD ====================
def show_super_admin_dashboard():
    if logo_base64:
        st.sidebar.markdown(f'<div class="logo-container"><img src="data:image/jpeg;base64,{logo_base64}" alt="Logo"></div>', unsafe_allow_html=True)
    
    st.sidebar.markdown("## 🔐 Super Admin")
    st.sidebar.markdown(f"Welcome, **{st.session_state.user_name}**")
    
    page = st.sidebar.radio("Menu", ["📊 Dashboard", "🏢 Companies", "⚙️ Settings"])
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown('<div style="text-align: center; color: #64748b; font-size: 0.8rem;"><strong>Software Bazaar IT Solutions</strong><br>Founded by Mirza M Mobeen</div>', unsafe_allow_html=True)
    
    if page == "📊 Dashboard":
        st.markdown('<h1 class="main-header">🔐 Super Admin Dashboard</h1>', unsafe_allow_html=True)
        
        stats = get_platform_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            metric_card("Total Companies", stats["total_companies"], "🏢")
        with col2:
            metric_card("Active Companies", stats["active_companies"], "✅")
        with col3:
            metric_card("Total Employees", stats["total_employees"], "👥")
        with col4:
            metric_card("Total Records", stats["total_records"], "📝")
        
        st.markdown("---")
        st.subheader("📈 Recent Companies")
        
        companies = get_all_companies()
        if companies:
            companies_sorted = sorted(companies, key=lambda x: x.get("created_at", ""), reverse=True)[:10]
            
            for company in companies_sorted:
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    status = "🟢" if company.get("is_active", True) else "🔴"
                    st.markdown(f"### {status} {company['name']}")
                    st.caption(f"{company['admin_name']} | {company['admin_email']}")
                with col2:
                    st.caption(f"Registered: {company.get('created_at', '')[:10]}")
                with col3:
                    if company.get("is_active", True):
                        if st.button("Deactivate", key=f"d_{company['id']}"):
                            toggle_company_status(company["id"])
                            st.rerun()
                    else:
                        if st.button("Activate", key=f"a_{company['id']}"):
                            toggle_company_status(company["id"])
                            st.rerun()
                st.markdown("---")
    
    elif page == "🏢 Companies":
        st.markdown('<h1 class="main-header">🏢 All Companies</h1>', unsafe_allow_html=True)
        
        companies = get_all_companies()
        search = st.text_input("🔍 Search Company")
        
        if search:
            companies = [c for c in companies if search.lower() in c["name"].lower() or search.lower() in c["admin_email"].lower()]
        
        for company in companies:
            with st.expander(f"{company['name']} ({company['admin_email']})"):
                st.write(f"**Admin Name:** {company['admin_name']}")
                st.write(f"**Status:** {'Active' if company.get('is_active', True) else 'Inactive'}")
                st.write(f"**Registered:** {company.get('created_at', 'Unknown')}")
                
                c1, c2 = st.columns(2)
                with c1:
                    if company.get("is_active", True):
                        if st.button("Deactivate", key=f"deact_{company['id']}"):
                            toggle_company_status(company["id"])
                            st.rerun()
                    else:
                        if st.button("Activate", key=f"act_{company['id']}"):
                            toggle_company_status(company["id"])
                            st.rerun()
                with c2:
                    # Delete Company Button
                    if st.button("🗑️ Delete Company", key=f"del_{company['id']}"):
                        delete_company(company["id"])
                        st.success(f"Deleted {company['name']}")
                        st.rerun()
    
    elif page == "⚙️ Settings":
        st.subheader("Admin Settings")
        with st.form("sa_pass_update"):
            new_pass = st.text_input("New Super Admin Password", type="password")
            if st.form_submit_button("Update Password"):
                if len(new_pass) >= 6:
                    update_super_admin_password(new_pass)
                    st.success("Password updated!")
                else:
                    st.error("Password too short")


# ==================== COMPANY DASHBOARD ====================
def show_company_dashboard():
    company_id = st.session_state.company_id
    current_employee_id = st.session_state.employee_id
    
    if logo_base64:
        st.sidebar.markdown(f'<div class="logo-container"><img src="data:image/jpeg;base64,{logo_base64}" alt="Logo"></div>', unsafe_allow_html=True)
    
    st.sidebar.markdown(f"## {st.session_state.company_name}")
    st.sidebar.markdown(f"👤 **{st.session_state.user_name}**")
    
    if st.session_state.user_role == "admin":
        st.sidebar.caption("Admin Access")
    else:
        st.sidebar.caption("Employee Access")
        
    st.sidebar.markdown("---")
    
    # Permission-based Menu - TEMPORARILY FORCED FOR DEBUGGING
    # The issue is menu items not appearing on deployment
    menu = ["🏠 Dashboard"]
    
    # FORCE: Always add Employees menu for now (was: has_permission check)
    menu.append("👥 Employees")
    
    menu.append("📝 Daily Entry")
    
    # FORCE: Always add Monthly Report for now (was: has_permission check)
    menu.append("📊 Monthly Report")
    
    # FORCE: Always add Settings for now (was: has_permission check)
    menu.append("⚙️ Settings")
    
    # DEBUG: Show what menu items were added
    st.sidebar.caption(f"Menu items: {len(menu)}")
        
    page = st.sidebar.radio("Menu", menu, label_visibility="collapsed")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown('<div style="text-align: center; color: #64748b; font-size: 0.8rem;"><strong>Software Bazaar IT Solutions</strong><br>Founded by Mirza M Mobeen</div>', unsafe_allow_html=True)
    
    # DEBUG PANEL - Shows session state for debugging deployment issues
    with st.sidebar.expander("🔧 Debug Info"):
        st.write(f"**User Type:** {st.session_state.get('user_type', 'NOT SET')}")
        st.write(f"**User Role:** {st.session_state.get('user_role', 'NOT SET')}")
        st.write(f"**Company ID:** {st.session_state.get('company_id', 'NOT SET')}")
        st.write(f"**Employee ID:** {st.session_state.get('employee_id', 'NOT SET')}")
        st.write(f"**Permissions:** {st.session_state.get('permissions', {})}")
        st.write(f"**has_permission checks:**")
        st.write(f"- can_view_all: {has_permission('can_view_all')}")
        st.write(f"- can_add_employees: {has_permission('can_add_employees')}")
        st.write(f"- can_view_reports: {has_permission('can_view_reports')}")
        st.write(f"- can_manage_settings: {has_permission('can_manage_settings')}")
            
    # Function to get latest prices
    menu_items = get_menu_items(company_id)
    prices = {m["id"]: m["price"] for m in menu_items}
    
    # ===== DASHBOARD =====
    if page == "🏠 Dashboard":
        # Filter Toggle for non-admins
        if current_employee_id and has_permission("can_view_all"):
            st.session_state.show_my_records_only = st.toggle("Show My Records Only", value=st.session_state.show_my_records_only)
        
        # Filter logic
        employees = get_employees(company_id)
        if current_employee_id and st.session_state.show_my_records_only:
            my_emp = next((e for e in employees if e["id"] == current_employee_id), None)
            display_employees = [my_emp] if my_emp else []
        else:
            display_employees = employees
            
        st.markdown('<h1 class="main-header">🏠 Dashboard</h1>', unsafe_allow_html=True)
        
        today = date.today()
        st.markdown(f"### {today.strftime('%B %d, %Y')}")
        
        # Metrics
        today_consumption = 0
        month_consumption = 0
        month_collection = 0
        
        for emp in display_employees:
            today_consumption += calculate_daily_cost(company_id, emp["id"], today)
            month_consumption += calculate_monthly_consumption(company_id, emp["id"], today.month, today.year)
            
            col = get_monthly_collection(company_id, emp["id"], today.month, today.year)
            month_collection += col["amount"] if col else emp["monthly_collection"]
            
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("Today's Expense", format_pkr(today_consumption), "🍛")
        with c2:
            metric_card("Month Expense", format_pkr(month_consumption), "📅")
        with c3:
            metric_card("Month Collections", format_pkr(month_collection), "💰")
            
        st.markdown("---")
        
        # Quick Entry (Simplified)
        if has_permission("can_add_entries"):
            st.subheader("⚡ Quick Entry")
            if display_employees:
                # Default to current user if only one, else list
                target_emp = display_employees[0]
                if len(display_employees) > 1:
                    target_emp_name = st.selectbox("Select Employee", [e["name"] for e in display_employees])
                    target_emp = next(e for e in display_employees if e["name"] == target_emp_name)
                    
                emp_id = target_emp["id"]
                record = get_record_for_date(company_id, emp_id, today)
                
                # Counters
                c1, c2, c3 = st.columns(3)
                
                # Roti
                with c1:
                    st.markdown("**Roti**")
                    r_val = record["roti"] if record else 0
                    c_a, c_b, c_c = st.columns([1,1,1])
                    if c_a.button("➖", key="r_minus"):
                        r_val = max(0, r_val - 1)
                    c_b.markdown(f"<h3 style='text-align: center'>{r_val}</h3>", unsafe_allow_html=True)
                    if c_c.button("➕", key="r_plus"):
                        r_val += 1
                
                # Naan
                with c2:
                    st.markdown("**Naan**")
                    n_val = record["naan"] if record else 0
                    c_a, c_b, c_c = st.columns([1,1,1])
                    if c_a.button("➖", key="n_minus"):
                        n_val = max(0, n_val - 1)
                    c_b.markdown(f"<h3 style='text-align: center'>{n_val}</h3>", unsafe_allow_html=True)
                    if c_c.button("➕", key="n_plus"):
                        n_val += 1

                # Tea
                with c3:
                    st.markdown("**Tea**")
                    t_val = record["tea"] if record else 0
                    # Handle boolean tea legacy
                    if isinstance(t_val, bool): t_val = 1 if t_val else 0
                    
                    c_a, c_b, c_c = st.columns([1,1,1])
                    if c_a.button("➖", key="t_minus"):
                        t_val = max(0, t_val - 1)
                    c_b.markdown(f"<h3 style='text-align: center'>{t_val}</h3>", unsafe_allow_html=True)
                    if c_c.button("➕", key="t_plus"):
                        t_val += 1

                if st.button("Save Quick Entry", use_container_width=True):
                    add_daily_record(company_id, emp_id, today, roti=r_val, naan=n_val, tea=t_val, 
                                     rice=record["rice"] if record else False,
                                     salan=record["salan"] if record else False,
                                     other=record["other"] if record else False)
                    st.success(f"Saved for {target_emp['name']}!")
                    st.rerun()
            else:
                st.info("No employees found.")

    # ===== EMPLOYEES =====
    elif page == "👥 Employees":
        st.markdown('<h1 class="main-header">👥 Employees</h1>', unsafe_allow_html=True)
        
        # Tabs for adding/managing
        if has_permission("can_add_employees"):
            t1, t2 = st.tabs(["📋 List", "➕ Add / Invite"])
        else:
            t1, t2 = st.tabs(["📋 List"]) if has_permission("can_view_all") else (None, None)
            
        with t1 if t1 else st.container():
            employees = get_employees(company_id)
            search = st.text_input("🔍 Search")
            filtered = [e for e in employees if search.lower() in e["name"].lower()] if search else employees
            
            for emp in filtered:
                with st.expander(f"👤 {emp['name']} {'(Admin)' if emp.get('is_admin') else ''}"):
                    c1, c2 = st.columns(2)
                    c1.write(f"Email: {emp.get('email', 'N/A')}")
                    c2.write(f"Collection: {emp['monthly_collection']}")
                    
                    bal = get_monthly_balance(company_id, emp["id"], date.today().month, date.today().year)
                    st.write(f"**Current Balance:** {format_pkr(bal)}")
                    
                    # Permissions Editor
                    if has_permission("can_edit_employees") and not emp.get("is_admin"):
                        st.markdown("**Permissions**")
                        perms = emp.get("permissions", DEFAULT_PERMISSIONS)
                        new_perms = perms.copy()
                        
                        pc1, pc2, pc3 = st.columns(3)
                        with pc1:
                            new_perms["can_add_entries"] = st.checkbox("Add Entries", perms.get("can_add_entries", True), key=f"p1_{emp['id']}")
                            new_perms["can_edit_entries"] = st.checkbox("Edit Entries", perms.get("can_edit_entries", False), key=f"p1b_{emp['id']}")
                            new_perms["can_view_all"] = st.checkbox("View All", perms.get("can_view_all", False), key=f"p2_{emp['id']}")
                        with pc2:
                            new_perms["can_view_reports"] = st.checkbox("View Reports", perms.get("can_view_reports", False), key=f"p3_{emp['id']}")
                            new_perms["can_manage_settings"] = st.checkbox("Settings", perms.get("can_manage_settings", False), key=f"p4_{emp['id']}")
                            new_perms["can_invite"] = st.checkbox("Invite Users", perms.get("can_invite", False), key=f"p5_{emp['id']}")
                        with pc3:
                            new_perms["can_add_employees"] = st.checkbox("Add Employees", perms.get("can_add_employees", False), key=f"p6_{emp['id']}")
                            new_perms["can_edit_employees"] = st.checkbox("Edit Employees", perms.get("can_edit_employees", False), key=f"p7_{emp['id']}")
                            new_perms["can_delete_employees"] = st.checkbox("Delete Employees", perms.get("can_delete_employees", False), key=f"p8_{emp['id']}")
                        
                        if new_perms != perms:
                            if st.button("Update Permissions", key=f"upd_{emp['id']}"):
                                update_employee_permissions(company_id, emp["id"], new_perms)
                                st.success("Permissions updated!")
                                st.rerun()
                                
                    if has_permission("can_delete_employees") and not emp.get("is_admin"):
                        if st.button("🗑️ Remove Employee", key=f"del_{emp['id']}"):
                            delete_employee(company_id, emp["id"])
                            st.rerun()

        if has_permission("can_add_employees") and t2:
            with t2:
                st.subheader("Invite New Employee")
                with st.form("invite_emp"):
                    i_name = st.text_input("Name")
                    i_email = st.text_input("Email")
                    i_col = st.number_input("Monthly Collection", value=DEFAULT_MONTHLY_COLLECTION, step=500)
                    
                    st.markdown("**Initial Permissions**")
                    ic1, ic2, ic3 = st.columns(3)
                    with ic1:
                        ip_add_entries = st.checkbox("Can Add Entries", value=True)
                        ip_edit_entries = st.checkbox("Can Edit Entries")
                        ip_view_all = st.checkbox("Can View All Records")
                    with ic2:
                        ip_reports = st.checkbox("Can View Reports")
                        ip_settings = st.checkbox("Can Manage Settings")
                        ip_invite = st.checkbox("Can Invite Users")
                    with ic3:
                        ip_add_emps = st.checkbox("Can Add Employees")
                        ip_edit_emps = st.checkbox("Can Edit Employees")
                        ip_del_emps = st.checkbox("Can Delete Employees")
                    
                    if st.form_submit_button("Send Invite"):
                        if i_name and i_email:
                            try:
                                perms = DEFAULT_PERMISSIONS.copy()
                                perms["can_add_entries"] = ip_add_entries
                                perms["can_edit_entries"] = ip_edit_entries
                                perms["can_view_all"] = ip_view_all
                                perms["can_view_reports"] = ip_reports
                                perms["can_manage_settings"] = ip_settings
                                perms["can_invite"] = ip_invite
                                perms["can_add_employees"] = ip_add_emps
                                perms["can_edit_employees"] = ip_edit_emps
                                perms["can_delete_employees"] = ip_del_emps
                                
                                invite = create_invite_token(company_id, i_email, i_name, i_col, perms, st.session_state.user_name)
                                invite_link = f"http://localhost:8501/?invite={invite['token']}"
                                
                                if EMAIL_ENABLED:
                                    send_employee_invite(i_email, st.session_state.company_name, i_name, st.session_state.user_name, invite_link)
                                    st.success(f"Invite sent to {i_email}!")
                                else:
                                    st.warning("Email service not configured. Share this link manually:")
                                    st.code(f"?invite={invite['token']}")
                                    st.success(f"Invite created for {i_name}")
                                    
                            except ValueError as e:
                                st.error(str(e))
                        else:
                            st.error("Name and Email required")
                
                st.markdown("---")
                st.subheader("Pending Invites")
                invites = get_pending_invites(company_id)
                if invites:
                    for inv in invites:
                        c1, c2, c3 = st.columns([3, 2, 1])
                        with c1:
                            st.markdown(f"**{inv['name']}** ({inv['email']})")
                            st.caption(f"Invited by {inv['created_by']}")
                        with c2:
                            st.text(f"Expires: {inv['expires_at'][:10]}")
                        with c3:
                            if st.button("Cancel", key=f"cncl_{inv['id']}"):
                                delete_invite(company_id, inv["id"])
                                st.rerun()
                else:
                    st.caption("No pending invites")
    
    # ===== DAILY ENTRY =====
    elif page == "📝 Daily Entry":
        st.markdown('<h1 class="main-header">📝 Daily Entry</h1>', unsafe_allow_html=True)
        
        employees = get_employees(company_id)
        if not employees:
            st.warning("Add employees first!")
            return
        
        selected_date = st.date_input("📅 Date", value=date.today())
        
        st.markdown("---")
        
        # Shared Items Prices
        st.subheader("💰 Shared Items (Total Cost)")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            ex_rice = get_daily_shared_item(company_id, selected_date, "rice")
            rice_price = st.number_input("🍚 Rice Total", min_value=0, value=int(ex_rice["total_price"]) if ex_rice else 0, step=10)
            if st.button("Save Rice"):
                set_daily_shared_item(company_id, selected_date, "rice", rice_price)
                st.success("Saved!")
        with c2:
            ex_salan = get_daily_shared_item(company_id, selected_date, "salan")
            salan_price = st.number_input("🍛 Salan Total", min_value=0, value=int(ex_salan["total_price"]) if ex_salan else 0, step=10)
            if st.button("Save Salan"):
                set_daily_shared_item(company_id, selected_date, "salan", salan_price)
                st.success("Saved!")
        with c3:
            ex_other = get_daily_shared_item(company_id, selected_date, "other")
            other_price = st.number_input("🍱 Other Total", min_value=0, value=int(ex_other["total_price"]) if ex_other else 0, step=10)
            if st.button("Save Other"):
                set_daily_shared_item(company_id, selected_date, "other", other_price)
                st.success("Saved!")
        
        st.markdown("---")
        
        menu_items = get_menu_items(company_id)
        prices = {m["id"]: m["price"] for m in menu_items}
        st.markdown(f"**Fixed Prices:** Roti = PKR {prices.get('roti', 20)} | Naan = PKR {prices.get('naan', 25)} | Tea = PKR {prices.get('tea', 15)}")
        
        st.markdown("---")
        st.subheader("🍽️ Employee Meals")
        
        # Header
        cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1])
        cols[0].markdown("**Employee**")
        cols[1].markdown("**Roti**")
        cols[2].markdown("**Naan**")
        cols[3].markdown("**Tea**")
        cols[4].markdown("**Rice**")
        cols[5].markdown("**Salan**")
        cols[6].markdown("**Other**")
        cols[7].markdown("**Cost**")
        cols[8].markdown("**Save**")
        
        # Filter employees if "can_view_all" is missing
        display_employees = employees
        if current_employee_id and not has_permission("can_view_all"):
             display_employees = [e for e in employees if e["id"] == current_employee_id]

        for emp in display_employees:
            existing = get_record_for_date(company_id, emp["id"], selected_date)
            
            # Handle tea as int
            existing_tea = existing.get("tea", 0) if existing else 0
            if isinstance(existing_tea, bool):
                existing_tea = 1 if existing_tea else 0
            
            cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1, 1])
            cols[0].markdown(f"**{emp['name']}**")
            
            roti = cols[1].number_input("r", 0, 10, existing["roti"] if existing else 0, label_visibility="collapsed", key=f"r_{emp['id']}_{selected_date}")
            naan = cols[2].number_input("n", 0, 10, existing["naan"] if existing else 0, label_visibility="collapsed", key=f"n_{emp['id']}_{selected_date}")
            tea = cols[3].number_input("t", 0, 10, existing_tea, label_visibility="collapsed", key=f"t_{emp['id']}_{selected_date}")
            rice = cols[4].checkbox("ri", existing["rice"] if existing else False, label_visibility="collapsed", key=f"ri_{emp['id']}_{selected_date}")
            
            has_bread = roti > 0 or naan > 0
            salan = cols[5].checkbox("s", existing["salan"] if existing else False, disabled=not has_bread, label_visibility="collapsed", key=f"s_{emp['id']}_{selected_date}")
            other = cols[6].checkbox("o", existing.get("other", False) if existing else False, label_visibility="collapsed", key=f"o_{emp['id']}_{selected_date}")
            
            cost = roti * prices.get('roti', 20) + naan * prices.get('naan', 25) + tea * prices.get('tea', 15)
            cols[7].markdown(f"~{int(cost)}")
            
            if cols[8].button("💾", key=f"sv_{emp['id']}_{selected_date}"):
                add_daily_record(company_id, emp["id"], selected_date, roti, naan, rice, salan if has_bread else False, tea, other)
                st.success(f"Saved {emp['name']}")
                st.rerun()
    
    # ===== MONTHLY REPORT =====
    elif page == "📊 Monthly Report":
        st.markdown('<h1 class="main-header">📊 Monthly Report</h1>', unsafe_allow_html=True)
        
        employees = get_employees(company_id)
        if not employees:
            st.warning("Add employees first!")
            return
        
        c1, c2 = st.columns(2)
        with c1:
            months = list(calendar.month_name)[1:]
            month = st.selectbox("Month", range(1, 13), format_func=lambda x: months[x-1], index=date.today().month-1)
        with c2:
            year = st.selectbox("Year", range(2024, 2030), index=date.today().year-2024)
        
        st.markdown("---")
        
        # Build report
        data = []
        for emp in employees:
            col = get_monthly_collection(company_id, emp["id"], month, year)
            collected = col["amount"] if col else emp["monthly_collection"]
            consumed = calculate_monthly_consumption(company_id, emp["id"], month, year)
            records = get_daily_records(company_id, emp["id"], month, year)
            
            data.append({
                "Employee": emp["name"],
                "Collection": int(collected),
                "Roti": sum(r["roti"] for r in records),
                "Naan": sum(r["naan"] for r in records),
                "Tea": sum(r.get("tea", 0) if isinstance(r.get("tea"), int) else (1 if r.get("tea") else 0) for r in records),
                "Rice": sum(1 for r in records if r["rice"]),
                "Salan": sum(1 for r in records if r["salan"]),
                "Other": sum(1 for r in records if r.get("other")),
                "Consumed": int(consumed),
                "Balance": int(collected - consumed)
            })
        
        df = pd.DataFrame(data)
        
        # Summary
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("Total Collection", format_pkr(df["Collection"].sum()), "💰")
        with c2:
            metric_card("Total Consumed", format_pkr(df["Consumed"].sum()), "🍽️")
        with c3:
            bal = df["Balance"].sum()
            metric_card("Total Balance", format_pkr(bal), "✅" if bal >= 0 else "⚠️")
        
        st.markdown("---")
        
        # Table
        def color_bal(val):
            if isinstance(val, (int, float)):
                return 'background-color: rgba(16,185,129,0.3)' if val >= 0 else 'background-color: rgba(239,68,68,0.3)'
            return ''
        
        st.dataframe(df.style.map(color_bal, subset=["Balance"]), use_container_width=True, hide_index=True)
        
        st.download_button("📥 Download CSV", df.to_csv(index=False), f"report_{months[month-1]}_{year}.csv", use_container_width=True)
    
    # ===== SETTINGS =====
    elif page == "⚙️ Settings" and has_permission("can_manage_settings"):
        st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
        
        company = get_company_by_id(company_id)
        
        st.subheader("🏢 Company Profile")
        with st.form("update_profile"):
            new_name = st.text_input("Company Name", value=company["name"])
            new_admin = st.text_input("Admin Name", value=company["admin_name"])
            if st.form_submit_button("Update Profile"):
                update_company(company_id, name=new_name, admin_name=new_admin)
                st.session_state.company_name = new_name
                st.session_state.user_name = new_admin
                st.success("Updated!")
                st.rerun()
        
        st.markdown("---")
        st.subheader("💰 Menu Prices")
        
        menu_items = get_menu_items(company_id)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            curr_roti = next((m["price"] for m in menu_items if m["id"] == "roti"), 20)
            new_roti = st.number_input("Roti Price", value=curr_roti)
            if st.button("Update Roti"):
                update_menu_price(company_id, "roti", new_roti)
                st.success("Updated!")
                st.rerun()
        
        with c2:
            curr_naan = next((m["price"] for m in menu_items if m["id"] == "naan"), 25)
            new_naan = st.number_input("Naan Price", value=curr_naan)
            if st.button("Update Naan"):
                update_menu_price(company_id, "naan", new_naan)
                st.success("Updated!")
                st.rerun()
        
        with c3:
            curr_tea = next((m["price"] for m in menu_items if m["id"] == "tea"), 15)
            # Ensure price is treated as number, not bool from old logic
            if isinstance(curr_tea, bool): curr_tea = 15 
            new_tea = st.number_input("Tea Price", value=int(curr_tea))
            if st.button("Update Tea"):
                update_menu_price(company_id, "tea", new_tea)
                st.success("Updated!")
                st.rerun()
        
        st.markdown("---")
        
        # Collections
        st.subheader("💵 Monthly Collections")
        employees = get_employees(company_id)
        today = date.today()
        
        if employees:
            with st.form("collections"):
                st.markdown(f"**{calendar.month_name[today.month]} {today.year}**")
                for emp in employees:
                    ex = get_monthly_collection(company_id, emp["id"], today.month, today.year)
                    val = int(ex["amount"]) if ex else int(emp["monthly_collection"])
                    c1, c2 = st.columns([2, 2])
                    with c1:
                        st.markdown(f"**{emp['name']}**")
                    with c2:
                        st.number_input(f"c_{emp['id']}", value=val, step=100, label_visibility="collapsed", key=f"col_{emp['id']}")
                
                if st.form_submit_button("Save Collections"):
                    for emp in employees:
                        amt = st.session_state.get(f"col_{emp['id']}", emp["monthly_collection"])
                        add_monthly_collection(company_id, emp["id"], today.month, today.year, amt)
                    st.success("Saved!")
                    st.rerun()
        
        # Danger Zone - Delete Company (Company Admin Only)
        if st.session_state.user_type == "company_admin":
            st.markdown("---")
            st.error("🚨 Danger Zone")
            with st.expander("🗑️ Delete Company Account"):
                st.warning("This action cannot be undone. All data will be permanently deleted.")
                with st.form("delete_company_form"):
                    conf_pass = st.text_input("Enter Admin Password to Confirm", type="password")
                    if st.form_submit_button("Permanently Delete Company"):
                        if verify_password(conf_pass, company["password_hash"]):
                            delete_company(company_id)
                            st.success("Account deleted.")
                            logout()
                        else:
                            st.error("Incorrect password")

        st.markdown("---")
        st.subheader("ℹ️ About")
        if logo_base64:
            st.image(f"data:image/jpeg;base64,{logo_base64}", width=100)
        st.markdown("""
        **Lunch Expense Management Platform** v3.0
        
        Features: Employee & Member management, Tea + Shared items, Monthly reports, PKR currency
        
        **Developed by Software Bazaar IT Solutions**
        
        *Founded by Mirza M Mobeen*
        """)

# ==================== MAIN ====================
if not st.session_state.logged_in:
    show_login_page()
elif st.session_state.user_type == "super_admin":
    show_super_admin_dashboard()
else:
    show_company_dashboard()
