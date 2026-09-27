import re
import math
from typing import Dict, Tuple, Any

def col_letter_to_index(col_str: str) -> int:
    """A -> 0, B -> 1, Z -> 25, AA -> 26"""
    col_str = col_str.upper()
    idx = 0
    for char in col_str:
        idx = idx * 26 + (ord(char) - ord('A') + 1)
    return idx - 1

def index_to_col_letter(idx: int) -> str:
    """0 -> A, 1 -> B, 25 -> Z, 26 -> AA"""
    result = ""
    idx += 1
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        result = chr(ord('A') + rem) + result
    return result

class FormulaEngine:
    """
    Basit ve güvenli elektronik tablo formül motoru.
    Destekler:
    - =SUM(A1:A5) veya =TOPLA(A1:A5)
    - =AVERAGE(B1:B10) veya =ORTALAMA(B1:B10)
    - =MIN(C1:C4)
    - =MAX(D1:D10)
    - =COUNT(A1:A10) veya =SAY(A1:A10)
    - Dört işlem: =A1+B1, =A1*2, =(A1+B1)/2
    """

    def __init__(self, get_cell_value_func):
        """
        get_cell_value_func: callable(row: int, col: int) -> float or str
        """
        self.get_cell_value = get_cell_value_func

    def evaluate(self, expr: str) -> Any:
        if not expr or not isinstance(expr, str) or not expr.startswith("="):
            return expr

        raw_expr = expr[1:].strip()
        if not raw_expr:
            return ""

        try:
            # 1. Aralık Fonksiyonları: SUM, AVERAGE, MIN, MAX, COUNT
            def parse_range(range_str: str):
                parts = range_str.split(":")
                if len(parts) != 2:
                    return []
                start_m = re.match(r"([A-Za-z]+)(\d+)", parts[0].strip())
                end_m = re.match(r"([A-Za-z]+)(\d+)", parts[1].strip())
                if not start_m or not end_m:
                    return []

                start_c = col_letter_to_index(start_m.group(1))
                start_r = int(start_m.group(2)) - 1
                end_c = col_letter_to_index(end_m.group(1))
                end_r = int(end_m.group(2)) - 1

                min_r, max_r = min(start_r, end_r), max(start_r, end_r)
                min_c, max_c = min(start_c, end_c), max(start_c, end_c)

                values = []
                for r in range(min_r, max_r + 1):
                    for c in range(min_c, max_c + 1):
                        v = self.get_cell_value(r, c)
                        try:
                            num = float(v)
                            values.append(num)
                        except (ValueError, TypeError):
                            pass
                return values

            # SUM / TOPLA
            def repl_sum(m):
                vals = parse_range(m.group(1))
                return str(sum(vals))

            # AVERAGE / ORTALAMA
            def repl_avg(m):
                vals = parse_range(m.group(1))
                return str(sum(vals) / len(vals)) if vals else "0"

            # MIN
            def repl_min(m):
                vals = parse_range(m.group(1))
                return str(min(vals)) if vals else "0"

            # MAX
            def repl_max(m):
                vals = parse_range(m.group(1))
                return str(max(vals)) if vals else "0"

            # COUNT / SAY
            def repl_count(m):
                vals = parse_range(m.group(1))
                return str(len(vals))

            calc_str = raw_expr
            calc_str = re.sub(r"(?i)\b(?:SUM|TOPLA)\((.*?)\)", repl_sum, calc_str)
            calc_str = re.sub(r"(?i)\b(?:AVERAGE|ORTALAMA)\((.*?)\)", repl_avg, calc_str)
            calc_str = re.sub(r"(?i)\bMIN\((.*?)\)", repl_min, calc_str)
            calc_str = re.sub(r"(?i)\bMAX\((.*?)\)", repl_max, calc_str)
            calc_str = re.sub(r"(?i)\b(?:COUNT|SAY)\((.*?)\)", repl_count, calc_str)

            # 2. Tekil Hücre Referansları (Örn: A1, B2)
            def repl_cell(m):
                col = col_letter_to_index(m.group(1))
                row = int(m.group(2)) - 1
                v = self.get_cell_value(row, col)
                try:
                    return str(float(v))
                except (ValueError, TypeError):
                    return "0"

            calc_str = re.sub(r"\b([A-Za-z]+)(\d+)\b", repl_cell, calc_str)

            # 3. Güvenli Matematiksel İfade Değerlendirme
            # Yalnızca sayılar ve temel operatörlere izin ver
            if not re.match(r"^[\d\s\+\-\*\/\(\)\.\,]+$", calc_str):
                return "#DEĞER!"

            # Virgülleri noktaya çevir
            calc_str = calc_str.replace(",", ".")
            res = eval(calc_str, {"__builtins__": None}, {})
            if isinstance(res, float) and res.is_integer():
                return int(res)
            return round(res, 4) if isinstance(res, float) else res
        except ZeroDivisionError:
            return "#SIFIRABÖLÜNDÜ!"
        except Exception:
            return "#HATA!"
