# CẨM NANG HƯỚNG DẪN PHÁT TRIỂN & QUY CHUẨN KỸ THUẬT DỰ ÁN
## NỀN TẢNG HỌC TẬP, KHẢO THÍ & CHIA SẺ HỌC LIỆU TIN HỌC GDPT

Chào mừng bạn gia nhập đội ngũ phát triển dự án **TinHoc Education Platform**! 
Tài liệu này là "kim chỉ nam" giúp mọi thành viên trong nhóm (kể cả những bạn mới bắt đầu làm quen với lập trình Web) nắm vững toàn bộ bức tranh hệ thống, cách cài đặt môi trường, quy trình làm việc nhóm với Git không bao giờ bị đụng code, cũng như các tiêu chuẩn bắt buộc khi viết code.

---

## PHẦN I. GIẢI NGỐ CHO NGƯỜI MỚI: BACKEND (BE) VÀ FRONTEND (FE) LÀ GÌ?

Nếu bạn mới tham gia dự án và còn bỡ ngỡ chưa biết mình sẽ làm gì ở **Frontend (FE)** hay **Backend (BE)**, hãy hình dung hệ thống website của chúng ta giống như **một Nhà hàng hiện đại**:

```
[ HỌC SINH / GIÁO VIÊN ]
          |
          | (Nhìn thấy & Bấm nút)
          v
+-------------------------------------------------------------------+
| 1. FRONTEND (FE) - "Phòng ăn, Thực đơn & Nhân viên phục vụ"       |
| - Công nghệ: Vue 3 + Vite + Tailwind CSS + Pinia                  |
| - Nhiệm vụ: Hiển thị giao diện đẹp, hiệu ứng lật thẻ Flashcard,   |
|   đồng hồ đếm ngược 50 phút, nhận thao tác click của người dùng.  |
+-------------------------------------------------------------------+
          |
          | (Gửi yêu cầu qua mạng bằng gói tin JSON - Gọi API)
          v
+-------------------------------------------------------------------+
| 2. BACKEND (BE) - "Nhà bếp, Đầu bếp trưởng & Bộ não xử lý"        |
| - Công nghệ: Python FastAPI + SQLAlchemy 2.0 Async + Celery       |
| - Nhiệm vụ: Kiểm tra quyền hạn, chấm điểm bài thi, tính toán      |
|   thuật toán SM-2, lọc mã độc XSS, lưu nhật ký và đọc/ghi CSDL.   |
+-------------------------------------------------------------------+
          |
          | (Truy vấn & Lưu trữ dữ liệu)
          v
+-------------------------------------------------------------------+
| 3. DATABASE & CACHE - "Kho nguyên liệu & Tủ lạnh lấy đồ nhanh"    |
| - MySQL 8.0: Lưu trữ bền vững 45 bảng dữ liệu của hệ thống.       |
| - Redis 7: Lưu bộ nhớ đệm (Cache) siêu tốc và hàng đợi tác vụ.    |
+-------------------------------------------------------------------+
```

### 1. Frontend (FE) là gì và làm gì trong dự án này?
* **Khái niệm dễ hiểu:** Frontend là **tất cả những gì người dùng nhìn thấy và chạm vào được** trên màn hình trình duyệt (Chrome, Edge, Safari...).
* **Công việc cụ thể của bạn nếu làm FE (`thư mục frontend/`):**
  1. **Xây dựng giao diện (UI):** Cắt ghép bố cục trang chủ, trang đọc bài giảng lý thuyết, màn hình phòng thi 28 câu hỏi, giao diện lật thẻ Flashcard 3D, bảng xếp hạng.
  2. **Quản lý trạng thái (State Management với Pinia):** Lưu tạm các đáp án A, B, C, D mà học sinh đang tích chọn vào bộ nhớ trình duyệt để lỡ mất mạng vẫn không bị mất bài.
  3. **Gọi API (Bằng Axios):** Khi học sinh bấm nút *"Nộp bài"*, FE sẽ gom các câu trả lời lại thành một gói tin JSON và gửi sang cho Backend chấm điểm, sau đó nhận kết quả trả về để vẽ biểu đồ điểm số lên màn hình.
  4. **Trải nghiệm người dùng (UX):** Làm hiệu ứng đang tải (Skeleton/Loading), đổi giao diện Sáng/Tối (Light/Dark Mode), phím tắt chọn đáp án nhanh.

### 2. Backend (BE) là gì và làm gì trong dự án này?
* **Khái niệm dễ hiểu:** Backend là **phần chìm của tảng băng** nằm trên máy chủ (Server). Người dùng không nhìn thấy code Backend, nhưng mọi sự thông minh, tính toán và bảo mật đều nằm ở đây.
* **Công việc cụ thể của bạn nếu làm BE (`thư mục backend/`):**
  1. **Xây dựng các đầu mối giao tiếp (RESTful APIs):** Tạo ra các đường dẫn (ví dụ: `POST /api/v1/exams/submit`) để chờ Frontend gọi tới.
  2. **Xử lý logic nghiệp vụ (Business Logic):**
     * Chấm điểm bài thi theo đúng công thức Bộ GD&ĐT (câu MCQ $0.25$ điểm; câu Đúng/Sai tính điểm lũy tiến $0.1 \rightarrow 0.25 \rightarrow 0.5 \rightarrow 1.0$).
     * Tính toán ngày ôn tập tiếp theo của thẻ Flashcard bằng thuật toán lặp lại ngắt quãng SM-2.
     * Bóc tách tệp Word/PDF và tạo ảnh bìa thu nhỏ (Thumbnail) chạy ngầm bằng Celery Worker.
  3. **Bảo mật & Phân quyền:** Kiểm tra mật khẩu, cấp phát thẻ thông hành JWT Token, chặn học sinh xem trộm đáp án trước khi nộp bài, khử khuẩn mã độc XSS, giới hạn tốc độ gọi API (Rate Limit).
  4. **Làm việc với Cơ sở dữ liệu (Database):** Dùng SQLAlchemy 2.0 để thêm, sửa, xóa và tìm kiếm dữ liệu trong 45 bảng MySQL.

---

## PHẦN II. HƯỚNG DẪN SETUP DỰ ÁN KHI VỪA CLONE VỀ MÁY

Trước tiên, hãy tải (clone) mã nguồn dự án từ kho lưu trữ Git về máy tính của bạn:

```bash
git clone <đường-dẫn-link-git-của-nhóm>
cd tinhoc-education-platform
```

Để chạy được dự án trên máy cá nhân, bạn có **2 cách**. Nếu bạn là người mới, **hãy chọn Cách 1 (Dùng Docker)** vì nó tự động hóa $100\%$, không lo lỗi thiếu thư viện hay lệch phiên bản!

---

### CÁCH 1: Dùng Docker (Khuyến nghị – Nhanh và Đơn giản nhất)

* **Yêu cầu:** Máy tính đã cài đặt và đang bật ứng dụng **Docker Desktop**. Bạn **không cần** phải tự cài đặt thủ công Python, Node.js, MySQL hay Redis trên máy thật.

#### Bước 1: Mở Terminal (PowerShell / Command Prompt / Git Bash) tại thư mục vừa clone
```bash
cd tinhoc-education-platform
```

#### Bước 2: Khởi chạy toàn bộ cụm dịch vụ với 1 câu lệnh duy nhất
```bash
docker compose up -d --build
```
**Hệ thống sẽ tự động thực hiện từ A đến Z:**
1. Tải và cấu hình **MySQL 8.0** & **Redis 7**.
2. Build và cấu hình toàn bộ thư viện cho **Backend FastAPI** và **Frontend Vue 3**.
3. Tự động kết nối, tạo đầy đủ **45 bảng CSDL** chuẩn hóa.
4. Tự động nạp sẵn **Seed Data** ($4$ Roles, Khối lớp K10–K12, $16$ Chủ đề GDPT 2018, Chuyên mục diễn đàn và Danh mục tài liệu).

#### Bước 3: Truy cập vào ứng dụng
Ngay khi các container khởi động xong (báo chữ `Started` màu xanh), bạn mở trình duyệt web:
* 🌐 **Giao diện người dùng (Frontend):** `http://localhost:5173`
* 📖 **Tài liệu API tương tác (Swagger UI - nơi thử nghiệm các API của Backend):** `http://localhost:8000/docs`
* 🩺 **Kiểm tra trạng thái sức khỏe Backend:** `http://localhost:8000/health`

#### 🛠️ Các lệnh Docker hữu ích khi làm việc hằng ngày:
* **Xem trạng thái các container đang chạy:**
  ```bash
  docker compose ps
  ```
* **Xem nhật ký (log) hoạt động hoặc lỗi theo thời gian thực:**
  ```bash
  docker compose logs -f
  # Hoặc chỉ xem riêng log của Backend để debug lỗi Python:
  docker compose logs -f backend
  ```
* **Cập nhật lại Docker khi bạn hoặc đồng đội có thay đổi cấu trúc / thêm thư viện mới:**
  *(Lưu ý: Nếu bạn chỉ sửa code `.py` hoặc `.vue` thông thường, Docker đã có cơ chế Hot-Reload tự nhận diện. Nhưng nếu bạn thêm thư viện mới vào `requirements.txt`, `package.json`, hoặc sửa cấu hình Docker/DB, hãy chạy lệnh sau để cập nhật):*
  ```bash
  docker compose up -d --build
  ```
* **Tắt toàn bộ hệ thống khi nghỉ làm việc (giải phóng RAM):**
  ```bash
  docker compose down
  ```
* **Bật lại ở các lần làm việc sau (không cần build lại nên cực nhanh):**
  ```bash
  docker compose up -d
  ```

---

### CÁCH 2: Chạy trực tiếp trên máy (Local Development)

* **Yêu cầu:** Máy tính đã cài sẵn **Python 3.12+**, **Node.js 20+**, **MySQL 8.0** và **Redis** cục bộ.

#### 1. Khởi chạy Backend (FastAPI)
1. Mở Terminal và di chuyển vào thư mục `backend`:
   ```bash
   cd backend
   ```
2. Tạo và kích hoạt môi trường ảo (`venv`):
   * **Trên Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
     *(Nếu Windows báo lỗi ExecutionPolicy, hãy chạy lệnh: `Set-ExecutionPolicy Unrestricted -Scope Process` rồi chạy lại lệnh activate).*
   * **Trên macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. Cài đặt các thư viện Python:
   ```bash
   pip install -r requirements.txt
   ```
4. Tạo file cấu hình `backend/.env` (nếu chưa có):
   ```env
   PROJECT_NAME="TinHoc Education Platform"
   DEBUG=True
   DATABASE_URL=mysql+aiomysql://root:123456@localhost:3306/tinhoc_education_db
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=supersecretkey_change_in_production_123456789
   ```
5. Chạy server Backend:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   *(Server sẽ tự tạo 45 bảng và nạp seed data vào MySQL ngay lần chạy đầu tiên).*

#### 2. Khởi chạy Frontend (Vue 3 + Vite)
Mở một cửa sổ Terminal **mới** (giữ nguyên cửa sổ Backend đang chạy):
1. Di chuyển vào thư mục `frontend`:
   ```bash
   cd frontend
   ```
2. Cài đặt các gói thư viện npm:
   ```bash
   npm install
   ```
3. Chạy môi trường phát triển:
   ```bash
   npm run dev
   ```
4. Truy cập giao diện tại: `http://localhost:5173`

---

### 💡 Lưu ý quan trọng khi kết nối Cơ sở dữ liệu
* Khi chạy bằng **Docker**, cổng MySQL của container được ánh xạ (map) ra máy thật của bạn ở cổng **`3307`** (nhằm tránh xung đột nếu máy tính của bạn đã cài sẵn một bản MySQL khác đang chiếm cổng `3306`).
* Để mở xem bảng dữ liệu bằng các phần mềm quản trị CSDL như **DBeaver / Navicat / MySQL Workbench** trên máy thật, bạn điền thông số như sau:
  * **Host:** `localhost` hoặc `127.0.0.1`
  * **Port:** `3307` *(Nếu chạy Docker)* hoặc `3306` *(Nếu chạy MySQL cài trực tiếp trên máy)*
  * **User:** `root`
  * **Password:** `123456`
  * **Database:** `tinhoc_education_db`

---

## PHẦN III. QUY TRÌNH LÀM VIỆC VỚI GIT – TUYỆT ĐỐI KHÔNG ĐỤNG CODE!

> ⚠️ **NGUYÊN TẮC SỐNG CÒN CỦA NHÓM:**
> **TUYỆT ĐỐI KHÔNG BAO GIỜ** viết code trực tiếp hay push thẳng lên nhánh `main` (hoặc `develop`). Ai làm tính năng nào **bắt buộc phải tạo một nhánh (branch) riêng của người đó**, làm xong đẩy lên nhánh riêng rồi tạo yêu cầu gộp code (Pull Request). Làm đúng quy trình này thì cả nhóm 10 người cùng code sẽ không bao giờ giẫm chân lên nhau!

Dưới đây là quy trình 5 bước chuẩn chỉnh mỗi khi bạn bắt đầu ngồi vào máy code (hướng dẫn cả cách gõ lệnh Terminal lẫn cách bấm chuột trên VS Code):

### Bước 1: Trước khi làm việc $\rightarrow$ Luôn kéo (Pull) code mới nhất về máy!
Đồng đội của bạn có thể vừa hoàn thành tính năng mới tối qua. Trước khi tạo nhánh hoặc viết code, bạn phải lấy bản cập nhật mới nhất về:

* **Cách 1: Dùng lệnh Terminal**
  ```bash
  # Chuyển về nhánh chính (main)
  git checkout main

  # Kéo toàn bộ code mới nhất từ trên mạng (GitHub/GitLab) về máy
  git pull origin main
  ```
* **Cách 2: Dùng giao diện VS Code**
  1. Nhìn xuống góc dưới cùng bên trái màn hình VS Code, bấm vào tên nhánh hiện tại và chọn nhánh `main`.
  2. Bấm vào biểu tượng **Source Control** (hình nhánh cây ở thanh công cụ bên trái, hoặc ấn `Ctrl + Shift + G`).
  3. Bấm vào dấu `...` (More Actions) ở góc trên khung Source Control $\rightarrow$ Chọn **Pull**.

### Bước 2: Tạo một Nhánh (Branch) riêng cho tính năng của bạn
Quy ước đặt tên nhánh:
* Làm tính năng mới: `feature/<tên-ngắn-gọn>` (Ví dụ: `feature/auth-login`, `feature/flashcard-ui`, `feature/exam-grading`)
* Sửa lỗi: `fix/<tên-lỗi>` (Ví dụ: `fix/timer-bug`)

* **Cách 1: Dùng lệnh Terminal**
  ```bash
  # Lệnh này vừa tạo nhánh mới, vừa chuyển bạn sang nhánh đó luôn:
  git checkout -b feature/ten-tinh-nang-cua-ban
  ```
* **Cách 2: Dùng giao diện VS Code**
  1. Bấm vào tên nhánh `main` ở góc dưới cùng bên trái VS Code.
  2. Một bảng hiện ra ở giữa màn hình, chọn **"+ Create new branch..."**.
  3. Gõ tên nhánh (ví dụ: `feature/trang-dang-nhap`) rồi nhấn `Enter`.
  4. Kiểm tra góc dưới bên trái đã đổi sang tên nhánh mới của bạn là thành công!

### Bước 3: Tiến hành viết code & Cập nhật Docker
* Lúc này bạn hoàn toàn tự do viết code trong nhánh của mình mà không sợ làm hỏng code của người khác.
* **Lưu ý nếu dùng Docker:** 
  * Sau khi bạn `git pull` code mới về, hoặc sau khi bạn viết thêm bảng Database / cài thêm thư viện, hãy nhớ chạy lại lệnh sau để Docker cập nhật code và thư viện mới nhất:
    ```bash
    docker compose up -d --build
    ```
  * Nếu muốn khởi động lại nhanh riêng container Backend để nhận cấu hình mới:
    ```bash
    docker compose restart backend
    ```

### Bước 4: Đóng gói (Commit) và Đẩy code (Push) lên nhánh riêng của bạn
Khi đã code xong một phần công việc và chạy thử không có lỗi, hãy lưu và đẩy lên kho lưu trữ:

* **Cách 1: Dùng lệnh Terminal**
  ```bash
  # 1. Kiểm tra xem mình đã sửa những file nào (chữ màu đỏ/xanh)
  git status

  # 2. Đưa tất cả các file đã sửa vào vùng chuẩn bị đóng gói (Stage)
  git add .

  # 3. Đóng gói kèm lời nhắn rõ ràng mình vừa làm gì (Commit)
  git commit -m "feat: hoàn thành giao diện và API đăng nhập bằng Google"

  # 4. Đẩy nhánh của riêng bạn lên kho lưu trữ chung (Push)
  git push -u origin feature/ten-tinh-nang-cua-ban
  ```
* **Cách 2: Dùng giao diện VS Code / PyCharm / WebStorm (Rất trực quan)**
  1. Mở tab **Source Control** (`Ctrl + Shift + G`).
  2. Bạn sẽ thấy danh sách các file vừa sửa ở mục **Changes**. Hãy bấm vào từng file để xem lại phần so sánh (Diff) xem mình có để quên code nháp hay lỗi nào không.
  3. Di chuột vào dòng chữ **Changes** và bấm dấu **`+`** (*Stage All Changes*) để đưa các file lên mục **Staged Changes**.
  4. Ở ô nhập văn bản (**Message**) phía trên, gõ ghi chú rõ ràng (ví dụ: `"feat: thêm API chấm điểm câu hỏi đúng sai"`).
  5. Bấm nút **Commit** màu xanh.
  6. Ngay sau đó, nút đó sẽ đổi thành **Publish Branch** (hoặc **Sync Changes**). Bạn bấm vào đó để đẩy code lên GitHub/GitLab!

### Bước 5: Tạo Pull Request (Merge Request) để gộp code
1. Sau khi Push xong, bạn mở trang GitHub/GitLab của nhóm trên trình duyệt.
2. Bạn sẽ thấy nút màu xanh **"Compare & pull request"** vừa hiện lên cho nhánh của bạn $\rightarrow$ Bấm vào đó.
3. Điền mô tả ngắn gọn những gì bạn đã làm $\rightarrow$ Bấm **"Create pull request"**.
4. Nhắn vào nhóm chat để Trưởng nhóm (Team Lead) hoặc đồng đội vào kiểm tra (Review code) và bấm **Merge** vào nhánh chính.

---

## PHẦN IV. QUY CHUẨN VIẾT CODE & CÁC CHỐT CHẶN BẮT BUỘC

Để dự án chạy ổn định, dễ bảo trì và đạt điểm tối đa khi nghiệm thu, mọi thành viên khi code bất kỳ tính năng nào đều phải tuân thủ các quy tắc vàng sau đây:

### 1. Đọc kỹ Tài liệu Đặc tả trước khi gõ dòng code đầu tiên!
Trong dự án của chúng ta đã có sẵn bộ 3 tài liệu gốc cực kỳ chi tiết:
1. **`Tài liệu đặc tả.docx` (hoặc `.md`):** Chứa đầy đủ mô tả 8 Module, các bước xử lý từng luồng (Workflows), điều kiện rẽ nhánh, mã lỗi HTTP ($400, 401, 403, 404, 409, 422, 429$) và **cả các hình ảnh sơ đồ luồng hoạt động, sơ đồ ERD**.
2. **`database_design.md`:** Từ điển dữ liệu của đúng **45 bảng MySQL**, quy chuẩn JSON Schema cho 3 dạng câu hỏi và công thức chấm điểm.
3. **`security_xss_prevention_guide.md`:** Kiến trúc 4 lớp phòng chống mã độc XSS.

👉 **Mẹo cực hay khi làm việc:** Trước khi bắt đầu code một Module (ví dụ: Module 6 - Diễn đàn, hoặc Module 7 - Flashcard), bạn hãy mở `Tài liệu đặc tả` ngay tại chương đó, đọc kỹ luồng xử lý và **có thể gửi kèm cả nội dung văn bản lẫn hình ảnh sơ đồ trong tài liệu cho AI đọc**. Khi AI nhìn thấy sơ đồ luồng và cấu trúc bảng trong tài liệu, nó sẽ viết code chính xác $100\%$ theo thiết kế của nhóm mà không bịa ra tên bảng hay tên cột khác!

### 2. Viết Clean Code & Ưu tiên tối đa việc dùng lại hàm sẵn có (DRY)
* **Tuyệt đối không viết lặp lại những gì hệ thống đã xây dựng sẵn!** Trước khi tự viết một hàm kết nối DB, hàm kiểm tra token hay component hiển thị code, hãy nhìn vào thư mục `app/core/` (ở BE) và `src/components/common/` (ở FE).
* **Ở Backend (`backend/app/`):**
  * Luôn lấy phiên làm việc CSDL qua Dependency: `db: AsyncSession = Depends(get_db)`.
  * Luôn làm sạch văn bản HTML/Markdown bằng các hàm có sẵn trong `app/core/sanitizer.py` (`clean_html_content`, `clean_plain_text`).
  * Phân tầng rõ ràng: **`routers/`** chỉ nhận request và trả response; toàn bộ tính toán phức tạp phải đặt trong **`services/`**; cấu trúc dữ liệu đầu vào/đầu ra phải đặt trong **`schemas/`**.
* **Ở Frontend (`frontend/src/`):**
  * Khi cần hiển thị khối mã nguồn Python/SQL/HTML trong đề thi hoặc diễn đàn, **bắt buộc dùng lại component `<CodeBlock :code="..." :language="..." />`**.
  * Khi cần hiển thị nội dung bài giảng hoặc bình luận Markdown, **bắt buộc dùng lại `<SafeMarkdownViewer :content="..." />`**. Tuyệt đối cấm tự ý dùng `v-html` trần!

### 3. Năm (05) Chốt chặn Kỹ thuật Bắt buộc khi viết API Backend
Mọi API bạn viết ra đều phải đi qua đầy đủ các hàng rào bảo vệ sau:

#### ① Chốt chặn 1: Middleware Xác thực & Phân quyền (Authentication & RBAC)
* Không để lộ các API nội bộ. Phải gắn Dependency kiểm tra vai trò rõ ràng:
  * API dành cho học sinh: `current_user: User = Depends(get_current_active_user)`
  * API dành cho giáo viên/kiểm duyệt: `current_user: User = Depends(require_roles(["Instructor", "Reviewer", "Admin"]))`
  * API chỉ dành cho Quản trị viên: `current_user: User = Depends(require_roles(["Admin"]))`

#### ② Chốt chặn 2: Bảo mật Cấp độ Dòng dữ liệu – Row-Level Security (RLS / Ownership Check)
* **Đây là lỗi bảo mật cực kỳ phổ biến (IDOR) mà người mới và AI rất hay quên!**
* Việc người dùng đã đăng nhập (`Student`) **không có nghĩa** là họ được quyền xem hay sửa dữ liệu của học sinh khác.
* **Quy tắc bắt buộc:** Khi truy vấn hoặc cập nhật bất kỳ bản ghi cá nhân nào (bài thi `exam_submissions`, sổ tay câu sai `user_wrong_questions`, bài viết diễn đàn `forum_posts`, tiến độ học `user_lesson_progress`), câu lệnh `SELECT / UPDATE / DELETE` **bắt buộc phải kẹp thêm điều kiện `WHERE user_id == current_user.id`** (trừ khi người gọi là `Admin` hoặc `Instructor` được cấp quyền).
  ```python
  # ❌ SAI (Lỗ hổng nghiêm trọng: Học sinh A truyền ID bài thi của Học sinh B vào là xem được hết!):
  stmt = select(ExamSubmission).where(ExamSubmission.id == submission_id)

  # ✅ ĐÚNG (Row-Level Security: Chỉ chủ sở hữu bài thi mới truy xuất được):
  stmt = select(ExamSubmission).where(
      ExamSubmission.id == submission_id,
      ExamSubmission.user_id == current_user.id  # <-- Bắt buộc kiểm tra quyền sở hữu dòng!
  )
  ```

#### ③ Chốt chặn 3: Giới hạn Tần suất Gọi API (Rate Limiting)
* Mọi endpoint nhạy cảm hoặc tốn tài nguyên đều phải gắn bộ giới hạn tốc độ (Rate Limiter qua Redis) để chống spam và tấn công làm sập server (DoS / Brute-force):
  * API Đăng nhập / Gửi OTP / Quên mật khẩu: Tối đa **$5$ yêu cầu / phút / IP**.
  * API Tải tệp đóng góp lên: Tối đa **$5$ yêu cầu / phút / User**.
  * API Đăng câu hỏi diễn đàn: Tối đa **$1$ bài / $60$ giây / User**.
  * API Công khai: Tối đa **$120$ yêu cầu / phút / IP**.
* Khi vượt ngưỡng, trả về mã lỗi chuẩn `HTTP 429 Too Many Requests` kèm thông báo tiếng Việt thân thiện.

#### ④ Chốt chặn 4: Middleware Ghi Nhật ký Kiểm toán & Truy vết (Audit & Structured Logging)
* **Correlation-ID Middleware:** Mọi request đi vào Backend đều được tự động gắn một mã định danh duy nhất `X-Correlation-ID` để nếu có lỗi xảy ra, chúng ta tra cứu được toàn bộ hành trình của request đó.
* **Ghi bảng `audit_logs` (Bảng 45):** Bất kỳ thao tác nhạy cảm nào (Đăng nhập thành công/thất bại, Đổi mật khẩu, Cấp quyền Role, Khóa tài khoản, Phê duyệt/Gỡ tài liệu, Sửa đáp án câu hỏi thi) **bắt buộc phải gọi hàm ghi lại dấu vết vào bảng `audit_logs`** (lưu `user_id`, `action`, `ip_address`, `user_agent`, và `details` JSON).

#### ⑤ Chốt chặn 5: Giao dịch Trọn vẹn (ACID Transaction)
* Bất kỳ tính năng nào thực hiện ghi/cập nhật từ **2 bảng trở lên** (ví dụ: Nộp bài thi = Cập nhật `exam_submissions` + Lưu 28 dòng `exam_submission_answers` + Đẩy câu sai vào `user_wrong_questions`; hoặc Duyệt tài liệu = Đổi trạng thái `shared_documents` + Ghi sổ cái `contributor_points_history` + Cộng điểm vào `users`) **bắt buộc phải gói trong một khối Transaction duy nhất**. Nếu 1 bước lỗi, toàn bộ phải `rollback()` để không bao giờ sinh ra dữ liệu rác dở dang!

---

## PHẦN V. CẨM NANG SỬ DỤNG AI (CHATGPT / CLAUDE / CURSOR) AN TOÀN & HIỆU QUẢ

Nhóm khuyến khích sử dụng AI để tăng tốc độ lập trình, nhưng **bạn là kỹ sư làm chủ sản phẩm, không phải người copy-paste mù quáng**. Hãy khắc cốt ghi tâm 2 nhóm lưu ý sống còn sau:

### 1. Lưu ý về Bảo mật khi dùng AI (Security)
* **Rà quét Secret và API Key:** AI thường có thói quen sinh ra mã cứng (hardcode) các khóa API, mật khẩu DB, JWT Secret trực tiếp trong file `.py` hoặc `.js`. **Tuyệt đối không bao giờ commit password hay khóa bí mật thật vào code!** Mọi cấu hình nhạy cảm phải đọc từ biến môi trường (`settings.SECRET_KEY`, `import.meta.env`). Luôn kiểm tra kỹ trước khi `git push`.
* **Kiểm soát chặt Authentication & Authorization (RLS):** AI rất hay bỏ quên hoặc viết lỏng lẻo các dependency kiểm tra quyền. Sau khi AI sinh code xong, bạn phải tự hỏi và kiểm tra ngay: *"Người dùng thường (Student) có gọi nhầm vào API của Admin được không? Học sinh A đổi ID trên thanh địa chỉ URL có sửa hoặc xem trộm được dữ liệu của Học sinh B không?"*
* **Lọc và xác thực dữ liệu đầu vào (Input Validation):** Luôn yêu cầu AI dùng Pydantic v2 Schema kết hợp hàm khử khuẩn `nh3` / `Bleach` để làm sạch dữ liệu người dùng nhập vào, triệt tiêu hoàn toàn SQL Injection và XSS.
* **Áp dụng Rate Limiting:** Luôn nhắc AI gắn decorator/dependency Rate Limit cho các API quan trọng (đăng nhập, quên mật khẩu, nộp bài, tải file, đăng bài).
* **Không đưa dữ liệu nhạy cảm vào Prompt:** Tuyệt đối không dán (paste) mật khẩu thật, khóa bí mật máy chủ hoặc dữ liệu cá nhân thật của người dùng lên các công cụ AI công khai.

### 2. Lưu ý về Hiệu năng Web & Chất lượng Code khi dùng AI (Performance)
* **Ép AI tuân thủ ràng buộc kỹ thuật ngay từ câu lệnh đầu tiên:** Đừng viết prompt mơ hồ kiểu *"Làm cho tôi trang ngân hàng câu hỏi"*. Hãy đưa ra ràng buộc rõ ràng: *"Sử dụng FastAPI Async, SQLAlchemy 2.0 `Mapped`/`mapped_column`, bắt buộc có phân trang (Pagination `skip`, `limit`), không dùng vòng lặp truy vấn N+1, ở Vue 3 dùng `<script setup>` và Lazy Loading"*.
* **Kiểm soát "Context Rot" (Thối rữa ngữ cảnh) và độ phình của mã:** Khi bạn chat quá dài với AI trong cùng một cuộc hội thoại, AI sẽ bắt đầu "quên" quy tắc đầu, viết đè lên logic cũ, hoặc sinh ra các đoạn code thừa thãi, trùng lặp hàm. **Cách xử lý:** Mỗi khi làm xong 1 tính năng nhỏ, hãy mở một cuộc hội thoại (New Chat) mới, chỉ đính kèm đúng các file liên quan đến tính năng tiếp theo để ngữ cảnh luôn sạch và gọn.
* **Review kỹ `git diff` trước khi Commit/Merge (Cấm "Munch-code"):** Tuyệt đối không bấm "Accept All" hoặc copy-paste toàn bộ code của AI mà không đọc hiểu từng dòng. Hãy luôn mở phần **Changes (Diff)** trên VS Code để đọc lại từng thay đổi, xóa bỏ các đoạn code thừa, các vòng lặp vô nghĩa hoặc các thư viện nặng không cần thiết mà AI tự ý thêm vào.
* **Kiểm tra hiệu năng từ phía "Hộp đen" (Black-box Testing):** Trước khi bàn giao tính năng, hãy mở DevTools (F12 $\rightarrow$ tab Network & Lighthouse) để đo tốc độ tải trang, kiểm tra xem API phản hồi mất bao nhiêu mili-giây, có gọi lặp API liên tục hay làm đơ trình duyệt không.

---

## PHẦN VI. YÊU CẦU PHI CHỨC NĂNG (NON-FUNCTIONAL REQUIREMENTS - NFRs)

Toàn bộ các tính năng khi triển khai trong dự án bắt buộc phải đáp ứng đầy đủ **8 nhóm Yêu cầu Phi chức năng (NFR)** dưới đây:

### 1. Hiệu Suất (Performance)
Hệ thống phải đảm bảo độ trễ thấp và khả năng chịu tải tức thời trong các khung giờ cao điểm (kỳ thi thử tập trung, đợt ôn thi tốt nghiệp THPT).
* **Thời gian phản hồi API (Response Time):**
  * **Truy vấn đọc (Read Operations** – Tra cứu thuật ngữ, xem danh sách bài, lấy đề thi): Độ trễ $p95 < 150\text{ ms}$, $p99 < 300\text{ ms}$.
  * **Tra cứu nhanh cú pháp & Cheatsheet:** Độ trễ $< 50\text{ ms}$ khi gọi qua mạng và $0\text{ ms}$ đối với các dữ liệu đã đệm trên Client (Pinia Store).
  * **Giao dịch ghi (Write Operations** – Nộp bài thi, lưu tiến trình SM-2, đăng bài thảo luận): Độ trễ $p95 < 400\text{ ms}$.
  * **Tải trang đầu (First Contentful Paint - FCP):** $< 1.2\text{ giây}$; Thời gian tương tác hoàn chỉnh (**Time to Interactive - TTI**) $< 2.0\text{ giây}$ trên đường truyền mạng tiêu chuẩn (4G/Băng thông rộng).
* **Năng lực xử lý (Throughput & Concurrency):**
  * Hỗ trợ tối thiểu **$5,000$ người dùng hoạt động đồng thời (Concurrent Users - CCU)** trong các phiên thi thử trực tuyến mà không suy giảm hiệu năng.
  * Thông lượng xử lý của cụm máy chủ Backend đạt tối thiểu **$2,000\text{ yêu cầu/giây}$ (Requests Per Second - RPS)** ở chế độ tải đỉnh (Peak Load).
* **Hiệu suất xử lý tệp tin (File Processing):**
  * Tạo liên kết tải về an toàn (Signed URL) trong vòng $< 100\text{ ms}$.
  * Tiến trình ngầm phân tích tệp tài liệu Word (`.docx`) hoặc PDF (`.pdf`) dung lượng $10\text{ MB}$ hoàn tất trong vòng $< 5\text{ giây}$.

#### 1.1. Kiến Trúc Đảm Bảo Hiệu Suất
* **Tầng ứng dụng bất đồng bộ (Asynchronous FastAPI Pipeline):**
  * $100\%$ các endpoint xử lý I/O được xây dựng bằng cú pháp bất đồng bộ (`async/await`), sử dụng `uvloop` và giao tiếp với cơ sở dữ liệu qua **SQLAlchemy 2.0 Async**.
  * Tuyệt đối không chặn luồng chính (**No Blocking I/O**); các tác vụ nặng (tạo thumbnail, quét virus, tính toán lịch ôn SM-2 diện rộng) được chuyển giao hoàn toàn cho hàng đợi tác vụ ngầm (**Celery / BackgroundTasks**) xử lý tách biệt.
* **Chiến lược Bộ nhớ đệm Đa tầng (Multi-Layer Caching):**
  * **Client Cache (Vue.js / Pinia / LocalStorage):** Tải trước (Pre-fetch) toàn bộ từ điển cú pháp Python, SQL, HTML/CSS và danh mục môn học về bộ nhớ trình duyệt, giảm $70\%$ số lượng request đọc lặp lại.
  * **Application Cache (Redis Server):** Lưu trữ kết quả tra cứu thuật ngữ phổ biến, cấu trúc các bộ đề thi đang mở, và vé tải tài liệu an toàn. Cơ chế vô hiệu hóa bộ đệm (**Cache Invalidation**) tự động kích hoạt ngay khi giáo viên hoặc kiểm duyệt viên cập nhật dữ liệu mới.
* **Tối ưu hóa Cơ sở dữ liệu (Database Optimization):**
  * Sử dụng cơ chế cô lập giao dịch chống khóa đọc chặn ghi (**Lock Contention**) giữa học sinh làm bài và hệ thống ghi log.
  * Xây dựng hệ thống chỉ mục phức hợp (Composite Indexes) và chỉ mục trên các cột trạng thái phổ biến (`status = 'Published'`, `is_resolved = 1`).
  * Sử dụng các cột tính toán/sinh tự động có chỉ mục (Generated / Computed Columns) đối với các trường trích xuất từ dữ liệu bán cấu trúc JSON để tăng tốc độ truy vấn.
* **Tối ưu hóa Giao diện (Frontend Optimization):**
  * Áp dụng **Code Splitting** và **Lazy Loading** theo từng tuyến đường (Route-level code splitting) thông qua Vite.
  * Sử dụng kỹ thuật **Virtual Scrolling** đối với danh sách câu hỏi lớn và bảng thuật ngữ dài trên $500$ mục nhằm giảm tải DOM cho trình duyệt.

---

### 2. Bảo Mật (Security)
Hệ thống bảo vệ toàn vẹn dữ liệu học tập, ngăn ngừa gian lận thi cử và phòng chống các cuộc tấn công mạng theo chuẩn **OWASP Top 10**.
* **Xác thực & Phân quyền (Authentication & Authorization):**
  * Cơ chế xác thực phi trạng thái (Stateless) bằng **JWT Access Token** (thời hạn sống $15 - 30\text{ phút}$) và **Refresh Token** (thời hạn $7\text{ ngày}$, lưu trữ trong `HttpOnly`, `Secure`, `SameSite=Strict` Cookie kết hợp cơ chế Refresh Token Rotation chống đánh cắp qua mã độc XSS).
  * Kiểm soát truy cập dựa trên vai trò phân tầng (**RBAC**): `Guest`, `Student`, `Contributor`, `Reviewer`, `Instructor`, `Admin` kết hợp **Row-Level Security (RLS)**. Mọi API nghiệp vụ đều có tầng bảo vệ kiểm tra quyền hạn trước khi thực thi.
* **Mã hóa Dữ liệu (Data Encryption):**
  * **Dữ liệu truyền tải (In-Transit):** Bắt buộc $100\%$ kết nối qua giao thức HTTPS sử dụng TLS 1.3; cấu hình HSTS (HTTP Strict Transport Security) với thời hạn tối thiểu $1\text{ năm}$.
  * **Dữ liệu lưu trữ (At-Rest):** Mã hóa dữ liệu lưu trữ trên đĩa. Các thông tin nhạy cảm (mật khẩu) được băm bằng thuật toán **Argon2id** hoặc **BCrypt** với chi phí tính toán (Work Factor $\ge 12$) an toàn; mã OTP được băm bằng **HMAC-SHA256** kèm Server Pepper.
* **Toàn vẹn Tệp tin & Chống Tải Mã độc:**
  * Mọi tệp tài liệu do cộng đồng tải lên bắt buộc kiểm tra chữ ký byte thực tế (**Magic Bytes**) qua thư viện `puremagic`.
  * Tách biệt thư mục lưu trữ, tước hoàn toàn quyền thực thi mã lệnh (`no-exec`) và đổi tên tệp thành chuỗi ngẫu nhiên **UUID v4**.

#### 2.1. Kiến Trúc Bảo Mật Theo Chiều Sâu (Defence in Depth - 5 Lớp Phòng Thủ)
1. **Lớp 1 – Vành đai Mạng (Perimeter Layer):** Tích hợp WAF và lá chắn chống DDoS. Cài đặt Rate Limiting theo địa chỉ IP: tối đa $120\text{ yêu cầu/phút}$ cho các API công khai; tối đa $5\text{ yêu cầu/phút}$ đối với API đăng nhập và tải tệp lên.
2. **Lớp 2 – Reverse Proxy (Nginx):** Loại bỏ các tiêu đề rò rỉ phiên bản phần mềm (`Server`, `X-Powered-By`). Cấu hình nghiêm ngặt các Header bảo mật: `Content-Security-Policy (CSP)`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.
3. **Lớp 3 – Ứng dụng (Application Layer):** Khử khuẩn toàn bộ dữ liệu văn bản người dùng nhập bằng `nh3` / `Bleach`. Thẩm định cấu trúc dữ liệu JSON đầu vào bằng **Pydantic v2**.
4. **Lớp 4 – Cơ sở Dữ liệu (Database Layer):** Tài khoản ứng dụng kết nối vào CSDL tuân thủ nguyên tắc đặc quyền tối thiểu (**Least Privilege**), không sử dụng tài khoản quản trị tối cao (`root`/`sa`) trên môi trường Production. $100\%$ câu lệnh dùng truy vấn tham số hóa (**Parameterized Queries**) qua SQLAlchemy ORM để triệt tiêu lỗ hổng SQL Injection.
5. **Lớp 5 – Lưu trữ Tệp (File Storage Layer):** Không công khai đường dẫn vật lý của tệp; việc tải tệp bắt buộc thông qua liên kết có chữ ký số (**Signed URL**) hết hạn sau $15\text{ phút}$.

---

### 3. Khả Dụng & Độ Tin Cậy (Availability & Reliability)
* **Chỉ số Sẵn sàng (High Availability SLA):**
  * Cam kết thời gian hoạt động tối thiểu đạt **$99.9\%$** (tổng thời gian gián đoạn ngoài kế hoạch không vượt quá $8.76\text{ giờ}$ trong một năm).
* **Mục tiêu Sao lưu & Khôi phục Thảm họa (Disaster Recovery):**
  * **RPO (Recovery Point Objective):** Không quá $15\text{ phút}$ (mức độ mất mát dữ liệu tối đa khi có sự cố nghiêm trọng).
  * **RTO (Recovery Time Objective):** Không quá $60\text{ phút}$ (thời gian tối đa để toàn bộ hệ thống hoạt động trở lại).
* **Chiến lược Sao lưu Cơ sở Dữ liệu (Database Backup Strategy):**
  * **Full Backup:** Thực hiện tự động vào lúc `02:00` sáng mỗi ngày.
  * **Differential / Incremental Backup:** Thực hiện mỗi $6\text{ giờ}$ một lần.
  * **Transaction / Binary Log Backup:** Thực hiện định kỳ mỗi $15\text{ phút}$ một lần để đảm bảo khôi phục đến từng mốc thời gian cụ thể (**Point-in-Time Recovery**).
* **Khả năng Phục hồi Lỗi (Fault Tolerance & Graceful Degradation):**
  * **Mất kết nối Redis:** Nếu cụm Cache gặp sự cố, ứng dụng tự động chuyển hướng truy vấn trực tiếp vào CSDL chính mà không làm sập API.
  * **Mất kết nối mạng Client khi làm bài:** Ứng dụng Vue.js tự động lưu tạm phương án trả lời vào `LocalStorage`/`IndexedDB` trên thiết bị học sinh và tự động đồng bộ bù ngay khi có mạng trở lại.

---

### 4. Khả Năng Mở Rộng (Scalability)
* **Mở rộng Chiều ngang Máy chủ Ứng dụng (Horizontal Scaling):**
  * Backend FastAPI được đóng gói dưới dạng Docker Container phi trạng thái (**Stateless Containers**).
  * Cho phép tăng giảm số lượng Container (Replicas) dễ dàng phía sau Load Balancer (Nginx/HAProxy) dựa trên tải CPU (khi CPU vượt ngưỡng $70\%$).
* **Phân tách Tải Đọc/Ghi Cơ sở Dữ liệu (Database Scaling):**
  * Kiến trúc hỗ trợ cấu hình Primary-Replica: Các thao tác ghi (Nộp bài, Đăng bài) hướng về **Primary Node**; các tác vụ đọc nặng (Báo cáo thống kê, Tra cứu kho tài liệu) được điều hướng về **Read-Only Replicas**.
  * Quản lý kết nối thông qua Connection Pooling của SQLAlchemy (`QueuePool` với kích thước pool mặc định $20$, `max_overflow` $40$ kết nối/worker).
* **Phân luồng Tác vụ Nặng (Asynchronous Worker Scaling):**
  * Tách rời cụm xử lý Worker (Celery/Redis) ra khỏi cụm API chính. Khi có đột biến tài liệu tải lên cần bóc tách hoặc cần chạy thuật toán SM-2 cho hàng chục nghìn học sinh, chỉ cần tăng số lượng Worker container mà không ảnh hưởng tới tốc độ phục vụ người dùng web.

---

### 5. Khả Năng Bảo Trì (Maintainability)
* **Chuẩn hóa Mã nguồn (Coding Standards):**
  * **Backend Python:** Tuân thủ chuẩn **PEP 8**; bắt buộc sử dụng **Type Hinting** đầy đủ và kiểm tra bằng `mypy`; cấu trúc mã nguồn theo mô hình **Modular Monolith** (tách biệt rõ ràng tầng `Router`, `Service`, `Model`, `Schema`).
  * **Frontend Vue.js:** Bắt buộc sử dụng **Vue 3 `<script setup>` (Composition API)**; cấu trúc component theo nguyên tắc nguyên tử (**Atomic Design**); định dạng mã nguồn bằng **ESLint** và **Prettier**.
* **Ghi vết & Giám sát Hệ thống (Logging & Observability):**
  * Hệ thống ghi log có cấu trúc dạng JSON (**Structured Logging** qua `Loguru` hoặc `structlog`), gắn mã định danh tương quan `Correlation-ID` cho mỗi request để dễ dàng truy vết lỗi xuyên suốt từ Frontend qua Backend.
  * Phân loại mức độ log nghiêm ngặt (`INFO`, `WARNING`, `ERROR`, `CRITICAL`). Nhật ký lỗi (`ERROR`) bắt buộc chứa đầy đủ Stack Trace và tham số ngữ cảnh (loại trừ thông tin nhạy cảm/mật khẩu).
  * Tích hợp Health Check Endpoints (`/health`, `/healthz/liveness`, `/healthz/readiness`) phục vụ hệ thống điều phối container tự động phát hiện và khởi động lại dịch vụ lỗi.
* **Tự Động Hóa Triển Khai (CI/CD Pipeline):**
  * Kiểm tra tự động (Linting, Unit Testing, Security Audit) chạy tự động $100\%$ trước khi cho phép gộp mã nguồn vào nhánh chính.
  * Triển khai không gián đoạn dịch vụ (**Zero-Downtime Deployment**) thông qua chiến lược Rolling Update hoặc Blue/Green Deployment.

---

### 6. Khả Năng Sử Dụng (Usability)
* **Thiết kế Trực quan & Thân thiện Sư phạm:**
  * Giao diện tối ưu theo chuẩn Thiết kế Trải nghiệm Người dùng (UX) hiện đại, hỗ trợ chuyển đổi linh hoạt giữa giao diện Sáng (**Light Mode**) và giao diện Tối (**Dark Mode**) giúp bảo vệ mắt học sinh khi học ban đêm.
  * Tương thích hoàn hảo (**Responsive Design**) trên các kích thước màn hình máy tính bàn, máy tính xách tay và máy tính bảng (kích thước màn hình từ $768\text{px}$ trở lên).
* **Tối ưu hóa Thao tác Nhanh (Keyboard Accessibility):**
  * **Phân hệ Flashcard** hỗ trợ phím tắt chuyên nghiệp: Phím `Space` để lật thẻ 3D; phím số `1`, `2`, `3`, `4` tương ứng với 4 mức độ nhớ (*Again, Hard, Good, Easy*) giúp tăng tốc độ ôn luyện.
  * **Phân hệ Làm bài thi** hỗ trợ phím tắt chọn nhanh đáp án `A`, `B`, `C`, `D` và phím mũi tên điều hướng chuyển câu hỏi.
* **Độ Rõ Ràng của Thông Báo & Trạng Thái:**
  * $100\%$ các thao tác xử lý kéo dài trên $0.5\text{ giây}$ (tải đề, bóc tách tệp, tìm kiếm) bắt buộc hiển thị trạng thái đang tải trực quan (**Skeleton Loaders** hoặc **Progress Bar**).
  * Thông báo lỗi hiển thị bằng **tiếng Việt sư phạm rõ ràng, dễ hiểu**, chỉ rõ nguyên nhân và hướng khắc phục thay vì hiển thị mã lỗi kỹ thuật thuần túy.

---

### 7. Tuân Thủ Quy Định (Compliance)
* **Chuẩn hóa Học thuật Giáo dục (Academic Alignment):**
  * Cấu trúc ma trận câu hỏi, đề thi và thang điểm tuân thủ $100\%$ quy chế thi tốt nghiệp THPT theo Chương trình Giáo dục phổ thông (GDPT) của Bộ Giáo dục và Đào tạo:
    * **Phần I:** $24$ câu trắc nghiệm nhiều lựa chọn (thang điểm $6.0$).
    * **Phần II:** $4$ câu trắc nghiệm Đúng/Sai với $4$ khẳng định $a, b, c, d$ độc lập tính điểm lũy tiến (thang điểm $4.0$).
  * Nội dung thuật ngữ, chuyên đề và flashcard phân định rõ ràng 2 nhánh hướng nghiệp: **Tin học ứng dụng (ICT)** và **Khoa học máy tính (CS)**.
* **Bảo vệ Dữ liệu Cá nhân (Data Privacy Compliance):**
  * Tuân thủ quy định bảo vệ dữ liệu cá nhân theo **Nghị định 13/2023/NĐ-CP** của Chính phủ Việt Nam:
    * Thu thập thông tin đúng mục đích giáo dục; có cơ chế để người dùng xác nhận đồng ý (Consent) khi đăng ký tài khoản.
    * Cung cấp tính năng cho phép người dùng yêu cầu trích xuất dữ liệu học tập cá nhân hoặc yêu cầu đóng băng/xóa tài khoản khi ngừng sử dụng.
* **Sở hữu Trí tuệ & Bản quyền Tác giả:**
  * Cơ chế đóng góp tài liệu cộng đồng bắt buộc người nộp cam kết bản quyền nội dung.
  * Cung cấp quy trình tiếp nhận khiếu nại bản quyền và hạ học liệu vi phạm (**Takedown Process**) trong vòng $24\text{ giờ}$ kể từ khi nhận được phản ánh hợp lệ.

---

### 8. Chiến Lược Kiểm Thử NFR (NFR Testing Strategy)

| Hạng mục kiểm thử | Công cụ thực hiện | Kịch bản & Tiêu chí nghiệm thu | Tần suất thực hiện |
| :--- | :--- | :--- | :--- |
| **Kiểm thử Tải (Load Testing)** | `Locust` / `k6` | Mô phỏng $5,000$ người dùng ảo đồng thời làm bài thi trắc nghiệm và gửi kết quả; tỷ lệ lỗi HTTP $< 0.1\%$, thời gian phản hồi $p95 < 400\text{ ms}$. | Định kỳ trước mỗi kỳ thi lớn hoặc phiên bản phát hành chính (Release). |
| **Kiểm thử Ứng suất (Stress Testing)** | `k6` | Tăng tải vượt ngưỡng thiết kế (từ $5,000$ lên $10,000$ CCU) để xác định điểm gãy (Breaking Point); kiểm tra hệ thống có tự phục hồi (Auto-recover) khi tải giảm hay không. | $6\text{ tháng}$ một lần. |
| **Kiểm thử Bảo mật Tĩnh (SAST)** | `SonarQube` / `Bandit` | Tự động quét mã nguồn Python và Vue.js tìm kiếm các lỗ hổng tiềm ẩn, hardcoded credentials, hoặc các hàm không an toàn; bắt buộc $0$ lỗi mức Critical/High. | Tích hợp tự động trong mỗi luồng CI/CD (Pull Request). |
| **Kiểm thử Bảo mật Động (DAST)** | `OWASP ZAP` | Quét tự động toàn bộ API endpoint tìm kiếm các lỗ hổng Injection, XSS, CSRF, lỗi cấu hình Header bảo mật. | Hàng tháng trên môi trường Staging. |
| **Kiểm thử Khôi phục Thảm họa (DR Drill)** | Kịch bản diễn tập nội bộ | Giả lập tình huống máy chủ cơ sở dữ liệu chính bị ngừng hoạt động đột ngột; đo đạc thời gian khôi phục dữ liệu từ bản sao lưu gần nhất (mục tiêu $\text{RTO} < 60\text{ phút}$, $\text{RPO} < 15\text{ phút}$). | $6\text{ tháng}$ một lần. |
| **Kiểm thử Hiệu năng Giao diện** | `Google Lighthouse` | Đo đạc trải nghiệm người dùng trên các trang chính (Trang chủ, Làm đề, Flashcard); đạt điểm số $> 90\text{ điểm}$ cho cả 3 tiêu chí: Performance, Accessibility và Best Practices. | Trước mỗi đợt triển khai giao diện mới. |

---

## PHẦN VII. CHECKLIST TỰ KIỂM TRA TRƯỚC KHI TẠO PULL REQUEST (PR)

Trước khi bấm nút gửi code của bạn lên nhóm, hãy tự đánh dấu kiểm tra đủ 7 mục sau:
- [ ] **1. Đã `git pull origin main`** để cập nhật code mới nhất của nhóm chưa?
- [ ] **2. Đang đứng ở nhánh riêng (`feature/...` hoặc `fix/...`)** chứ không phải nhánh `main` đúng không?
- [ ] **3. Có để lộ mật khẩu, API Key hay file `.env`** trong các file sắp commit không?
- [ ] **4. Đã kiểm tra Row-Level Security (`user_id == current_user.id`)**, Rate Limit và ghi `audit_logs` cho các thao tác nhạy cảm chưa?
- [ ] **5. Đã khử khuẩn XSS** (dùng `sanitizer.py` ở BE và `SafeMarkdownViewer` / `CodeBlock` ở FE) chưa?
- [ ] **6. Đã đọc lại `git diff`** để xóa các đoạn `console.log`, `print()` nháp và code thừa do AI sinh ra chưa?
- [ ] **7. Đã chạy thử trên máy/Docker** và xác nhận tính năng hoạt động mượt mà chưa?