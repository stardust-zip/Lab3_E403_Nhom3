from src.tools.check_stock import PRODUCTS


def search_by_brand(brand: str) -> str:
    """Tim kiem dien thoai theo hang (Samsung, Apple, Xiaomi, OPPO)."""
    brand = brand.strip().strip("'\"").lower()
    matches = []
    for name, p in PRODUCTS.items():
        if p["brand"].lower() == brand and p["category"] == "dien thoai":
            matches.append(
                f"- {name.title()}: {p['price']:,}d (con {p['quantity']} sp)"
            )
    if matches:
        return f"Dien thoai {brand.title()} tai cua hang:\n" + "\n".join(matches)
    return f"Khong tim thay dien thoai hang '{brand}'. Cua hang co: Samsung, Apple, Xiaomi, OPPO."


def search_by_price(max_price: str) -> str:
    """Tim dien thoai theo khoang gia. Input: gia toi da (VND), vd '3000000'."""
    max_price = (
        max_price.strip()
        .strip("'\"")
        .replace(",", "")
        .replace(".", "")
        .replace("d", "")
    )
    try:
        budget = int(max_price)
    except ValueError:
        return f"Loi: '{max_price}' khong phai so hop le. Hay nhap so nguyen VND, vd: 3000000"
    matches = []
    for name, p in PRODUCTS.items():
        if p["price"] <= budget and p["category"] == "dien thoai":
            matches.append(f"- {name.title()}: {p['price']:,}d")
    if matches:
        return f"Dien thoai duoi {budget:,}d:\n" + "\n".join(matches)
    return f"Khong co dien thoai nao duoi {budget:,}d."


def list_brands(_input: str = "") -> str:
    """Liet ke cac hang dien thoai co trong cua hang."""
    brands = set()
    for p in PRODUCTS.values():
        if p["category"] == "dien thoai":
            brands.add(p["brand"])
    brand_list = sorted(brands)
    counts = {}
    for p in PRODUCTS.values():
        if p["category"] == "dien thoai":
            counts[p["brand"]] = counts.get(p["brand"], 0) + 1
    lines = [f"- {b} ({counts[b]} san pham)" for b in brand_list]
    return "Cac hang dien thoai tai cua hang:\n" + "\n".join(lines)
