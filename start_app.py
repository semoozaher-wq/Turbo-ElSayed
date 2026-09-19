import os

print("جاري تحديث الملفات من GitHub...")
os.system("git pull origin main")

print("جاري تشغيل التطبيق...")
os.system("streamlit run webui/Main.py --server.port 8502 --server.address 0.0.0.0")
