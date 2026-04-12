#!/usr/bin/env python3
"""
seed_hs_codes.py — Seed 50 mã HS XNK phổ biến Việt Nam – Trung Quốc.

Bao gồm: điện tử, dệt may, máy móc, hóa chất, nông sản, sắt thép,
         nhựa, ô tô phụ tùng, đồ gỗ, thiết bị y tế.

Usage:
    python3 scripts/seed_hs_codes.py
"""

import os
import sys
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
DATABASE_URL = os.environ.get("DATABASE_URL", "")


# ── Chapter data ─────────────────────────────────────────────────────────────
CHAPTERS = [
    ("08", "Quả và quả hạch ăn được; vỏ quả thuộc họ cam quýt hoặc các loại dưa"),
    ("10", "Ngũ cốc"),
    ("28", "Hóa chất vô cơ; các hợp chất vô cơ hoặc hữu cơ của kim loại quý"),
    ("29", "Hóa chất hữu cơ"),
    ("39", "Plastic và các sản phẩm bằng plastic"),
    ("40", "Cao su và các sản phẩm bằng cao su"),
    ("44", "Gỗ và các mặt hàng bằng gỗ; than củi"),
    ("52", "Bông"),
    ("54", "Sợi filament nhân tạo; dải và các dạng tương tự bằng vật liệu dệt nhân tạo"),
    ("61", "Quần áo và hàng may mặc phụ trợ, dệt kim hoặc móc"),
    ("62", "Quần áo và hàng may mặc phụ trợ, không dệt kim hoặc móc"),
    ("64", "Giày, dép, ghệt và các sản phẩm tương tự; các bộ phận của các sản phẩm trên"),
    ("72", "Sắt và thép"),
    ("73", "Các sản phẩm bằng sắt hoặc thép"),
    ("76", "Nhôm và các sản phẩm bằng nhôm"),
    ("84", "Lò phản ứng hạt nhân, nồi hơi, máy, thiết bị cơ khí"),
    ("85", "Máy điện và thiết bị điện và các bộ phận của chúng"),
    ("87", "Xe cộ trừ xe chạy trên đường ray, và các bộ phận, phụ tùng của chúng"),
    ("90", "Dụng cụ, thiết bị quang học, đo lường, kiểm tra, chính xác, y tế"),
    ("94", "Đồ nội thất; bộ đồ giường, đệm; thiết bị chiếu sáng"),
]

# ── HS Codes: 50 mã phổ biến nhất trong thương mại VN–TQ ─────────────────────
# Format: (code, chapter_code, description_vi, description_en, unit,
#           tax_normal, tax_preferential, tax_special, notes)
HS_CODES = [
    # ── ĐIỆN TỬ & LINH KIỆN (Chapter 85) ────────────────────────────────────
    (
        "8517.12.00", "85",
        "Điện thoại di động (smartphone)",
        "Mobile phones (smartphones)",
        "chiếc", 0.00, 0.00, None,
        "Nhập khẩu phổ biến từ TQ. Thuế MFN 0%, ACFTA 0%."
    ),
    (
        "8528.72.40", "85",
        "Màn hình LCD/LED dùng cho máy tính",
        "LCD/LED monitors for computers",
        "chiếc", 0.00, 0.00, None,
        "Phổ biến trong nhập khẩu linh kiện điện tử từ TQ."
    ),
    (
        "8542.31.00", "85",
        "Mạch tích hợp điện tử (chip vi xử lý)",
        "Electronic integrated circuits - processors",
        "chiếc", 0.00, 0.00, None,
        "Chip bán dẫn, vi xử lý. Thuế 0%."
    ),
    (
        "8544.42.91", "85",
        "Dây điện, cáp điện bọc nhựa (điện áp ≤ 1000V)",
        "Electric wires/cables, insulated (≤1000V)",
        "mét/kg", 8.00, 0.00, None,
        "Cáp điện nhập từ TQ. ACFTA 0% khi có C/O Form E."
    ),
    (
        "8504.40.40", "85",
        "Bộ chuyển đổi điện (bộ nguồn, adapter)",
        "Power converters / adapters",
        "chiếc", 0.00, 0.00, None,
        "Adapter sạc, bộ nguồn máy tính."
    ),
    (
        "8506.10.00", "85",
        "Pin Mangan dioxide (pin carbon)",
        "Manganese dioxide primary cells and batteries",
        "chiếc", 20.00, 5.00, None,
        "Pin AA, AAA nhập từ TQ. Thuế ACFTA 5%."
    ),
    (
        "8507.60.00", "85",
        "Bộ ắc quy Lithium-ion",
        "Lithium-ion accumulators",
        "chiếc", 0.00, 0.00, None,
        "Pin Li-ion cho xe điện, laptop. Thuế 0%."
    ),
    (
        "8471.30.00", "85",
        "Máy tính xách tay (laptop)",
        "Portable automatic data processing machines (laptops)",
        "chiếc", 0.00, 0.00, None,
        "Laptop nhập TQ. Thuế 0%, không cần C/O."
    ),
    (
        "8443.32.29", "85",
        "Máy in phun hoặc laser dùng cho văn phòng",
        "Inkjet or laser printers for office use",
        "chiếc", 0.00, 0.00, None,
        "Máy in văn phòng."
    ),
    (
        "8536.50.19", "85",
        "Công tắc điện, cầu dao (điện áp ≤ 1000V)",
        "Electrical switches for < 1000V",
        "chiếc", 8.00, 0.00, None,
        "Vật liệu điện nhập TQ. ACFTA 0%."
    ),

    # ── MÁY MÓC & THIẾT BỊ (Chapter 84) ─────────────────────────────────────
    (
        "8471.41.00", "84",
        "Máy tính để bàn (desktop computer)",
        "Desktop computers",
        "chiếc", 0.00, 0.00, None,
        "Máy tính bàn nhập TQ. Thuế 0%."
    ),
    (
        "8479.89.99", "84",
        "Máy móc công nghiệp chuyên dụng khác",
        "Other industrial machinery and equipment",
        "chiếc", 0.00, 0.00, None,
        "Máy chuyên dụng. Cần kiểm tra chuyên ngành tùy loại."
    ),
    (
        "8413.70.90", "84",
        "Bơm chất lỏng các loại (bơm nước, bơm dầu)",
        "Pumps for liquids (water pumps, oil pumps)",
        "chiếc", 0.00, 0.00, None,
        "Bơm nước nhập TQ phổ biến."
    ),
    (
        "8418.10.00", "84",
        "Tủ lạnh gia đình (kết hợp tủ đông)",
        "Combined refrigerator-freezers, household type",
        "chiếc", 25.00, 20.00, None,
        "Điện gia dụng nhập TQ."
    ),
    (
        "8450.11.00", "84",
        "Máy giặt gia đình (≤ 10kg)",
        "Household washing machines (capacity ≤10kg)",
        "chiếc", 25.00, 20.00, None,
        "Máy giặt nhập TQ."
    ),

    # ── SẮT THÉP (Chapter 72) ─────────────────────────────────────────────────
    (
        "7208.51.00", "72",
        "Thép cuộn cán nóng (HRC) không hợp kim, chiều rộng ≥ 600mm",
        "Hot-rolled flat steel, non-alloy, width ≥600mm",
        "tấn", 0.00, 0.00, None,
        "Thép cuộn nhập TQ. Có thể bị áp thuế tự vệ."
    ),
    (
        "7210.49.11", "72",
        "Thép mạ kẽm nhúng nóng (tôn mạ kẽm)",
        "Hot-dip galvanized steel sheets",
        "tấn", 0.00, 0.00, None,
        "Tôn mạ kẽm phổ biến trong xây dựng."
    ),
    (
        "7213.10.00", "72",
        "Thép thanh vằn, dây thép cuộn (xây dựng)",
        "Bars and rods, hot-rolled, with indentations (rebar)",
        "tấn", 0.00, 0.00, None,
        "Thép xây dựng nhập TQ. Kiểm tra chất lượng bắt buộc."
    ),
    (
        "7217.10.10", "72",
        "Dây thép không mạ (đường kính < 0.8mm)",
        "Wire of iron/non-alloy steel, not plated, diameter < 0.8mm",
        "tấn", 5.00, 0.00, None,
        "Dây thép cuộn nhập TQ."
    ),
    (
        "7304.31.20", "73",
        "Ống thép không hàn, mặt cắt tròn (phi < 168.3mm)",
        "Seamless steel pipes/tubes, circular cross-section, OD < 168.3mm",
        "tấn", 0.00, 0.00, None,
        "Ống thép không hàn nhập TQ."
    ),

    # ── NHỰA & CAO SU (Chapter 39, 40) ───────────────────────────────────────
    (
        "3901.20.00", "39",
        "Polyethylene (PE) tỉ trọng ≥ 0.94 (dạng hạt nguyên liệu)",
        "Polyethylene with density ≥0.94 (HDPE pellets)",
        "tấn", 3.00, 0.00, None,
        "Hạt nhựa HDPE nhập TQ làm nguyên liệu."
    ),
    (
        "3902.10.00", "39",
        "Polypropylene (PP) dạng hạt nguyên liệu",
        "Polypropylene (PP pellets)",
        "tấn", 3.00, 0.00, None,
        "Hạt nhựa PP nhập TQ."
    ),
    (
        "3920.20.10", "39",
        "Tấm, màng nhựa PP (dùng in bao bì)",
        "Plates, sheets, film of polypropylene (for packaging)",
        "kg", 8.00, 0.00, None,
        "Màng nhựa PP nhập TQ."
    ),
    (
        "4011.10.10", "40",
        "Lốp xe ô tô mới (kích cỡ phổ thông)",
        "New pneumatic tyres for passenger cars",
        "chiếc", 0.00, 0.00, None,
        "Lốp xe TQ. Cần kiểm tra hợp quy QCVN."
    ),
    (
        "4016.10.00", "40",
        "Sản phẩm cao su lưu hóa xốp (gioăng, đệm, con lăn)",
        "Cellular vulcanised rubber products (seals, gaskets)",
        "kg", 10.00, 0.00, None,
        "Linh kiện cao su nhập TQ."
    ),

    # ── DỆT MAY & GIÀY DÉP (Chapter 61, 62, 64) ──────────────────────────────
    (
        "6109.10.00", "61",
        "Áo phông cotton dệt kim (T-shirt)",
        "T-shirts, singlets of cotton, knitted",
        "chiếc/kg", 12.00, 12.00, None,
        "Hàng dệt may nhập TQ. Có quota theo FTA."
    ),
    (
        "6203.42.00", "62",
        "Quần dài nam cotton (không dệt kim)",
        "Men's cotton trousers, woven",
        "chiếc", 12.00, 12.00, None,
        "Quần nam nhập TQ."
    ),
    (
        "6204.62.00", "62",
        "Quần dài nữ cotton (không dệt kim)",
        "Women's cotton trousers, woven",
        "chiếc", 12.00, 12.00, None,
        "Quần nữ nhập TQ."
    ),
    (
        "6402.99.90", "64",
        "Giày thể thao đế cao su/nhựa, mũ giày vật liệu khác",
        "Sports footwear, rubber/plastic sole, other upper material",
        "đôi", 30.00, 20.00, None,
        "Giày dép nhập TQ. Thuế cao, phổ biến nhập tiểu ngạch."
    ),
    (
        "5402.47.00", "54",
        "Sợi polyester tổng hợp (sợi xe, không đặt cách)",
        "Polyester yarn, multiple/cabled, not textured",
        "kg", 12.00, 0.00, None,
        "Sợi dệt nhập TQ làm nguyên liệu may mặc."
    ),

    # ── GỖ & NỘI THẤT (Chapter 44, 94) ───────────────────────────────────────
    (
        "4412.39.00", "44",
        "Gỗ dán (plywood) từ gỗ nhiệt đới khác",
        "Plywood of other tropical wood species",
        "m3", 25.00, 20.00, None,
        "Gỗ dán nhập TQ. Cần kiểm tra nguồn gốc gỗ hợp pháp (FLEGT)."
    ),
    (
        "9403.20.00", "94",
        "Đồ nội thất bằng kim loại (giường sắt, bàn ghế văn phòng)",
        "Other metal furniture (beds, office tables/chairs)",
        "chiếc", 25.00, 20.00, None,
        "Bàn ghế, giường sắt nhập TQ."
    ),
    (
        "9403.60.00", "94",
        "Đồ nội thất bằng gỗ khác (tủ, kệ, bàn gỗ)",
        "Other wooden furniture (wardrobes, shelves, tables)",
        "chiếc", 25.00, 20.00, None,
        "Nội thất gỗ nhập TQ."
    ),

    # ── NHÔM (Chapter 76) ─────────────────────────────────────────────────────
    (
        "7601.20.00", "76",
        "Hợp kim nhôm dạng thỏi, phôi (nguyên liệu)",
        "Aluminium alloys, unwrought",
        "tấn", 0.00, 0.00, None,
        "Nhôm nguyên liệu nhập TQ."
    ),
    (
        "7604.29.90", "76",
        "Thanh, que nhôm hợp kim (thanh định hình nhôm)",
        "Aluminium alloy bars, rods, profiles",
        "tấn/kg", 10.00, 0.00, None,
        "Thanh nhôm định hình cho cửa nhôm, kết cấu."
    ),
    (
        "7610.10.00", "76",
        "Cửa sổ, cửa ra vào bằng nhôm và khung",
        "Aluminium doors, windows and their frames",
        "bộ/m2", 27.00, 22.00, None,
        "Cửa nhôm nhập TQ. Kiểm tra quy chuẩn xây dựng."
    ),

    # ── HÓA CHẤT (Chapter 28, 29) ─────────────────────────────────────────────
    (
        "2814.10.00", "28",
        "Amoniac khan (dùng trong phân bón, lạnh công nghiệp)",
        "Anhydrous ammonia",
        "tấn", 0.00, 0.00, None,
        "Hóa chất công nghiệp. Kiểm soát theo quy định hóa chất nguy hiểm."
    ),
    (
        "2917.32.00", "29",
        "Dioctyl orthophthalate (DOP) — chất hóa dẻo nhựa PVC",
        "Dioctyl orthophthalate (DOP plasticizer)",
        "tấn", 3.00, 0.00, None,
        "Chất phụ gia nhựa nhập TQ."
    ),
    (
        "2933.61.00", "29",
        "Melamine (nguyên liệu sản xuất ván ép, sơn, nhựa)",
        "Melamine (raw material for laminates, paints)",
        "tấn", 3.00, 0.00, None,
        "Melamine nhập TQ."
    ),

    # ── XE & PHỤ TÙNG (Chapter 87) ───────────────────────────────────────────
    (
        "8703.23.59", "87",
        "Xe ô tô con động cơ xăng 1500-2000cc (nhập nguyên chiếc CBU)",
        "Passenger cars, spark-ignition, 1500-2000cc",
        "chiếc", 64.00, 47.00, None,
        "Ô tô nhập khẩu TQ. Thuế cao, cần kiểm tra khí thải Euro."
    ),
    (
        "8708.29.90", "87",
        "Phụ tùng, linh kiện ô tô khác (thân xe, khung xe)",
        "Other parts for motor vehicles (body, chassis parts)",
        "chiếc/kg", 15.00, 0.00, None,
        "Phụ tùng ô tô nhập TQ."
    ),
    (
        "8714.91.00", "87",
        "Khung xe đạp (bao gồm xe đạp điện)",
        "Bicycle frames (including e-bike frames)",
        "chiếc", 25.00, 10.00, None,
        "Khung xe đạp điện nhập TQ, phổ biến."
    ),

    # ── THIẾT BỊ Y TẾ (Chapter 90) ────────────────────────────────────────────
    (
        "9018.90.90", "90",
        "Dụng cụ y tế khác (kim tiêm, ống nghiệm, bơm tiêm)",
        "Other medical instruments (syringes, tubes, needles)",
        "chiếc/hộp", 0.00, 0.00, None,
        "Vật tư y tế nhập TQ. Cần số lưu hành thiết bị y tế."
    ),
    (
        "9019.10.00", "90",
        "Thiết bị vật lý trị liệu (máy massage, thiết bị thở)",
        "Mechano-therapy/massage/respiration apparatus",
        "chiếc", 0.00, 0.00, None,
        "Thiết bị y tế nhập TQ."
    ),

    # ── NÔNG SẢN (Chapter 8, 10) ──────────────────────────────────────────────
    (
        "0805.10.00", "08",
        "Cam tươi hoặc khô",
        "Fresh or dried oranges",
        "tấn/kg", 10.00, 0.00, None,
        "Trái cây nhập TQ. Kiểm dịch thực vật bắt buộc."
    ),
    (
        "0806.10.00", "08",
        "Nho tươi",
        "Fresh grapes",
        "tấn/kg", 10.00, 0.00, None,
        "Nho TQ nhập phổ biến. Kiểm dịch thực vật."
    ),
    (
        "1006.30.00", "10",
        "Gạo xay (rice, semi-milled or wholly milled)",
        "Rice, semi-milled or wholly milled",
        "tấn", 0.00, 0.00, None,
        "Gạo TQ ít xuất hiện nhưng có nhập một số loại đặc sản."
    ),

    # ── HÀNG TIÊU DÙNG PHỔ BIẾN ─────────────────────────────────────────────
    (
        "9506.62.00", "94",
        "Bóng bơm hơi (bóng đá, bóng rổ, bóng chuyền)",
        "Inflatable balls (footballs, basketballs, volleyballs)",
        "chiếc", 20.00, 10.00, None,
        "Dụng cụ thể thao nhập TQ."
    ),
    (
        "3923.30.00", "39",
        "Bình, lọ, hộp nhựa (đồ đựng bằng nhựa)",
        "Carboys, bottles, flasks of plastic for goods",
        "kg/chiếc", 10.00, 0.00, None,
        "Bao bì nhựa nhập TQ."
    ),
]


def seed_chapters(cur) -> int:
    inserted = 0
    for code, title_vi in CHAPTERS:
        cur.execute(
            """
            INSERT INTO hs_chapters (chapter_code, title_vi)
            VALUES (%s, %s)
            ON CONFLICT (chapter_code) DO UPDATE SET title_vi = EXCLUDED.title_vi
            """,
            (code, title_vi)
        )
        inserted += 1
    return inserted


def seed_hs_codes(cur) -> int:
    inserted = updated = 0
    for row in HS_CODES:
        (code, chapter_code, desc_vi, desc_en, unit,
         tax_normal, tax_pref, tax_special, notes) = row

        cur.execute(
            """
            INSERT INTO hs_codes
                (code, chapter_code, description_vi, description_en,
                 unit, tax_rate_normal, tax_rate_preferential, tax_rate_special, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
                description_vi          = EXCLUDED.description_vi,
                description_en          = EXCLUDED.description_en,
                unit                    = EXCLUDED.unit,
                tax_rate_normal         = EXCLUDED.tax_rate_normal,
                tax_rate_preferential   = EXCLUDED.tax_rate_preferential,
                tax_rate_special        = EXCLUDED.tax_rate_special,
                notes                   = EXCLUDED.notes,
                updated_at              = NOW()
            """,
            (code, chapter_code, desc_vi, desc_en, unit,
             tax_normal, tax_pref, tax_special, notes)
        )
        inserted += 1

    return inserted


def verify(cur) -> dict:
    cur.execute("SELECT COUNT(*) FROM hs_codes")
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT chapter_code, COUNT(*) as cnt
        FROM hs_codes GROUP BY chapter_code ORDER BY cnt DESC LIMIT 5
    """)
    top_chapters = cur.fetchall()

    # Test pg_trgm search
    cur.execute("SELECT * FROM search_hs_codes('điện thoại', 5, 0.1)")
    search_results = cur.fetchall()

    return {
        "total": total,
        "top_chapters": top_chapters,
        "search_test": [r[1] for r in search_results],  # code column
    }


def main():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)

    print("XNK Webapp — T03 Seed HS Codes")
    print(f"DB: {DATABASE_URL.split('@')[1]}")
    print(f"Total to seed: {len(HS_CODES)} HS codes, {len(CHAPTERS)} chapters\n")

    conn = psycopg2.connect(DATABASE_URL, connect_timeout=15)
    conn.autocommit = True
    cur = conn.cursor()

    # Seed chapters
    print("Seeding chapters...")
    n_chapters = seed_chapters(cur)
    print(f"  ✓ {n_chapters} chapters inserted/updated")

    # Seed HS codes
    print("\nSeeding HS codes...")
    n_codes = seed_hs_codes(cur)
    print(f"  ✓ {n_codes} HS codes inserted/updated")

    # Verify
    print("\nVerifying...")
    stats = verify(cur)
    print(f"  Total hs_codes in DB: {stats['total']}")
    print(f"  Top chapters: {stats['top_chapters']}")
    print(f"  pg_trgm test search('điện thoại'): {stats['search_test']}")

    cur.close()
    conn.close()

    if stats["total"] >= 50:
        print(f"\n✓ T03 COMPLETED — {stats['total']} HS codes seeded, pg_trgm working")
        sys.exit(0)
    else:
        print(f"\n✗ Expected ≥50 rows, got {stats['total']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
