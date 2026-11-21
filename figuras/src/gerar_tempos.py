"""Gera figuras/tempos-a4.pdf e figuras/tempos-a3.pdf.

Diagrama de tempos ideal (regime permanente) do sequencial NE555 + CD4017B:
v_C (pinos 2/6), OUT555 = CLK, Q0..Q5 e o pulso Q6 -> RESET.
Valores do esquemático: R1 = 1,2 kOhm, R2 = 10 kOhm, C2 = 10 uF.
"""
import shutil
from pathlib import Path

import numpy as np
import matplotlib
import matplotlib.pyplot as plt


def configurar(preambulo_extra="", forcar_usetex=None):
    """Estilo técnico: usetex (Computer Modern) quando houver LaTeX, senão mathtext."""
    usetex = bool(shutil.which("latex")) if forcar_usetex is None else forcar_usetex
    base = {"font.size": 10, "axes.labelsize": 10, "xtick.labelsize": 9,
            "ytick.labelsize": 9, "axes.spines.top": False, "axes.spines.right": False,
            "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "lines.linewidth": 1.4}
    if usetex:
        base.update({"text.usetex": True, "font.family": "serif",
                     "text.latex.preamble": r"\usepackage{amsmath}" + preambulo_extra})
    else:
        base.update({"text.usetex": False, "font.family": "serif",
                     "font.serif": ["DejaVu Serif"], "mathtext.fontset": "cm"})
    matplotlib.rcParams.update(base)


def salvar(fig, caminho):
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(caminho)
    print(f"OK {caminho}")

R1, R2, C2 = 1.2e3, 10e3, 10e-6
LN2 = np.log(2.0)
TH = LN2 * (R1 + R2) * C2          # 77,63 ms
TL = LN2 * R2 * C2                 # 69,31 ms
T = TH + TL                        # 146,94 ms
CICLOS = 7.25

PETROLEO = "#0D7377"
DOURADO = "#8F6E1F"
OLIVA = "#556B2F"
CHAR = "#36454F"
VCCR = "#A61E22"


def v_c(t):
    """Tensão no capacitor normalizada por VCC, começando no início de uma carga."""
    tm = np.mod(t, T)
    carga = 1.0 - (2.0 / 3.0) * np.exp(-tm / ((R1 + R2) * C2))
    desc = (2.0 / 3.0) * np.exp(-(tm - TH) / (R2 * C2))
    return np.where(tm < TH, carga, desc)


def saida_555(t):
    return (np.mod(t, T) < TH).astype(float)


def q_k(k, t):
    n = np.floor(t / T).astype(int) % 6
    return (n == k).astype(float)


def desenhar(caminho, largura_in, altura_in, sans, ef=1.0):
    """ef = escala das fontes (1,0 no A4; menor na prancha A3, que é mais compacta)."""
    configurar(preambulo_extra=r"\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}",
               forcar_usetex=False if sans else None)
    if sans:
        matplotlib.rcParams.update({"font.family": "sans-serif",
                                    "font.sans-serif": ["Arial", "DejaVu Sans"],
                                    "mathtext.fontset": "dejavusans"})
    matplotlib.rcParams.update({"xtick.labelsize": 9 * ef, "ytick.labelsize": 9 * ef,
                                "axes.labelsize": 10 * ef})
    fig, ax = plt.subplots(figsize=(largura_in, altura_in))
    t = np.linspace(0.0, CICLOS * T, 8000)
    ms = t * 1e3

    # trilhas (de cima para baixo): v_C, CLK, Q0..Q5, Q6/RESET
    alt_dig = 0.62
    passo = 1.0
    y_vc = 9.7
    trilhas = []

    # v_C normalizada: 1/3 -> y_vc, 2/3 -> y_vc + 1.3
    esc = 1.3 / (1.0 / 3.0)
    base_vc = y_vc - esc * (1.0 / 3.0)
    ax.plot(ms, base_vc + esc * v_c(t), color=PETROLEO, lw=1.4)
    for frac, txt in ((1 / 3, r"$\frac{1}{3}V_{CC}$"), (2 / 3, r"$\frac{2}{3}V_{CC}$")):
        yy = base_vc + esc * frac
        ax.hlines(yy, 0.0, CICLOS * T * 1e3, color="0.55", lw=0.6, ls="--")
        ax.text(CICLOS * T * 1e3 + 6, yy, txt, va="center", ha="left", fontsize=8 * ef, color="0.3")
    trilhas.append((y_vc + 0.65, r"$v_C$ (pinos 2 e 6)", PETROLEO))

    y_clk = 7.6
    ax.plot(ms, y_clk + alt_dig * saida_555(t), color=PETROLEO, lw=1.4, drawstyle="steps-post")
    trilhas.append((y_clk + alt_dig / 2, "OUT555 = CLK", PETROLEO))

    for k in range(6):
        yk = 6.55 - k * passo
        ax.plot(ms, yk + alt_dig * q_k(k, t), color=OLIVA, lw=1.3, drawstyle="steps-post")
        trilhas.append((yk + alt_dig / 2, rf"Q{k} $\rightarrow$ D{k + 1}", OLIVA))

    y_rst = 6.55 - 6 * passo
    ax.plot([ms[0], ms[-1]], [y_rst, y_rst], color=DOURADO, lw=1.3)
    for n in range(1, int(CICLOS // 6) + 1):
        t6 = 6 * n * T * 1e3
        larg = 3.0  # ms, apenas para ficar visível (o pulso real é de nanossegundos)
        ax.plot([t6, t6, t6 + larg, t6 + larg], [y_rst, y_rst + alt_dig, y_rst + alt_dig, y_rst],
                color=DOURADO, lw=1.3)
        ax.annotate("pulso de reset (fora de escala:\nlargura real da ordem de centenas de ns)",
                    xy=(t6 + larg, y_rst + alt_dig * 0.9), xytext=(t6 - 560, y_rst + 0.45),
                    fontsize=7.5 * ef, color=DOURADO, ha="left", va="center",
                    bbox=dict(fc="white", ec="none", pad=0.8),
                    arrowprops=dict(arrowstyle="->", lw=0.7, color=DOURADO))
    trilhas.append((y_rst + alt_dig / 2, "Q6 = RESET", DOURADO))

    # bordas de subida do clock (linhas guia)
    for n in range(0, int(CICLOS) + 1):
        ax.axvline(n * T * 1e3, color="0.82", lw=0.6, zorder=0)

    # cotas no primeiro ciclo
    y_cota = y_clk + alt_dig + 0.3
    for x0, x1, txt in ((0.0, TH * 1e3, r"$t_H$"), (TH * 1e3, T * 1e3, r"$t_L$")):
        ax.annotate("", xy=(x0, y_cota), xytext=(x1, y_cota),
                    arrowprops=dict(arrowstyle="<->", lw=0.7, color=CHAR))
        ax.text((x0 + x1) / 2, y_cota + 0.1, txt, ha="center", va="bottom", fontsize=8 * ef, color=CHAR,
                bbox=dict(fc="white", ec="none", pad=0.4))
    ax.annotate("", xy=(0.0, y_cota + 0.6), xytext=(T * 1e3, y_cota + 0.6),
                arrowprops=dict(arrowstyle="<->", lw=0.7, color=CHAR))
    ax.text(T * 1e3 + 12, y_cota + 0.6,
            r"$T = t_H + t_L \approx 77{,}62 + 69{,}30 = 146{,}92$ ms  $\Rightarrow$  $f \approx 6{,}81$ Hz",
            ha="left", va="center", fontsize=8 * ef, color=CHAR,
            bbox=dict(fc="white", ec="none", pad=0.8))

    # um LED aceso por período: marcação da volta completa
    ax.annotate("", xy=(0.0, -0.95), xytext=(6 * T * 1e3, -0.95),
                arrowprops=dict(arrowstyle="<->", lw=0.7, color=CHAR))
    ax.text(3 * T * 1e3, -0.9, r"uma volta completa: $6T\approx 0{,}88$ s", ha="center",
            va="bottom", fontsize=7.5 * ef, color=CHAR, bbox=dict(fc="white", ec="none", pad=0.8))

    ax.set_yticks([y for y, _, _ in trilhas])
    ax.set_yticklabels([s for _, s, _ in trilhas])
    for lbl, (_, _, cor) in zip(ax.get_yticklabels(), trilhas):
        lbl.set_color(cor)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-10, CICLOS * T * 1e3 + 75)
    ax.set_ylim(-1.15, y_vc + 1.55)
    ax.set_xlabel("tempo (ms)")
    ax.spines["left"].set_visible(False)
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(100))
    fmt = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}")
    ax.xaxis.set_major_formatter(fmt)
    salvar(fig, caminho)
    plt.close(fig)


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parents[1]
    print(f"tH = {TH*1e3:.2f} ms, tL = {TL*1e3:.2f} ms, T = {T*1e3:.2f} ms, f = {1/T:.3f} Hz")
    desenhar(str(raiz / "tempos-a4.pdf"), 6.3, 4.6, sans=False)
    desenhar(str(raiz / "tempos-a3.pdf"), 4.78, 3.08, sans=True, ef=0.8)
