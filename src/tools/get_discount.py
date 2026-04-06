# Chuong trinh khuyen mai cua hang
PROMOTIONS = {
    "HSSV2026": {
        "name": "Khuyen mai Hoc sinh - Sinh vien 2026",
        "discount_percent": 5,
        "description": "Giam 5% cho hoc sinh sinh vien (can xuat trinh the HSSV). Ap dung cho dien thoai.",
    },
    "COMBO3": {
        "name": "Mua combo 3 mon giam them",
        "discount_percent": 8,
        "description": "Giam 8% tong hoa don khi mua dien thoai + 2 phu kien tro len.",
    },
    "TET2026": {
        "name": "Khuyen mai Tet 2026",
        "discount_percent": 10,
        "description": "Giam 10% tat ca san pham. Het han 28/02/2026.",
    },
    "THANHVIEN": {
        "name": "Uu dai thanh vien",
        "discount_percent": 3,
        "description": "Giam 3% cho khach hang thanh vien.",
    },
    "MUANHIEU": {
        "name": "Mua nhieu giam nhieu",
        "discount_percent": 7,
        "description": "Giam 7% khi mua tu 2 san pham tro len (bao gom phu kien).",
    },
}


def get_discount(code: str) -> str:
    """Tra cuu ma khuyen mai. Tra ve phan tram giam gia va dieu kien."""
    code = code.strip().strip("'\"").upper().replace(" ", "")
    if code in PROMOTIONS:
        p = PROMOTIONS[code]
        return f"Ma '{code}': {p['name']} - Giam {p['discount_percent']}%. Dieu kien: {p['description']}"

    # Tim gan dung
    for key, p in PROMOTIONS.items():
        if code in key or key in code:
            return f"Ma '{key}': {p['name']} - Giam {p['discount_percent']}%. Dieu kien: {p['description']}"

    return f"Ma '{code}' khong hop le hoac da het han. Cac ma hien co: {', '.join(PROMOTIONS.keys())}"


def list_promotions(_input: str = "") -> str:
    """Liet ke tat ca chuong trinh khuyen mai hien co."""
    lines = []
    for code, p in PROMOTIONS.items():
        lines.append(
            f"- {code}: {p['name']} (giam {p['discount_percent']}%) - {p['description']}"
        )
    return "Cac chuong trinh khuyen mai hien tai:\n" + "\n".join(lines)
