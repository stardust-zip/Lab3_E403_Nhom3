from src.tools.calculator import calculator
from src.tools.check_stock import check_stock
from src.tools.get_discount import get_discount, list_promotions
from src.tools.search import search_by_brand, search_by_price, list_brands

TOOLS = [
    {
        "name": "check_stock",
        "description": "Tim kiem san pham theo ten (dien thoai hoac phu kien). Input: ten san pham, vd 'iphone 17 pro', 'op lung iphone 17 pro'. Tra ve gia va so luong ton kho.",
        "func": check_stock,
    },
    {
        "name": "search_by_price",
        "description": "Tim dien thoai theo khoang gia. Input: gia toi da (VND), vd '3000000'. Tra ve danh sach dien thoai trong tam gia.",
        "func": search_by_price,
    },
    {
        "name": "search_by_brand",
        "description": "Tim dien thoai theo hang. Input: ten hang, vd 'Samsung', 'Apple', 'Xiaomi', 'OPPO'.",
        "func": search_by_brand,
    },
    {
        "name": "list_brands",
        "description": "Liet ke tat ca cac hang dien thoai co trong cua hang. Khong can input (truyen 'all').",
        "func": list_brands,
    },
    {
        "name": "get_discount",
        "description": "Tra cuu ma khuyen mai/voucher. Input: ma khuyen mai, vd 'HSSV2026', 'COMBO3', 'MUANHIEU'. Tra ve phan tram giam va dieu kien.",
        "func": get_discount,
    },
    {
        "name": "list_promotions",
        "description": "Liet ke tat ca chuong trinh khuyen mai hien co. Khong can input (truyen 'all').",
        "func": list_promotions,
    },
    {
        "name": "calculator",
        "description": "Tinh toan bieu thuc toan hoc. Input: bieu thuc, vd '32990000 + 350000 + 150000', '33490000 * 0.95'. Tra ve ket qua.",
        "func": calculator,
    },
]
