import os
from services.emailer import send_email
from dotenv import load_dotenv

# โหลด .env
load_dotenv()

print("cwd =", os.getcwd())
print(".env path =", os.path.join(os.getcwd(), ".env"))
print("SMTP_HOST =", os.getenv("SMTP_HOST"))
print("SMTP_PORT =", os.getenv("SMTP_PORT"))
print("SMTP_USER =", os.getenv("SMTP_USER"))
print("FROM_ADDR =", os.getenv("FROM_ADDR"))
print("SMTP_PASS set? =", bool(os.getenv("SMTP_PASS")))

try:
    # ส่งไปยังอีเมลนักศึกษา
    send_email(
        "652021044@tsu.ac.th", 
        "ทดสอบ Brevo", 
        "สวัสดีครับ 🎉\nนี่คืออีเมลทดสอบจาก Cocoa App ผ่าน Brevo SMTP"
    )
    print("✅ ส่งสำเร็จ")
except Exception as e:
    print("❌ ส่งไม่สำเร็จ:", e)
