#!/usr/bin/env python3
"""
check.py — Orchestrateur de validation web-design-enhancer
Transforme les phases du SKILL.md en gates mécaniques.
Compatible avec tout modèle IA — aucune dépendance plateforme.

Usage:
  python3 scripts/check.py --gate 0          # Phase 0 exécutée ?
  python3 scripts/check.py --gate 1          # DESIGN.md valide ? (bloque avant le code)
  python3 scripts/check.py --final           # Validation complète avant livraison
  python3 scripts/check.py --final --code ./src

Codes de sortie:
  0 = OK, continuer
  1 = BLOQUÉ, corriger avant de continuer
"""

import sys
import os
import re
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# ─── Couleurs terminal ────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):  print(f"  {GREEN}✅ {msg}{RESET}")
def fail(msg): print(f"  {RED}❌ {msg}{RESET}")
def warn(msg): print(f"  {YELLOW}⚠️  {msg}{RESET}")
def info(msg): print(f"  {CYAN}→  {msg}{RESET}")

SCRIPTS_DIR = Path(__file__).parent
LOG_FILE    = Path(".phase-log.json")


# ─── Log de phases ────────────────────────────────────────────────────────────

def load_log():
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text())
        except Exception:
            pass
    return {}

def save_log(log):
    LOG_FILE.write_text(json.dumps(log, indent=2))

def mark_passed(gate):
    log = load_log()
    log[gate] = {"passed": True, "at": datetime.now().isoformat()}
    save_log(log)

def gate_passed(gate):
    return load_log().get(gate, {}).get("passed", False)


# ─── Gate 0 — Preuve d'exécution Phase 0 ─────────────────────────────────────

def check_gate0():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  GATE 0 — Phase 0 exécutée ?{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    errors = []

    # 1. design-system-output.md présent (produit par search.py --save)
    ds_files = list(Path(".").glob("design-system-output*.md"))
    if ds_files:
        ok(f"design-system-output.md trouvé ({ds_files[0].name})")
    else:
        fail("design-system-output.md absent")
        info("Lancer : python3 scripts/search.py \"<description>\" --design-system -p \"<Projet>\" --save")
        errors.append("search.py non exécuté")

    # 2. Un fichier DESIGN.md de référence getdesign présent
    getdesign_files = list(Path(".").glob("getdesign-*.md")) + list(Path(".").glob("brand-*.md"))
    if getdesign_files:
        ok(f"Référence getdesign.md trouvée ({getdesign_files[0].name})")
    else:
        fail("Aucun fichier de référence getdesign.md trouvé")
        info("Lancer : npx getdesign@latest add <brand>")
        info("Exemples de brand : vercel / stripe / linear / notion / supabase")
        errors.append("getdesign.md non exécuté")

    # 3. DESIGN.md du projet présent
    if Path("DESIGN.md").exists():
        ok("DESIGN.md présent")
    else:
        fail("DESIGN.md absent — créer depuis templates/design-md-template.md")
        errors.append("DESIGN.md absent")

    # 4. Section Sources Phase 0 dans DESIGN.md
    if Path("DESIGN.md").exists():
        content = Path("DESIGN.md").read_text(encoding="utf-8")
        if "## 0. Sources Phase 0" in content:
            ok("Section '## 0. Sources Phase 0' présente dans DESIGN.md")
            # Vérifier que les placeholders ont été remplacés
            if "[Ex:" in content or "<brand>" in content or "<description>" in content:
                fail("DESIGN.md contient encore des placeholders non remplis")
                info("Remplacer tous les [Ex: ...] et <placeholder> par de vraies valeurs")
                errors.append("Placeholders non remplis dans DESIGN.md")
        else:
            fail("Section '## 0. Sources Phase 0' absente du DESIGN.md")
            info("Utiliser templates/design-md-template.md comme base")
            errors.append("Section Sources absente du DESIGN.md")

    # Résultat
    _print_result(errors, "GATE 0")
    if not errors:
        mark_passed("gate0")
    return len(errors) == 0


# ─── Gate 1 — Validation DESIGN.md ───────────────────────────────────────────

def check_gate1():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  GATE 1 — DESIGN.md valide ? (avant tout code){RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    # Gate 0 doit être passé
    if not gate_passed("gate0"):
        fail("Gate 0 non validé — exécuter d'abord : python3 scripts/check.py --gate 0")
        _print_result(["Gate 0 non passé"], "GATE 1")
        return False

    if not Path("DESIGN.md").exists():
        fail("DESIGN.md absent")
        _print_result(["DESIGN.md absent"], "GATE 1")
        return False

    ok("Gate 0 validé")

    # Lancer validate_design.py
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "validate_design.py"), "DESIGN.md"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode == 0:
        mark_passed("gate1")
        return True
    return False


# ─── Gate Final — Validation complète avant livraison ────────────────────────

def check_final(code_path=None):
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  GATE FINAL — Validation avant livraison{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    # Gate 1 doit être passé
    if not gate_passed("gate1"):
        fail("Gate 1 non validé — exécuter d'abord : python3 scripts/check.py --gate 1")
        _print_result(["Gate 1 non passé"], "GATE FINAL")
        return False

    ok("Gate 1 validé")
    errors = []

    # 1. detect_ai_slop.py
    print(f"\n{CYAN}[1/3] Détection antipatterns IA...{RESET}")
    slop_args = [sys.executable, str(SCRIPTS_DIR / "detect_ai_slop.py"), "--design", "DESIGN.md"]
    if code_path:
        slop_args += ["--code", code_path]
    r = subprocess.run(slop_args, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        errors.append("detect_ai_slop.py — antipatterns détectés")

    # 2. audit_spacing.py
    print(f"\n{CYAN}[2/3] Audit grille 8px...{RESET}")
    spacing_path = code_path or "."
    r = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "audit_spacing.py"), "--path", spacing_path],
        capture_output=True, text=True
    )
    print(r.stdout)
    if r.returncode != 0:
        errors.append("audit_spacing.py — violations grille 8px")

    # 3. validate_design.py (passe finale)
    print(f"\n{CYAN}[3/3] Validation finale DESIGN.md...{RESET}")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "validate_design.py"), "DESIGN.md"],
        capture_output=True, text=True
    )
    print(r.stdout)
    if r.returncode != 0:
        errors.append("validate_design.py — contrat DESIGN.md non respecté")

    _print_result(errors, "GATE FINAL")
    if not errors:
        mark_passed("final")
        _print_delivery_ok()
    return len(errors) == 0


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _print_result(errors, gate_name):
    print(f"\n{BOLD}{'─'*60}{RESET}")
    if errors:
        print(f"{RED}{BOLD}  ❌ {gate_name} : BLOQUÉ — {len(errors)} problème(s){RESET}")
        for e in errors:
            print(f"     • {e}")
        print(f"\n{YELLOW}  → Corriger les erreurs et relancer cette commande.{RESET}")
        print(f"{YELLOW}  → Ne pas passer à l'étape suivante tant que ce gate n'est pas vert.{RESET}")
    else:
        print(f"{GREEN}{BOLD}  ✅ {gate_name} : VALIDÉ — continuer{RESET}")
    print(f"{BOLD}{'─'*60}{RESET}\n")

def _print_delivery_ok():
    print(f"""
{GREEN}{BOLD}╔══════════════════════════════════════════════╗
║  ✅  LIVRAISON AUTORISÉE                       ║
║  Les 3 gates sont verts. Zéro AI slop détecté. ║
╚══════════════════════════════════════════════╝{RESET}
""")


# ─── Entrée ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="web-design-enhancer — orchestrateur de validation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gate", type=int, choices=[0, 1], help="Vérifier un gate spécifique (0 ou 1)")
    group.add_argument("--final", action="store_true", help="Validation complète avant livraison")
    parser.add_argument("--code", type=str, default=None, help="Chemin du code source (pour --final)")
    args = parser.parse_args()

    if args.gate == 0:
        success = check_gate0()
    elif args.gate == 1:
        success = check_gate1()
    elif args.final:
        success = check_final(args.code)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
