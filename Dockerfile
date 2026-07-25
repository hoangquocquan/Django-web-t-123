FROM python:3.12-slim

# WORKDIR là thư mục làm việc bên trong container.
# Các lệnh phía sau sẽ chạy trong /app.
WORKDIR /app

# Copy toàn bộ project vào container.
COPY . .

# Dự án hiện dùng thư viện chuẩn của Python, nên requirements có thể rỗng.
RUN pip install --no-cache-dir -r backend/requirements.txt

# ENV là cấu hình mặc định khi chạy trong Docker.
# MEC_HOST=0.0.0.0 giúp web trong container nhận request từ bên ngoài container.
ENV MEC_ENV=production
ENV MEC_DEBUG=false
ENV MEC_HOST=0.0.0.0
ENV MEC_PORT=8000
ENV MEC_DATABASE_PATH=/app/backend/database/mecprecision.sqlite

# EXPOSE chỉ ghi chú rằng container dùng port 8000.
# Khi chạy thật vẫn cần map port, ví dụ 8000:8000 trong docker-compose.yml.
EXPOSE 8000

# CMD là lệnh khởi động backend khi container chạy.
CMD ["python", "backend/app.py"]
