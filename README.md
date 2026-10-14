# TinHoc Education Platform 🎓💻

Nền tảng học tập và giáo dục trực tuyến môn Tin học toàn diện, hiện đại, hỗ trợ học sinh và giáo viên trong việc quản lý bài giảng, tài liệu PDF, luyện tập lập trình và làm bài tập trắc nghiệm.

---

## 📑 Mục lục
- [Giới thiệu dự án](#-giới-thiệu-dự-án)
- [Kiến trúc & Công nghệ](#-kiến-trúc--công-nghệ)
- [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Hướng dẫn cài đặt & Khởi chạy](#-hướng-dẫn-cài-đặt--khởi-chạy)
  - [Cách 1: Khởi chạy bằng Docker Compose (Khuyến nghị)](#cách-1-khởi-chạy-bằng-docker-compose-khuyến-nghị)
  - [Cách 2: Cài đặt và chạy Local Development](#cách-2-cài-đặt-và-chạy-local-development)
- [Cấu hình biến môi trường (.env)](#-cấu-hình-biến-môi-trường-env)
- [Tài liệu API](#-tài-liệu-api)
- [Quy trình đóng góp (Contributing)](#-quy-trình-đóng-góp-contributing)

---

## 🌟 Giới thiệu dự án

**TinHoc Education Platform** là giải pháp phần mềm mã nguồn mở được thiết kế cho ngành giáo dục môn Tin học:
- **Tương tác tài liệu & PDF:** Tích hợp trình xem tài liệu và bài giảng trực quan (`vue-pdf-embed`, `pdfjs-dist`).
- **Soạn thảo và hiển thị code/toán học:** Hỗ trợ highlight cú pháp lập trình (`PrismJS`) và công thức toán học (`KaTeX`).
- **Hệ thống xử lý tác vụ ngầm:** Tích hợp Redis & Celery broker cho các tác vụ chấm điểm, phân tích và xử lý file không đồng bộ.
- **Bảo mật và hiệu năng:** Backend xử lý bất đồng bộ hoàn toàn với FastAPI, SQLAlchemy Async, bảo mật JWT và cơ chế làm sạch dữ liệu đầu vào.

---

## 🛠 Kiến trúc & Công nghệ

### 1. Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **ORM & Database Client:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async) + `aiomysql` / `PyMySQL`
- **Migration:** [Alembic](https://alembic.sqlalchemy.org/)
- **Validation & Settings:** [Pydantic v2](https://docs.pydantic.dev/) + `pydantic-settings`
- **Xác thực & Bảo mật:** JWT (`python-jose`), `passlib` / `bcrypt`, làm sạch nội dung với `bleach`
- **Queue / Background Task Broker:** Redis 7

### 2. Frontend
- **Framework:** [Vue 3](https://vuejs.org/) (Composition API, `<script setup>`)
- **Build Tool:** [Vite](https://vite.dev/)
- **Styling:** [Tailwind CSS v4](https://tailwindcss.com/)
- **Tiện ích:** [VueUse](https://vueuse.org/), [Axios](https://axios-http.com/)
- **Trình diễn nội dung:** `KaTeX`, `PrismJS`, `vue-pdf-embed`

### 3. Hạ tầng & Cơ sở dữ liệu
- **Database:** MySQL 8.0
- **Cache & Broker:** Redis 7
- **Containerization:** Docker & Docker Compose

---

## 📂 Cấu trúc thư mục

```plaintext
tinhoc-education-platform/
├── backend/                             # Ứng dụng Backend (FastAPI)
│   ├── alembic/                         # Database migration scripts
│   ├── app/                             # Mã nguồn chính backend
│   │   ├── core/                        # Cấu hình hệ thống, bảo mật, database session
│   │   ├── middleware/                  # Custom middlewares (CORS, logging, audit)
│   │   ├── models/                      # SQLAlchemy ORM models
│   │   ├── routers/                     # API routes (Endpoints)
│   │   ├── schemas/                     # Pydantic schemas (Request/Response DTOs)
│   │   ├── services/                    # Business logic services
│   │   └── workers/                     # Background tasks / Celery jobs
│   ├── storage/                         # Lưu trữ tệp tin upload (contributions, avatar,...)
│   │   └── contributions/               # Tệp đóng góp từ người dùng
│   ├── tests/                           # Unit & integration tests
│   └── requirements.txt                 # Danh sách thư viện Python
├── frontend/                            # Ứng dụng Frontend (Vue 3 + Vite)
│   ├── public/                          # Static assets
│   ├── src/                             # Mã nguồn chính frontend
│   │   ├── api/                         # Axios API clients
│   │   ├── assets/                      # CSS, SVG, hình ảnh
│   │   ├── components/                  # UI components tái sử dụng (code, pdf, common)
│   │   ├── router/                      # Vue Router cấu hình điều hướng
│   │   ├── store/                       # State management (Pinia / reactive stores)
│   │   ├── views/                       # Các trang màn hình chính
│   │   ├── App.vue                      # Root component
│   │   └── main.js                      # Entry point ứng dụng
│   ├── package.json                     # Danh sách npm dependencies & scripts
│   └── vite.config.js                   # Cấu hình Vite & plugins
├── .gitignore                           # Chặn tệp nhạy cảm và tệp rác khi commit
├── docker-compose.yml                   # Cấu hình Docker Compose triển khai toàn cụm
└── README.md                            # Tài liệu hướng dẫn dự án
```

---

## ⚙️ Yêu cầu hệ thống

Trước khi bắt đầu, hãy đảm bảo máy tính đã cài đặt các công cụ sau:
- **Docker & Docker Compose** (nếu chạy bằng container)
- **Python 3.10+** (nếu chạy local backend)
- **Node.js 20+ hoặc 22+** và **npm** (nếu chạy local frontend)
- **Git**

---

## 🚀 Hướng dẫn cài đặt & Khởi chạy

### Cách 1: Khởi chạy bằng Docker Compose (Khuyến nghị)

Chạy toàn bộ cụm dịch vụ (MySQL Database, Redis Cache/Broker, Backend FastAPI) chỉ với một câu lệnh tại thư mục gốc:

```bash
docker compose up -d
```

Kiểm tra trạng thái các container:
```bash
docker compose ps
```

Khi chạy thành công:
- **Frontend App (Vue 3 + Vite):** [http://localhost:5173](http://localhost:5173)
- **Backend API (FastAPI):** [http://localhost:8000](http://localhost:8000)
- **Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **MySQL Database:** `localhost:3307` (Database: `tinhoc_education_db`, User: `root`, Password: `123456`)
- **Redis Server:** `localhost:6379`

Dừng cụm container:
```bash
docker compose down
```

---

### Cách 2: Cài đặt và chạy Local Development

#### 1. Khởi động Backend (FastAPI)

1. Di chuyển vào thư mục backend:
   ```bash
   cd backend
   ```

2. Tạo và kích hoạt môi trường ảo:
   - **Windows:**
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Cài đặt các thư viện:
   ```bash
   pip install -r requirements.txt
   ```

4. Tạo file cấu hình `.env` trong thư mục `backend/` (xem mẫu bên dưới).

5. Chạy cơ sở dữ liệu migration (Alembic):
   ```bash
   alembic upgrade head
   ```

6. Khởi chạy máy chủ API:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

#### 2. Khởi động Frontend (Vue 3 + Vite)

1. Mở một terminal mới và di chuyển vào thư mục frontend:
   ```bash
   cd frontend
   ```

2. Cài đặt các gói phụ thuộc:
   ```bash
   npm install
   ```

3. Khởi chạy development server:
   ```bash
   npm run dev
   ```

4. Mở trình duyệt và truy cập: [http://localhost:5173](http://localhost:5173)

---

## 🔐 Cấu hình biến môi trường (.env)

### Backend (`backend/.env`)
```env
PROJECT_NAME="TinHoc Education Platform"
ENVIRONMENT="development"
DEBUG=True

# Database Configuration
DATABASE_URL=mysql+aiomysql://root:123456@localhost:3306/tinhoc_education_db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# JWT Security
SECRET_KEY=your_super_secret_jwt_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Storage
UPLOAD_STORAGE_PATH=storage/contributions
```

### Frontend (`frontend/.env`)
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 📖 Tài liệu API

FastAPI cung cấp giao diện tương tác API tài liệu chuẩn hóa tự động:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🤝 Quy trình đóng góp (Contributing)

1. Fork dự án về tài khoản cá nhân.
2. Tạo nhánh tính năng mới:
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. Commit các thay đổi:
   ```bash
   git commit -m "feat: Thêm chức năng AmazingFeature"
   ```
4. Đẩy lên nhánh của bạn:
   ```bash
   git push origin feature/AmazingFeature
   ```
5. Mở một **Pull Request** trên GitHub để được review và merge.

---

## 📄 Bản quyền (License)

Dự án được phân phối dưới giấy phép [MIT License](LICENSE).

