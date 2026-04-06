from src.tools.calculator import calculator
from src.tools.check_stock import check_stock
from src.tools.get_discount import get_discount, list_promotions

TOOLS = [
    {
        "name": "check_stock",
        "description": "Tim kiem san pham theo ten (dien thoai hoac phu kien). Input: ten san pham, vd 'iphone 17 pro', 'op lung iphone 17 pro'. Tra ve gia va so luong ton kho.",
        "func": check_stock,
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
