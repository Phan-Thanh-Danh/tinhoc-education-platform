# filepath: backend/app/core/seed.py
from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DocumentCategory,
    ForumCategory,
    Grade,
    Role,
    Topic,
)

logger = logging.getLogger(__name__)


async def seed_initial_data(session: AsyncSession) -> None:
    """
    Khởi tạo dữ liệu mầm (seed data) ban đầu cho hệ thống nếu CSDL chưa có:
    - 4 Vai trò (roles)
    - 3 Khối lớp THPT (grades: K10, K11, K12)
    - Các Chủ đề chuẩn GDPT 2018 (topics)
    - Các Chuyên mục diễn đàn (forum_categories)
    - Các Danh mục tài liệu (document_categories)
    """
    logger.info("Kiểm tra và nạp dữ liệu khởi tạo (Seed Data)...")

    # 1. Seed Roles
    existing_roles = await session.execute(select(Role))
    if not existing_roles.scalars().first():
        roles_data = [
            Role(name="Student", description="Học sinh tham gia học tập, ôn luyện và làm bài thi"),
            Role(name="Instructor", description="Giáo viên giảng dạy, biên soạn bài giảng và câu hỏi"),
            Role(name="Reviewer", description="Chuyên gia / Giáo viên thẩm định chất lượng học liệu và tài liệu"),
            Role(name="Admin", description="Quản trị viên toàn quyền vận hành hệ thống"),
        ]
        session.add_all(roles_data)
        logger.info("Đã tạo 4 vai trò mặc định (Student, Instructor, Reviewer, Admin)")

    # 2. Seed Grades
    existing_grades = await session.execute(select(Grade))
    grade_map = {}
    if not existing_grades.scalars().first():
        grades_data = [
            Grade(code="K10", name="Tin học Lớp 10", order_index=1),
            Grade(code="K11", name="Tin học Lớp 11", order_index=2),
            Grade(code="K12", name="Tin học Lớp 12", order_index=3),
        ]
        session.add_all(grades_data)
        await session.flush()
        for g in grades_data:
            grade_map[g.code] = g.id
        logger.info("Đã tạo 3 khối lớp mặc định (K10, K11, K12)")
    else:
        all_grades = (await session.execute(select(Grade))).scalars().all()
        for g in all_grades:
            grade_map[g.code] = g.id

    # 3. Seed Topics theo chuẩn GDPT 2018
    existing_topics = await session.execute(select(Topic))
    if not existing_topics.scalars().first() and grade_map:
        topics_data = [
            # Lớp 10
            Topic(grade_id=grade_map["K10"], code="CS_A10", name="Chủ đề A: Máy tính và xã hội tri thức", order_index=1),
            Topic(grade_id=grade_map["K10"], code="CS_B10", name="Chủ đề B: Mạng máy tính và Internet", order_index=2),
            Topic(grade_id=grade_map["K10"], code="CS_D10", name="Chủ đề D: Đạo đức, pháp luật và văn hóa số", order_index=3),
            Topic(grade_id=grade_map["K10"], code="CS_E10", name="Chủ đề E: Ứng dụng tin học (Văn phòng & Đa phương tiện)", order_index=4),
            Topic(grade_id=grade_map["K10"], code="CS_F10", name="Chủ đề F: Giải quyết vấn đề với sự trợ giúp của máy tính (Python)", order_index=5),
            Topic(grade_id=grade_map["K10"], code="CS_G10", name="Chủ đề G: Hướng nghiệp với Tin học", order_index=6),
            # Lớp 11
            Topic(grade_id=grade_map["K11"], code="CS_A11", name="Chủ đề A: Máy tính và xã hội tri thức (Hệ điều hành & Phần cứng)", order_index=1),
            Topic(grade_id=grade_map["K11"], code="CS_B11", name="Chủ đề B: Mạng máy tính và Internet", order_index=2),
            Topic(grade_id=grade_map["K11"], code="CS_D11", name="Chủ đề D: Đạo đức, pháp luật và văn hóa số", order_index=3),
            Topic(grade_id=grade_map["K11"], code="CS_F11_ICT", name="Chủ đề F (ICT): Hệ quản trị CSDL & SQL", order_index=4),
            Topic(grade_id=grade_map["K11"], code="CS_F11_CS", name="Chủ đề F (CS): Kỹ thuật lập trình & Thuật toán", order_index=5),
            # Lớp 12
            Topic(grade_id=grade_map["K12"], code="CS_A12", name="Chủ đề A: Trí tuệ nhân tạo (AI) và xã hội số", order_index=1),
            Topic(grade_id=grade_map["K12"], code="CS_B12", name="Chủ đề B: Mạng máy tính & Giao thức truyền thông", order_index=2),
            Topic(grade_id=grade_map["K12"], code="CS_D12", name="Chủ đề D: Đạo đức, pháp luật và văn hóa số trong môi trường mạng", order_index=3),
            Topic(grade_id=grade_map["K12"], code="CS_F12_ICT", name="Chủ đề F (ICT): Thiết kế Web & HTML/CSS/JS", order_index=4),
            Topic(grade_id=grade_map["K12"], code="CS_F12_CS", name="Chủ đề F (CS): Cấu trúc dữ liệu & Thuật toán nâng cao", order_index=5),
        ]
        session.add_all(topics_data)
        logger.info("Đã tạo danh mục chủ đề GDPT 2018 cho các khối 10, 11, 12")

    # 4. Seed Forum Categories
    existing_forum_cats = await session.execute(select(ForumCategory))
    if not existing_forum_cats.scalars().first():
        forum_cats = [
            ForumCategory(code="CHUNG", name="Thảo luận chung Tin học GDPT", description="Diễn đàn trao đổi học tập và phương pháp ôn luyện", order_index=1),
            ForumCategory(code="THUAT_TOAN", name="Lập trình & Thuật toán", description="Thảo luận code Python, C++, Pascal và bài toán thuật toán", order_index=2),
            ForumCategory(code="CSDL_WEB", name="Cơ sở dữ liệu & Thiết kế Web", description="Hỏi đáp về SQL, Access, HTML, CSS và JavaScript", order_index=3),
            ForumCategory(code="MANG_AN_NINH", name="Mạng máy tính & An toàn số", description="Kiến thức mạng máy tính, giao thức và an toàn thông tin", order_index=4),
            ForumCategory(code="HOI_DAP_DE_THI", name="Hỏi đáp đề thi & Khảo thí", description="Giải đáp các câu hỏi trong đề thi thử và đề thi tốt nghiệp", order_index=5),
        ]
        session.add_all(forum_cats)
        logger.info("Đã tạo 5 chuyên mục diễn đàn hỏi đáp")

    # 5. Seed Document Categories
    existing_doc_cats = await session.execute(select(DocumentCategory))
    if not existing_doc_cats.scalars().first():
        doc_cats = [
            DocumentCategory(code="GIAO_AN", name="Giáo án & Kế hoạch bài dạy", description="Kế hoạch bài dạy (KHBD) theo Công văn 5512", order_index=1),
            DocumentCategory(code="DE_THI", name="Đề thi & Đề kiểm tra", description="Đề kiểm tra định kỳ, đề thi thử có ma trận và bản đặc tả", order_index=2),
            DocumentCategory(code="CHUYEN_DE", name="Tài liệu chuyên đề ôn tập", description="Tài liệu chuyên đề bồi dưỡng và củng cố kiến thức", order_index=3),
            DocumentCategory(code="MA_NGUON", name="Phần mềm & Mã nguồn mẫu", description="Code mẫu thực hành và ứng dụng mẫu cho học sinh", order_index=4),
        ]
        session.add_all(doc_cats)
        logger.info("Đã tạo 4 danh mục tài liệu chia sẻ")

    await session.commit()
    logger.info("Đồng bộ toàn bộ dữ liệu khởi tạo thành công!")

