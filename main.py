from dataclasses import dataclass
from functools import lru_cache
import csv, math
import matplotlib.pyplot as plt 

IPS = 200_000_000_000  # instrucciones por segundo (IPS)
LOG10_IPS = math.log10(IPS)
SEC_YEAR = 365 * 24 * 3600
EU_YEARS = 13.8e9  # edad del universo aprox. en años
LOG10_SEC_YEAR = math.log10(SEC_YEAR)
LOG10_EU_SEC = math.log10(EU_YEARS) + LOG10_SEC_YEAR

@dataclass(frozen=True)
class Complexity:  # Design Pattern -> Strategy
    name: str
    log10_ops: callable  # devuelve log10(f(n)) (operaciones)

@lru_cache(None)  # cache para evitar recalcular el factorial
def log10_fact(n: int) -> float:
    return 0.0 if n < 2 else log10_fact(n - 1) + math.log10(n)

def sci(logx: float) -> str:
    e = math.floor(logx); m = 10 ** (logx - e)
    return f"{m:.3g}×10^{e}"

def fmt_time(log_s: float) -> str:
    if log_s == -math.inf: return "0 s"
    if log_s < math.log10(60): return f"{10**log_s:.3g} s"
    if log_s < math.log10(3600): return f"{10**(log_s-math.log10(60)):.3g} min"
    if log_s < math.log10(86400): return f"{10**(log_s-math.log10(3600)):.3g} h"
    if log_s < LOG10_SEC_YEAR: return f"{10**(log_s-math.log10(86400)):.3g} días"
    log_y = log_s - LOG10_SEC_YEAR; log_eu = math.log10(EU_YEARS)
    if log_y < log_eu: return f"{10**log_y:.3g} a." if log_y < 6 else f"{10**(log_y-6):.3g} Ma"
    log_f = log_y - log_eu
    if log_f < 6: return f"{10**log_f:.3g} EU"
    return f"{10**(log_f-6):.3g} MEU" if log_f < 12 else f"{sci(log_f-6)} MEU"

def tlog10(n: int, c: Complexity) -> float:
    return c.log10_ops(n) - LOG10_IPS

def write_wide(path: str, input_sizes: list[int], complexities: list[Complexity]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["f(n)"] + input_sizes)
        for complexity in complexities:
            writer.writerow([complexity.name] + [fmt_time(tlog10(n, complexity)) for n in input_sizes])

def write_full(path: str, input_range: range, complexities: list[Complexity]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["n"] + [complexity.name for complexity in complexities])
        for n in input_range:
            writer.writerow([n] + [fmt_time(tlog10(n, complexity)) for complexity in complexities])

def print_elegant_preview(sample_sizes: list[int], complexities: list[Complexity], block_size: int = 4) -> None:
    complexity_names = [complexity.name for complexity in complexities]
    time_rows = [
        [fmt_time(tlog10(size, complexity)) for size in sample_sizes]
        for complexity in complexities
    ]

    print("\nTABLA RESUMEN DE COMPLEJIDAD")
    print("=" * 80)
    print("Formato: tiempo estimado por complejidad para distintos tamanos de entrada (n)\n")

    for block_start in range(0, len(sample_sizes), block_size):
        block_end = min(block_start + block_size, len(sample_sizes))
        block_sizes = sample_sizes[block_start:block_end]
        block_headers = ["f(n)"] + [f"n={size}" for size in block_sizes]

        block_rows = []
        for row_index, complexity_name in enumerate(complexity_names):
            block_values = time_rows[row_index][block_start:block_end]
            block_rows.append([complexity_name] + block_values)

        column_widths = []
        for column_index, header in enumerate(block_headers):
            widest_cell = max(len(str(row[column_index])) for row in block_rows) if block_rows else 0
            column_widths.append(max(len(header), widest_cell))

        separator = "+-" + "-+-".join("-" * width for width in column_widths) + "-+"
        header_line = "| " + " | ".join(
            header.ljust(column_widths[index]) for index, header in enumerate(block_headers)
        ) + " |"

        print(f"Bloque n = {block_sizes[0]} .. {block_sizes[-1]}")
        print(separator)
        print(header_line)
        print(separator)
        for row in block_rows:
            print("| " + " | ".join(str(cell).ljust(column_widths[index]) for index, cell in enumerate(row)) + " |")
        print(separator)
        print()

def plot(path: str, input_sizes: list[int], complexities: list[Complexity]) -> None:
    figure, axis = plt.subplots(figsize=(12, 7))
    x_values = input_sizes

    marker_cycle = ["o", "s", "D", "^", "v", "P", "X", "*", "<", ">", "h", "p", "8"]
    line_style_cycle = ["-", "--", "-.", ":"]

    for index, complexity in enumerate(complexities):
        y_values = [max(tlog10(n, complexity), -12) for n in x_values]
        marker = marker_cycle[index % len(marker_cycle)]
        line_style = line_style_cycle[(index // len(marker_cycle)) % len(line_style_cycle)]
        axis.plot(
            x_values,
            y_values,
            label=complexity.name,
            linewidth=1.7,
            linestyle=line_style,
            marker=marker,
            markersize=4.5,
            alpha=0.95,
        )

    axis.set_title("Complejidad temporal estimada (datos calculados)")
    axis.set_xlabel("Tamaño de entrada n")
    axis.set_ylabel("log10(tiempo en segundos)")
    axis.set_xscale("log", base=2)
    axis.set_xlim(min(x_values), max(x_values))
    axis.set_xticks(x_values)
    axis.set_xticklabels([str(value) for value in x_values], rotation=0)
    axis.grid(True, alpha=0.28)
    axis.legend(fontsize=8, ncol=3, loc="upper left", frameon=True)
    figure.tight_layout()
    figure.savefig(path, dpi=200)

def main() -> None:
    complexities = [
        Complexity("1", lambda n: 0.0),
        Complexity("log2 n", lambda n: math.log10(math.log2(n)) if n > 1 else -math.inf),
        Complexity("n", lambda n: math.log10(n)),
        Complexity("n log2 n", lambda n: (math.log10(n) + math.log10(math.log2(n))) if n > 1 else -math.inf),
        Complexity("n^2", lambda n: 2 * math.log10(n)),
        Complexity("n^3", lambda n: 3 * math.log10(n)),
        Complexity("n^4", lambda n: 4 * math.log10(n)),
        Complexity("n^5", lambda n: 5 * math.log10(n)),
        Complexity("n^(log2 n)", lambda n: (math.log10(n) * math.log2(n)) if n > 1 else 0.0),
        Complexity("2^n", lambda n: n * math.log10(2)),
        Complexity("3^n", lambda n: n * math.log10(3)),
        Complexity("n!", lambda n: log10_fact(n)),
        Complexity("n^n", lambda n: (n * math.log10(n)) if n > 0 else 0.0),
    ]
    sample_sizes_for_table = [2**k for k in range(0, 11)]
    full_input_range = range(1, 1025)

    plot("grafica_complejidad.png", sample_sizes_for_table, complexities)
    print_elegant_preview(sample_sizes_for_table, complexities)

if __name__ == "__main__":
    main()

