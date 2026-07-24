#!/usr/bin/env python3
import os, re, shutil, sys

ROOT = "/Users/r/Projects/PiezoPhone/PiezoPhone"
PL   = os.path.join(ROOT, "Project_Libraries")
PRETTY   = os.path.join(ROOT, "PiezoPhone.pretty")
SHAPES   = os.path.join(ROOT, "PiezoPhone.3dshapes")
SYMLIB   = os.path.join(ROOT, "PiezoPhone.kicad_sym")
NICK = "PiezoPhone"

os.makedirs(PRETTY, exist_ok=True)
os.makedirs(SHAPES, exist_ok=True)

log = []

# ---------------------------------------------------------------------------
# 1. Footprints to copy: (source path, dest filename)
# ---------------------------------------------------------------------------
footprints = [
    (f"{PL}/TB002_500_02BE/CUI_TB002-500-02BE.kicad_mod",                       "CUI_TB002-500-02BE.kicad_mod"),
    (f"{PL}/860020572003/WCAP-ATG5_5X11_DXL_.kicad_mod",                        "WCAP-ATG5_5X11_DXL_.kicad_mod"),
    (f"{PL}/STX_3000/KYCON_STX-3000.kicad_mod",                                 "KYCON_STX-3000.kicad_mod"),
    (f"{PL}/SB150_E3_73/DIOAD930W78L520D270.kicad_mod",                         "DIOAD930W78L520D270.kicad_mod"),
    (f"{PL}/LR1F10R/KiCADv6/footprints.pretty/RES_LR1_TYCO_TYC.kicad_mod",      "RES_LR1_TYCO_TYC.kicad_mod"),
    (f"{PL}/PDB12_H4251_103BF/KiCADv6/footprints.pretty/PDB12-H4251-103BF_BRN.kicad_mod", "PDB12-H4251-103BF_BRN.kicad_mod"),
    (f"{PL}/RDEC71E106K2K1H03B/KiCADv6/footprints.pretty/CAP_RDEC71E106K2K1H03B_MUR.kicad_mod", "CAP_RDEC71E106K2K1H03B_MUR.kicad_mod"),
    (f"{PL}/FG28X7R1H104KNT00/KiCADv6/footprints.pretty/CAP_FG28_TDK.kicad_mod","CAP_FG28_TDK.kicad_mod"),
]
# Ferrite footprints (existing complete set)
ferr_pretty = f"{ROOT}/footprints/Ferrite_THT_Wurth.pretty"
for fn in sorted(os.listdir(ferr_pretty)):
    if fn.endswith(".kicad_mod"):
        footprints.append((os.path.join(ferr_pretty, fn), fn))

for src, dst in footprints:
    shutil.copy2(src, os.path.join(PRETTY, dst))
log.append(f"Footprints copied: {len(footprints)}")

# ---------------------------------------------------------------------------
# 2. 3D models to copy: (source, dest filename)
# ---------------------------------------------------------------------------
models = [
    (f"{PL}/TB002_500_02BE/TB002-500-02BE.step", "TB002-500-02BE.step"),
    (f"{PL}/860020572003/WCAP-ATG5_5X11.step",   "WCAP-ATG5_5X11.step"),
    (f"{PL}/SB150_E3_73/SB150-E3_73.step",       "SB150-E3_73.step"),
    (f"{PL}/ANT11SF1CQE.stp",                     "ANT11SF1CQE.stp"),
    (f"{PL}/ABX00142-step/PCB(ABX00142).step",   "ABX00142_Arduino_Nano_R4.step"),
]
ferr_shapes = f"{ROOT}/3dmodels/Ferrite_THT_Wurth.3dshapes"
for fn in sorted(os.listdir(ferr_shapes)):
    if fn.endswith((".step", ".wrl")):
        models.append((os.path.join(ferr_shapes, fn), fn))

for src, dst in models:
    shutil.copy2(src, os.path.join(SHAPES, dst))
log.append(f"3D models copied: {len(models)}")

# ---------------------------------------------------------------------------
# 3. Fix 3D model references in copied footprints
# ---------------------------------------------------------------------------
# 3a. SnapMagic footprints that ship a STEP but have no (model ...) line: insert one.
add_model = {
    "CUI_TB002-500-02BE.kicad_mod":     "TB002-500-02BE.step",
    "WCAP-ATG5_5X11_DXL_.kicad_mod":    "WCAP-ATG5_5X11.step",
    "DIOAD930W78L520D270.kicad_mod":    "SB150-E3_73.step",
}
for fn, step in add_model.items():
    p = os.path.join(PRETTY, fn)
    with open(p) as fh:
        txt = fh.read()
    if "(model" in txt:
        log.append(f"  WARN {fn} already has a model line; left unchanged")
        continue
    model_block = (
        f'  (model "${{KIPRJMOD}}/PiezoPhone.3dshapes/{step}"\n'
        f'    (offset (xyz 0 0 0))\n'
        f'    (scale (xyz 1 1 1))\n'
        f'    (rotate (xyz 0 0 0))\n'
        f'  )\n'
    )
    # insert before the final top-level closing paren
    idx = txt.rstrip().rfind(")")
    txt = txt[:idx] + model_block + txt[idx:]
    with open(p, "w") as fh:
        fh.write(txt)
    log.append(f"  model added -> {fn}")

# 3b. Ferrite footprints: repoint ${WE_3DMODEL_DIR}/Ferrite_THT_Wurth.3dshapes -> KIPRJMOD/PiezoPhone.3dshapes
ferr_fixed = 0
for fn in os.listdir(PRETTY):
    if not fn.startswith("FB_Wurth_WE-WAFB_"):
        continue
    p = os.path.join(PRETTY, fn)
    with open(p) as fh:
        txt = fh.read()
    new = txt.replace("${WE_3DMODEL_DIR}/Ferrite_THT_Wurth.3dshapes",
                      "${KIPRJMOD}/PiezoPhone.3dshapes")
    if new != txt:
        with open(p, "w") as fh:
            fh.write(new)
        ferr_fixed += 1
log.append(f"  ferrite model paths repointed: {ferr_fixed}")

# ---------------------------------------------------------------------------
# 4. Merge symbols
# ---------------------------------------------------------------------------
sym_sources = [
    f"{PL}/TB002_500_02BE/TB002-500-02BE.kicad_sym",
    f"{PL}/860020572003/WCAP-ATG5_5X11.kicad_sym",
    f"{PL}/STX_3000/STX-3000.kicad_sym",
    f"{PL}/SB150_E3_73/SB150-E3_73.kicad_sym",
    f"{PL}/PDB12_H4251_103BF/KiCADv6/2026-05-28_05-19-05.kicad_sym",
    f"{PL}/LR1F10R/KiCADv6/2026-05-28_04-46-30.kicad_sym",
    f"{PL}/LR1F1K0/KiCADv6/2026-05-28_04-39-55.kicad_sym",
    f"{PL}/RDEC71E106K2K1H03B/KiCADv6/2026-05-28_19-37-08.kicad_sym",
    f"{PL}/FG28X7R1H104KNT00/KiCADv6/2026-05-28_04-52-06.kicad_sym",
    f"{ROOT}/Project_Symbols/Ferrite_Wurth_WE-WAFB.kicad_sym",
]

def extract_top_symbols(text):
    """Return list of top-level (symbol ...) s-expression strings."""
    out = []
    i = 0
    n = len(text)
    while True:
        j = text.find("(symbol ", i)
        if j == -1:
            break
        # ensure this is a TOP-level symbol: preceding non-space char on its line context.
        # We detect depth by scanning from start; simpler: balance parens from j.
        depth = 0
        k = j
        in_str = False
        esc = False
        while k < n:
            c = text[k]
            if in_str:
                if esc:
                    esc = False
                elif c == '\\':
                    esc = True
                elif c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        out.append(text[j:k+1])
                        i = k + 1
                        break
            k += 1
        else:
            break
    return out

def fix_footprint_prop(sym):
    def repl(m):
        val = m.group(2)
        base = val.split(":")[-1]
        return f'{m.group(1)}"{NICK}:{base}"'
    return re.sub(r'(\(property "Footprint" )"([^"]*)"', repl, sym)

all_syms = []
seen = set()
for src in sym_sources:
    with open(src) as fh:
        txt = fh.read()
    syms = extract_top_symbols(txt)
    for s in syms:
        name_m = re.match(r'\(symbol\s+"([^"]+)"', s)
        name = name_m.group(1) if name_m else "?"
        if name in seen:
            log.append(f"  WARN duplicate symbol skipped: {name} (from {os.path.basename(src)})")
            continue
        seen.add(name)
        all_syms.append(fix_footprint_prop(s))

header = '(kicad_symbol_lib\n  (version 20211014)\n  (generator kicad_symbol_editor)\n'
# reindent each symbol block to 2 spaces (they already start at col 0 or 2)
body = []
for s in all_syms:
    s = s.strip()
    body.append("  " + s)
content = header + "\n".join(body) + "\n)\n"
with open(SYMLIB, "w") as fh:
    fh.write(content)
log.append(f"Symbols merged: {len(all_syms)} -> {SYMLIB}")
log.append("Symbol names: " + ", ".join(sorted(seen)))

print("\n".join(log))
