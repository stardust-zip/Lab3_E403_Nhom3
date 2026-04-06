import re


def calculator(expression: str) -> str:
    """Tinh toan bieu thuc toan hoc. Input: bieu thuc hop le, vd '32990000 + 350000 + 150000'."""
    expression = expression.strip().strip("'\"")
    # Chi cho phep so, phep tinh, ngoac, dau cach, dau phay
    cleaned = expression.replace(",", "")
    if not re.match(r"^[\d\s\+\-\*\/\.\(\)]+$", cleaned):
        return f"Loi: Bieu thuc khong hop le '{expression}'"
    try:
        result = eval(cleaned, {"__builtins__": {}}, {})
        if isinstance(result, float) and result == int(result):
            result = int(result)
        return f"{result:,}".replace(",", ".")
    except Exception as e:
        return f"Loi: Khong the tinh '{expression}' — {e}"
