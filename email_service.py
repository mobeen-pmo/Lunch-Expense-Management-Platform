"""
Email Service for Lunch Management Platform
Developed by Software Bazaar IT Solutions

Handles OTP verification and email notifications
"""

import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import json
import os

# Email Configuration - Software Bazaar IT Solutions
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "softwarebazaaritsolutions@gmail.com",
    "sender_name": "Software Bazaar IT Solutions",
    "app_password": "poxmfdmnwwmbrtzx"  # Gmail App Password (no spaces)
}

# Use absolute path based on this file's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OTP_FILE = os.path.join(SCRIPT_DIR, "data", "otp_store.json")

def generate_otp(length=6):
    """Generate a random OTP"""
    return ''.join(random.choices(string.digits, k=length))

def store_otp(email: str, otp: str, purpose: str = "registration"):
    """Store OTP with expiry (10 minutes)"""
    data_dir = os.path.join(SCRIPT_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    otp_data = {}
    if os.path.exists(OTP_FILE):
        with open(OTP_FILE, 'r') as f:
            otp_data = json.load(f)
    
    otp_data[email.lower()] = {
        "otp": otp,
        "purpose": purpose,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
    }
    
    with open(OTP_FILE, 'w') as f:
        json.dump(otp_data, f, indent=2)

def verify_otp(email: str, otp: str, purpose: str = "registration") -> bool:
    """Verify OTP"""
    if not os.path.exists(OTP_FILE):
        return False
    
    with open(OTP_FILE, 'r') as f:
        otp_data = json.load(f)
    
    email_lower = email.lower()
    if email_lower not in otp_data:
        return False
    
    stored = otp_data[email_lower]
    
    # Check expiry
    expires_at = datetime.fromisoformat(stored["expires_at"])
    if datetime.now() > expires_at:
        return False
    
    # Check OTP and purpose
    if stored["otp"] == otp and stored["purpose"] == purpose:
        # Remove used OTP
        del otp_data[email_lower]
        with open(OTP_FILE, 'w') as f:
            json.dump(otp_data, f, indent=2)
        return True
    
    return False

def send_email(to_email: str, subject: str, html_body: str, app_password: str = None) -> bool:
    """Send email using Gmail SMTP"""
    try:
        password = app_password or EMAIL_CONFIG["app_password"]
        if not password:
            print("Email app password not configured")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = to_email
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], password)
            server.sendmail(EMAIL_CONFIG['sender_email'], to_email, msg.as_string())
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ==================== EMAIL TEMPLATES ====================

def get_otp_email(otp: str, company_name: str) -> str:
    """OTP verification email template"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #1e3a5f, #2ecc71); padding: 30px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 24px; }}
            .content {{ padding: 40px 30px; }}
            .otp-box {{ background: linear-gradient(135deg, #1e3a5f, #2ecc71); color: white; font-size: 32px; font-weight: bold; letter-spacing: 8px; padding: 20px; text-align: center; border-radius: 12px; margin: 20px 0; }}
            .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            .logo {{ font-size: 40px; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🍽️</div>
                <h1>Lunch Management Platform</h1>
            </div>
            <div class="content">
                <h2>Verify Your Email</h2>
                <p>Hello! You're registering <strong>{company_name}</strong> on our platform.</p>
                <p>Please use the following OTP to complete your registration:</p>
                <div class="otp-box">{otp}</div>
                <p><strong>This OTP is valid for 10 minutes.</strong></p>
                <p>If you didn't request this, please ignore this email.</p>
            </div>
            <div class="footer">
                <p><strong>Software Bazaar IT Solutions</strong></p>
                <p>Building Smart Solutions for Smart Businesses</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_welcome_email(company_name: str, admin_name: str) -> str:
    """Welcome email template after successful registration"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #1e3a5f, #2ecc71); padding: 30px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 24px; }}
            .content {{ padding: 40px 30px; }}
            .feature-list {{ background: #f8f9fa; padding: 20px; border-radius: 12px; margin: 20px 0; }}
            .feature-list li {{ margin: 10px 0; }}
            .cta-button {{ display: inline-block; background: linear-gradient(135deg, #1e3a5f, #2ecc71); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
            .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            .logo {{ font-size: 40px; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🎉</div>
                <h1>Welcome to Lunch Management Platform!</h1>
            </div>
            <div class="content">
                <h2>Hello {admin_name}!</h2>
                <p>Congratulations! <strong>{company_name}</strong> has been successfully registered on our platform.</p>
                
                <div class="feature-list">
                    <h3>🚀 What you can do:</h3>
                    <ul>
                        <li>👥 Add and manage employees</li>
                        <li>📝 Track daily meal consumption (Roti, Naan, Rice, Salan, Tea)</li>
                        <li>💰 Manage monthly collections</li>
                        <li>📊 Generate detailed reports</li>
                        <li>👤 Add team members with different roles</li>
                        <li>📥 Export reports to CSV</li>
                    </ul>
                </div>
                
                <p>Start by adding your employees and setting up your menu prices!</p>
                
                <p style="color: #666;">If you have any questions, feel free to contact us.</p>
            </div>
            <div class="footer">
                <p><strong>Software Bazaar IT Solutions</strong></p>
                <p>Building Smart Solutions for Smart Businesses</p>
                <p>📧 softwareitbazaar@gmail.com</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_password_reset_email(otp: str, user_name: str) -> str:
    """Password reset email template"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #dc2626, #f59e0b); padding: 30px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 24px; }}
            .content {{ padding: 40px 30px; }}
            .otp-box {{ background: linear-gradient(135deg, #dc2626, #f59e0b); color: white; font-size: 32px; font-weight: bold; letter-spacing: 8px; padding: 20px; text-align: center; border-radius: 12px; margin: 20px 0; }}
            .warning {{ background: #fef2f2; border: 1px solid #fecaca; padding: 15px; border-radius: 8px; color: #dc2626; margin: 20px 0; }}
            .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            .logo {{ font-size: 40px; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🔐</div>
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <h2>Hello {user_name}!</h2>
                <p>We received a request to reset your password. Use the following OTP to proceed:</p>
                <div class="otp-box">{otp}</div>
                <p><strong>This OTP is valid for 10 minutes.</strong></p>
                
                <div class="warning">
                    <strong>⚠️ Security Notice:</strong> If you didn't request this password reset, please ignore this email and ensure your account is secure.
                </div>
            </div>
            <div class="footer">
                <p><strong>Software Bazaar IT Solutions</strong></p>
                <p>Building Smart Solutions for Smart Businesses</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_member_invite_email(company_name: str, member_name: str, temp_password: str) -> str:
    """Member invitation email template"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #7c3aed, #a855f7); padding: 30px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 24px; }}
            .content {{ padding: 40px 30px; }}
            .credentials {{ background: #f8f9fa; padding: 20px; border-radius: 12px; margin: 20px 0; }}
            .credentials p {{ margin: 10px 0; }}
            .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            .logo {{ font-size: 40px; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">👋</div>
                <h1>You've Been Invited!</h1>
            </div>
            <div class="content">
                <h2>Hello {member_name}!</h2>
                <p>You've been added as a member of <strong>{company_name}</strong> on the Lunch Management Platform.</p>
                
                <div class="credentials">
                    <h3>🔑 Your Login Credentials:</h3>
                    <p><strong>Temporary Password:</strong> {temp_password}</p>
                    <p style="color: #dc2626;"><em>Please change your password after first login!</em></p>
                </div>
                
                <p>You can now track your daily meals and view reports.</p>
            </div>
            <div class="footer">
                <p><strong>Software Bazaar IT Solutions</strong></p>
                <p>Building Smart Solutions for Smart Businesses</p>
            </div>
        </div>
    </body>
    </html>
    """

# Helper function to send OTP
def send_registration_otp(email: str, company_name: str, app_password: str = None) -> tuple:
    """Send OTP for registration. Returns (success, otp)"""
    otp = generate_otp()
    store_otp(email, otp, "registration")
    
    html = get_otp_email(otp, company_name)
    success = send_email(email, "🔐 Verify Your Email - Lunch Management Platform", html, app_password)
    
    return success, otp

def send_password_reset_otp(email: str, user_name: str, app_password: str = None) -> tuple:
    """Send OTP for password reset. Returns (success, otp)"""
    otp = generate_otp()
    store_otp(email, otp, "password_reset")
    
    html = get_password_reset_email(otp, user_name)
    success = send_email(email, "🔐 Password Reset - Lunch Management Platform", html, app_password)
    
    return success, otp

def send_welcome_email_notification(email: str, company_name: str, admin_name: str, app_password: str = None) -> bool:
    """Send welcome email after registration"""
    html = get_welcome_email(company_name, admin_name)
    return send_email(email, "🎉 Welcome to Lunch Management Platform!", html, app_password)

def get_employee_invite_email(company_name: str, employee_name: str, inviter_name: str, invite_link: str) -> str:
    """Employee invitation email template with link"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #1e3a5f, #2ecc71); padding: 30px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 24px; }}
            .content {{ padding: 40px 30px; }}
            .invite-box {{ background: linear-gradient(135deg, rgba(30, 58, 95, 0.1), rgba(46, 204, 113, 0.1)); border: 2px solid #2ecc71; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center; }}
            .cta-button {{ display: inline-block; background: linear-gradient(135deg, #1e3a5f, #2ecc71); color: white !important; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; margin: 20px 0; }}
            .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            .logo {{ font-size: 40px; margin-bottom: 10px; }}
            .expire-notice {{ color: #f59e0b; font-size: 14px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">👋</div>
                <h1>You've Been Invited!</h1>
            </div>
            <div class="content">
                <h2>Hello {employee_name}!</h2>
                <p><strong>{inviter_name}</strong> has invited you to join <strong>{company_name}</strong> on the Lunch Management Platform.</p>
                
                <div class="invite-box">
                    <h3>🍽️ Join Your Team</h3>
                    <p>Click the button below to set up your account and start tracking your meals.</p>
                    <a href="{invite_link}" class="cta-button">Accept Invitation</a>
                    <p class="expire-notice">⏰ This invitation expires in 48 hours</p>
                </div>
                
                <p>Once you join, you'll be able to:</p>
                <ul>
                    <li>📝 View and track your daily meals</li>
                    <li>📊 See your monthly consumption and balance</li>
                    <li>🍽️ Access your personal dashboard</li>
                </ul>
                
                <p style="color: #666; font-size: 14px;">If you didn't expect this invitation, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p><strong>Software Bazaar IT Solutions</strong></p>
                <p>Building Smart Solutions for Smart Businesses</p>
            </div>
        </div>
    </body>
    </html>
    """

def send_employee_invite(email: str, company_name: str, employee_name: str, inviter_name: str, invite_link: str, app_password: str = None) -> bool:
    """Send employee invitation email with registration link"""
    html = get_employee_invite_email(company_name, employee_name, inviter_name, invite_link)
    return send_email(email, f"👋 {inviter_name} invited you to {company_name} - Lunch Management", html, app_password)

def get_employee_welcome_email(company_name: str, employee_name: str) -> str:
    """Employee welcome email template"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #1e3a5f, #2ecc71); padding: 30px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 24px; }}
            .content {{ padding: 40px 30px; }}
            .success-box {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }}
            .login-button {{ display: inline-block; background: #007bff; color: white !important; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 20px; }}
            .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            .logo {{ font-size: 40px; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🎉</div>
                <h1>Welcome Aboard!</h1>
            </div>
            <div class="content">
                <h2>Hi {employee_name},</h2>
                <p>You have successfully joined <strong>{company_name}</strong> on the Lunch Expense Management Platform.</p>
                
                <div class="success-box">
                    <strong>✅ Registration Complete</strong><br>
                    Your account is now active.
                </div>
                
                <p>You can now log in to:</p>
                <ul>
                    <li>🍛 Order lunch daily</li>
                    <li>💰 Handle your expense collection</li>
                    <li>📊 Track your monthly balance</li>
                </ul>
                
                <div style="text-align: center;">
                    <p>Go to your dashboard to get started.</p>
                </div>
            </div>
            <div class="footer">
                <p><strong>Software Bazaar IT Solutions</strong></p>
                <p>Building Smart Solutions for Smart Businesses</p>
                <p>Founded by Mirza M Mobeen</p>
            </div>
        </div>
    </body>
    </html>
    """

def send_employee_welcome(email: str, company_name: str, employee_name: str, app_password: str = None) -> bool:
    """Send welcome email to employee"""
    html = get_employee_welcome_email(company_name, employee_name)
    return send_email(email, f"🎉 Welcome to {company_name} - Registration Complete", html, app_password)

