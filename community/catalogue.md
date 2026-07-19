# Model Modding Catalogue

This catalogue is a human-readable entry point to the packages currently included in the repository. Manifests remain the source of truth for version, compatibility, dependencies and maturity.

## Mods

| Mod | Category | Status | Purpose | Used by |
| --- | --- | --- | --- | --- |
| [Inquisitive Strategist](../mods/personality/inquisitive-strategist/) | Personality | Experimental | Clarifies decisions, challenges assumptions and explores alternatives. | Product Strategy Copilot |
| [Socratic Teacher](../mods/personality/socratic-teacher/) | Personality | Experimental | Guides learners toward understanding while avoiding unnecessary interrogation. | Research Learning Companion |
| [Citation Guardian](../mods/safety/citation-guardian/) | Safety | Experimental | Keeps factual claims traceable and makes uncertainty visible. | Research Learning Companion |

## Recipes

| Recipe | Installed mods | Purpose |
| --- | --- | --- |
| [Product Strategy Copilot](../recipes/product-strategy-copilot/) | Inquisitive Strategist | Supports structured product and strategic decisions. |
| [Research Learning Companion](../recipes/research-learning-companion/) | Socratic Teacher, Citation Guardian | Combines guided learning with source discipline. |

## Maturity meaning

- **Draft:** incomplete and not ready for general testing.
- **Experimental:** usable for testing, with limitations and behaviour still under active evaluation.
- **Community validated:** reviewed and tested by multiple independent contributors.
- **Stable:** versioned, maintained and supported by repeatable evidence.
- **Archived:** no longer maintained or superseded.

A package does not become stable because it is popular. Maturity should change only when compatibility evidence, evaluation results and maintenance ownership justify it.

## Add to the catalogue

New entries are added when a mod or recipe is merged. Contributors should not edit maturity labels here without making the same change in the source manifest and supplying supporting evidence.
