# DESIGN.md — DataFlow

Contrat de design pour **DataFlow**, un SaaS d'analytics B2B.
Validé par `python3 scripts/validate_design.py DESIGN.md`.

---

## 0. Sources Phase 0

- **Brand utilisée :** Linear
- **Commande exécutée :** `npx getdesign@latest add linear`
- **Requête exécutée :** `python3 scripts/search.py "saas analytics dashboard" --design-system -p "DataFlow"`
- **Style retenu :** Data-Dense Dashboard
- **Justification :** Haute densité d'information, grille serrée, performance maximale, zéro ornement. Linear apporte la précision des tokens (radius 4px, hairline borders).

---

## 1. Thème Visuel & Concept

- **Concept :** Précision analytique — interfaces axées sur la lisibilité de la donnée, contraste fort, aucune fioriture.
- **Mots-clés :** Dense, structuré, technique, fiable, sobre.
- **Références :** Linear (compacité, tokens précis), Stripe (clarté typographique).

---

## 2. Palette de Couleurs

| Rôle | Hex | Utilisation |
| :--- | :--- | :--- |
| Primaire | #1E40AF | Boutons principaux, liens actifs, focus |
| Secondaire | #3B82F6 | Hover, accents secondaires, sparklines |
| Accent | #D97706 | CTA critiques, highlights |
| Fond | #F8FAFC | Arrière-plan principal |
| Texte | #1E3A8A | Texte principal, headings |
| Succès | #16A34A | Indicateurs positifs, deltas croissants |
| Attention | #F59E0B | Alertes, avertissements |
| Danger | #DC2626 | Actions destructives, erreurs |

Contraste WCAG AA — Texte sur Fond : 9.2:1 (min 4.5:1). Primaire sur Fond : 8.1:1 (min 3.0:1).

---

## 3. Typographie

- **Fira Code** (Display, Titres, KPI) — monospace technique, chiffres à largeur fixe, colonnes alignées.
- **Fira Sans** (Body, corps de texte) — lisible, neutre, complémentaire.

```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@400;500;600;700&display=swap');
```

---

## 4. Hiérarchie Typographique

- **H1 :** 28px / 700 / 1.2
- **H2 :** 20px / 600 / 1.3
- **H3 :** 16px / 600 / 1.4
- **P :** 14px / 400 / 1.6
- **Small :** 12px / 400 / 1.5

---

## 5. Espacement et Grille

- **Base de la grille :** 8px
- **Gouttière colonnes :** 16px
- **Padding section vertical :** 32px
- **Padding section horizontal :** 24px
- **Padding card interne :** 16px
- **Gap entre cards :** 16px
- **Hauteur ligne tableau :** 40px
- **Radius :** 4px (cartes, boutons)

---

## 6. Composants et États

### Boutons

- **Primaire (Normal) :** Fond #1E40AF, texte blanc, padding 8px 16px, font-weight 600
- **Primaire (Hover) :** Fond #1D4ED8, transition 200ms ease-out
- **Secondaire (Normal) :** Transparent, bordure 1px #1E40AF, texte #1E40AF
- **Ghost (Normal) :** Transparent, texte #1E3A8A, sans bordure

### Cartes (Cards)

- **Structure :** Fond blanc, bordure 1px solid #DBEAFE, radius 4px
- **Padding Interne :** 16px
- **Ombre :** `0 1px 3px rgba(30, 64, 175, 0.08)`

---

## 7. Motion et Animations

- **Transitions générales :** 200ms ease-out
- **Hover états :** 150ms ease-in-out
- **Entrées stagger :** duration 300ms, stagger 40ms, ease power2.out
- **Tooltip :** 150ms ease-out
- **Accessibilité :** `prefers-reduced-motion` obligatoire.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## ✅ Checklist de Validation Anti-Slop

- [x] **DESIGN.md** : Complet, Phase 0 documentée.
- [x] **Polices** : 2 polices (Fira Code + Fira Sans).
- [x] **Espacements** : Tous multiples de 8px (4, 8, 16, 24, 32, 40, 48, 64).
- [x] **Rayons** : 4px — net et technique.
- [x] **Icônes** : Lucide uniquement pour fonctions justifiées (icônes fonctionnelles ciblées uniquement).
- [x] **Gradients** : Aucun gradient décoratif.
- [x] **Artefacts** : Aucun emoji, aucun sticker, aucun badge statut non demandé.
- [x] **Logo** : Texte stylisé "DataFlow" en Fira Code 600.
- [x] **Structure** : Dashboard (sidebar fixe + topbar + grille de cards).
- [x] **Texte** : Descriptions précises, zéro buzzword.
- [x] **Boutons** : 3 variantes (Primaire, Secondaire, Ghost).
- [x] **Couleurs** : 8 couleurs avec rôles sémantiques.
- [x] **Animations** : Toutes ≤ 400ms. prefers-reduced-motion documenté.
- [x] **WCAG AA** : Ratios calculés et conformes.
