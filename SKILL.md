---
name: web-design-enhancer
description: Validateur et enforcer du contrat DESIGN.md. Pilier 3 de l'écosystème design composé de getdesign.md (références visuelles réelles), UI/UX Pro Max (intelligence design par industrie) et shadcn/ui (implémentation). Éradique l'improvisation visuelle de l'IA via 4 scripts de validation automatisée, GSAP et un audit Playwright sur 4 breakpoints.
---

# Web Design Enhancer

Ce skill est le **validateur et enforcer** de l'écosystème design. Il garantit que le code implémenté respecte à la lettre le contrat `DESIGN.md` établi en amont par les deux autres piliers.

---

## L'Écosystème — Les 3 Piliers

```
┌─────────────────────────────────────────────────────────────────────┐
│  PILIER 1 — getdesign.md          PILIER 2 — UI/UX Pro Max          │
│                                                                     │
│  Références visuelles réelles     Intelligence design/industrie     │
│  "À quoi ressemble mon projet ?"  "Quelles décisions pour mon       │
│  (72 sites : Stripe, Vercel,       type de produit ?"               │
│  Linear, Nike, Tesla...)          (161 règles, 67 styles,           │
│                                    161 palettes, 57 typos)          │
│                    ↘                      ↙                         │
│                                                                     │
│              DESIGN.md  ←  contrat de design du projet              │
│                                                                     │
│                              ↓                                      │
│                                                                     │
│  PILIER 3 — ce skill  +  shadcn/ui  +  GSAP                         │
│  Implémentation  →  Validation automatisée  →  Livraison            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Workflow Complet

### ⚡ Phase 0 — Orientation Design (Obligatoire, avant tout code)

**Ne jamais créer un DESIGN.md de zéro. Nourrir sa création depuis les deux sources.**

#### 0a. Référence visuelle — getdesign.md

Choisir le site dont l'esthétique est la plus proche du projet. Télécharger son DESIGN.md :

```bash
npx getdesign@latest add <brand>
```

Exemples selon le type de projet :

| Type de projet | Référence recommandée | Commande |
|---|---|---|
| Fintech, paiement | Stripe | `npx getdesign@latest add stripe` |
| Dev tool, infra | Vercel | `npx getdesign@latest add vercel` |
| SaaS minimaliste | Linear | `npx getdesign@latest add linear` |
| Workspace, docs | Notion | `npx getdesign@latest add notion` |
| Open-source, API | Supabase | `npx getdesign@latest add supabase` |
| E-commerce luxe | Ferrari | `npx getdesign@latest add ferrari` |
| Crypto, trading | Binance | `npx getdesign@latest add binance` |
| IA, chatbot | Cursor | `npx getdesign@latest add cursor` |

Le fichier `DESIGN.md` de référence est déposé à la racine. **C'est une inspiration, pas un copier-coller.** En extraire les tokens pertinents (couleurs, typo, rayons, ombres) qui correspondent au projet.

#### 0b. Intelligence design — UI/UX Pro Max

Générer le système de design adapté au type de produit :

```bash
python3 scripts\search.py \
  "description du produit" --design-system -p "Nom du projet"
```

Exemples :

```bash
# Application bancaire
python3 scripts\search.py \
  "fintech banking app" --design-system -p "MyBank"

# Plateforme wellness
python3 scripts\search.py \
  "beauty spa wellness booking" --design-system -p "Serenity"

# Dashboard SaaS analytics
python3  scripts\search.py \
  "saas analytics dashboard" --design-system -p "DataFlow"
```

La sortie contient : Pattern de page recommandé, Style prioritaire, Palette, Typographie, Effets clés, Anti-patterns à éviter absolument pour ce secteur.

#### 0c. Fusion → DESIGN.md du projet

Créer le `DESIGN.md` du projet en combinant les deux sources :

- **UI/UX Pro Max → décisions structurelles** : palette sémantique, typographie, pattern de page, anti-patterns sectoriels
- **getdesign.md → affinage stylistique** : tokens précis, rayons, ombres, densité, micro-détails visuels

**Règle de priorité en cas de conflit** : UI/UX Pro Max prime (adapté au secteur), getdesign.md affine la texture visuelle.

Utiliser `templates/design-md-template.md` comme structure de base.

---

### Phase 1 — Contrat de Design (Le "Cerveau")

Le `DESIGN.md` final doit être complet avant tout code. Exigences minimales :

- **Palette** : 4–8 couleurs avec rôles sémantiques (`Primaire`, `Fond`, `Texte`, `Accent`, `Succès`, `Danger`)
- **Typographie** : Maximum 2 polices (display + body), Google Fonts uniquement
- **Espacements** : Tous en multiples de 8px
- **Animations** : ≤ 400ms, mention de `prefers-reduced-motion` obligatoire
- **Composants** : Maximum 3 variantes par type

Valider avant de continuer :

```bash
python3 scripts/validate_design.py DESIGN.md
```

Ne pas passer à la phase suivante si des erreurs sont signalées (incluant le contraste WCAG AA).

---

### Phase 2 — Implémentation Structurelle (Le "Corps")

- **Primitives** : Exclusivement les composants **shadcn/ui** (Button, Card, Dialog, Input, Table...). Interdiction de recréer ces blocs depuis des `div` brutes.
- **Variables** : Configurer `globals.css` uniquement via les variables CSS définies dans le `DESIGN.md` (`--primary`, `--background`, `--radius`...).
- **Grille** : Classes Tailwind multiples de 8 uniquement (`p-2`, `p-4`, `p-8`, `gap-4`, `gap-8`). Interdiction absolue des valeurs arbitraires (`p-[11px]`, `mt-[13px]`).

---

### Phase 3 — Dynamisme avec GSAP (L'"Âme")

Voir `references/gsap-best-practices.md`.

- **shadcn/ui + Tailwind** gèrent les états natifs (hover, focus, disabled).
- **GSAP** uniquement pour l'orchestration : entrées échelonnées (staggers), effets au scroll (ScrollTrigger).
- Toutes les durées respectent les timings du `DESIGN.md` (≤ 400ms).

---

### Phase 4 — Inspection Visuelle (Les "Yeux" via MCP Playwright) — CRITIQUE

Une tâche n'est jamais terminée tant qu'elle n'a pas été inspectée visuellement.

```bash
python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
```

Inspecte sur **4 breakpoints** (375 / 768 / 1280 / 1920px). Corriger immédiatement si :

- **Artefacts IA** : emojis, stickers, icônes décoratives non demandées
- **Logos inventés** : placeholders graphiques (`logo-placeholder`, `your-logo`, `brandname`)
- **Géométrie bancale** : espacements non-multiples de 8px

Boucle de validation : corriger → relancer l'audit → répéter jusqu'à zéro défaut.

---

### Phase 5 — Validation Automatisée (Obligatoire avant livraison)

Exécuter dans cet ordre :

```bash
# 1. Détection des antipatterns IA dans le code source
python3 scripts/detect_ai_slop.py --design DESIGN.md --code ./client/src

# 2. Audit de la grille 8px sur tous les fichiers CSS/TSX/JSX
python3 scripts/audit_spacing.py --path ./client/src

# 3. Validation finale du contrat DESIGN.md (inclut contraste WCAG AA)
python3 scripts/validate_design.py DESIGN.md
```

Si un script renvoie une erreur → corriger immédiatement en consultant `references/antipatterns-guide.md` → relancer. **Tout rendu non validé par les 3 scripts est rejeté.**

---

## Règles d'Hygiène Visuelle (Non-négociables)

- **Moins mais mieux** : Tout élément visuel sans fonction claire (bordure, ombre, dégradé) est supprimé.
- **Grille 8px stricte** : `p-2` `p-4` `p-6` `p-8` `gap-4` `gap-8`. Jamais de `p-[11px]`.
- **Logo textuel** : Si aucun asset logo fourni → texte stylisé uniquement (`font-bold tracking-tight uppercase`). Jamais de placeholder graphique improvisé.
- **Contraste WCAG AA** : Texte/Fond minimum **4.5:1**. Éléments UI minimum **3.0:1**.

---

## Ressources

| Fichier | Rôle |
|---|---|
| `templates/design-md-template.md` | Structure du DESIGN.md à remplir |
| `templates/design-system.css` | Variables CSS prêtes à personnaliser |
| `references/design-md-spec-v2.md` | Spec complète du format DESIGN.md |
| `references/antipatterns-guide.md` | Exemples concrets ❌ vs ✅ |
| `references/gsap-best-practices.md` | Guide GSAP |
| `scripts/validate_design.py` | Validation DESIGN.md + WCAG AA |
| `scripts/detect_ai_slop.py` | Détection antipatterns dans le code |
| `scripts/audit_spacing.py` | Audit grille 8px |
| `scripts/visual_audit.py` | Audit visuel Playwright (4 breakpoints) |
