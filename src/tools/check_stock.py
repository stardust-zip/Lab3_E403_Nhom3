# Database san pham cua hang dien thoai
PRODUCTS = {
    # Samsung
    "samsung galaxy a05": {
        "brand": "Samsung",
        "price": 2490000,
        "quantity": 15,
        "category": "dien thoai",
    },
    "samsung galaxy a16": {
        "brand": "Samsung",
        "price": 4990000,
        "quantity": 20,
        "category": "dien thoai",
    },
    "samsung galaxy s24": {
        "brand": "Samsung",
        "price": 17990000,
        "quantity": 10,
        "category": "dien thoai",
    },
    "samsung galaxy s24 ultra": {
        "brand": "Samsung",
        "price": 27990000,
        "quantity": 5,
        "category": "dien thoai",
    },
    "samsung galaxy z flip6": {
        "brand": "Samsung",
        "price": 22990000,
        "quantity": 8,
        "category": "dien thoai",
    },
    # iPhone
    "iphone 16": {
        "brand": "Apple",
        "price": 22490000,
        "quantity": 25,
        "category": "dien thoai",
    },
    "iphone 16 pro": {
        "brand": "Apple",
        "price": 28490000,
        "quantity": 12,
        "category": "dien thoai",
    },
    "iphone 16 pro max": {
        "brand": "Apple",
        "price": 34490000,
        "quantity": 8,
        "category": "dien thoai",
    },
    "iphone 17 pro": {
        "brand": "Apple",
        "price": 32990000,
        "quantity": 18,
        "category": "dien thoai",
    },
    "iphone 17 pro max": {
        "brand": "Apple",
        "price": 38990000,
        "quantity": 10,
        "category": "dien thoai",
    },
    # Xiaomi
    "xiaomi redmi note 13": {
        "brand": "Xiaomi",
        "price": 4590000,
        "quantity": 30,
        "category": "dien thoai",
    },
    "xiaomi 14t": {
        "brand": "Xiaomi",
        "price": 10990000,
        "quantity": 12,
        "category": "dien thoai",
    },
    # OPPO
    "oppo reno12": {
        "brand": "OPPO",
        "price": 9490000,
        "quantity": 15,
        "category": "dien thoai",
    },
    "oppo a18": {
        "brand": "OPPO",
        "price": 2990000,
        "quantity": 25,
        "category": "dien thoai",
    },
    # Phu kien
    "op lung iphone 17 pro": {
        "brand": "Apple",
        "price": 350000,
        "quantity": 50,
        "category": "phu kien",
    },
    "op lung iphone 16 pro": {
        "brand": "Apple",
        "price": 290000,
        "quantity": 40,
        "category": "phu kien",
    },
    "op lung samsung galaxy s24": {
        "brand": "Samsung",
        "price": 250000,
        "quantity": 35,
        "category": "phu kien",
    },
    "kinh cuong luc iphone 17 pro": {
        "brand": "Apple",
        "price": 150000,
        "quantity": 100,
        "category": "phu kien",
    },
    "kinh cuong luc iphone 16 pro": {
        "brand": "Apple",
        "price": 120000,
        "quantity": 80,
        "category": "phu kien",
    },
    "kinh cuong luc samsung galaxy s24": {
        "brand": "Samsung",
        "price": 100000,
        "quantity": 60,
        "category": "phu kien",
    },
    "sac nhanh 20w": {
        "brand": "Apple",
        "price": 490000,
        "quantity": 40,
        "category": "phu kien",
    },
    "tai nghe airpods 4": {
        "brand": "Apple",
        "price": 3290000,
        "quantity": 20,
        "category": "phu kien",
    },
}


def check_stock(query: str) -> str:
    """Tim kiem san pham theo ten. Tra ve thong tin gia, so luong ton kho."""
    query = query.strip().strip("'\"").lower()

    # Tim chinh xac
    if query in PRODUCTS:
        p = PRODUCTS[query]
        return f"{query.title()}: {p['price']:,}d, con {p['quantity']} san pham ({p['category']})"

    # Tim gan dung
    matches = []
    for name, p in PRODUCTS.items():
        if query in name or name in query:
            matches.append(f"{name.title()}: {p['price']:,}d, con {p['quantity']} sp")

    if matches:
        return "\n".join(matches)

    return f"Khong tim thay san pham '{query}' trong cua hang."
