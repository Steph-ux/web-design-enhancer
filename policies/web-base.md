# Policy profile: web-base

Selects mechanical checks for general web UIs. Does **not** choose aesthetics.

## Checks (default)

- slop.static (blocking, safety_truth)
- a11y.static (blocking, accessibility_critical)
- spacing.grid (blocking, functional_quality)
- style.uniqueness (blocking when score exceeds template threshold)
- beauty.score (major when below floor)
- gestures.archetype (blocking when archetype committed)
- layout.browser (blocking when browser capability + URL present)

## Waivers

Not allowed: safety_truth, accessibility_critical.  
Allowed with record: anti_template_heuristic, taste_preference.
