# test_detect.py
import requests, json
from pathlib import Path

BASE = "http://127.0.0.1:5000/api/detect"
# ใช้ upload_root จาก JSON ของคุณ
UPLOAD_ROOT = Path(r"D:\2568_1\cocoa\cocoaServer\static\uploads")

def pretty(o): return json.dumps(o, ensure_ascii=False, indent=2)

def main():
    # 1) เช็ก labels (trigger โหลดโมเดล)
    print("== GET /labels ==")
    r = requests.get(f"{BASE}/labels", timeout=60)
    print(r.status_code, pretty(r.json()))

    # 2) รวบรวมรูปทั้งหมดใต้ inspections/**
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images_abs = [p for p in (UPLOAD_ROOT / "inspections").rglob("*") if p.suffix.lower() in exts]

    if not images_abs:
        print("\n⚠️ ไม่พบไฟล์รูปใน", UPLOAD_ROOT / "inspections")
        print("   ใส่รูปเช่น leaf1.jpg ไว้ในโฟลเดอร์ inspections/63 หรือ 64 แล้วรันใหม่")
        return

    # แปลงเป็น path แบบ relative จาก UPLOAD_ROOT ตามที่ API คาดหวัง
    images_rel = [str(p.relative_to(UPLOAD_ROOT)).replace("\\", "/") for p in images_abs]

    # เพื่อไม่ยิงหนักเกินไป ลองแค่ 5 รูปแรก (ปรับได้)
    sample = images_rel[:5]
    payload = {"images": sample, "conf": 0.25}

    print("\n== POST /api/detect with", len(sample), "image(s) ==")
    print("payload:", pretty(payload))
    r = requests.post(f"{BASE}", json=payload, timeout=180)
    print("status:", r.status_code)
    resp = r.json()
    print(pretty(resp))

    # 3) สรุปย่อผลลัพธ์
    if resp.get("success"):
        print("\n✅ สรุปผล:")
        for i, item in enumerate(resp.get("results", []), 1):
            preds = item.get("preds", [])
            top = preds[0] if preds else None
            if top:
                print(f"  {i}. {Path(item['image']).name}: {top['class']} ({top['confidence']:.2f})")
            else:
                print(f"  {i}. {Path(item['image']).name}: — no preds —")
    else:
        print("\n❌ ไม่สำเร็จ:", resp)

if __name__ == "__main__":
    main()
