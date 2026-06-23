# Contributing to Hikma Questions

## Structure de dossiers

```
questions/
  <formation-id>/
    metadata.yaml               ← formation (type: formation)
    <category-id>/
      metadata.yaml             ← catégorie (type: category)
      [<subcategory-id>/]
        metadata.yaml           ← sous-catégorie (type: category)
        <question-id>/
          metadata.yaml         ← question (sans champ type)
          fr.md
          ar.md
```

La position dans l'arbre de dossiers **est** la hiérarchie. Le build script la traverse automatiquement.

---

## Ajouter une question

### 1. Choisir la formation et la catégorie

Repérer la formation et le(s) dossier(s) catégorie existants. Créer de nouvelles catégories si nécessaire (voir § Ajouter une catégorie).

### 2. Créer le dossier question

```
questions/<formation>/<category>/[<subcategory>/]<question-id>/
```

Format de l'ID : `{formation-prefix}-{4-digit-number}` — ex. `qcm-kids-islam-0051`, `qcm-din-fitra-0044`.

### 3. Écrire `metadata.yaml`

```yaml
id: qcm-kids-islam-0051
difficulty: easy            # easy | medium | hard
tags:
  - your-tag
tags_by_lang:               # optionnel : tags spécifiques par langue
  fr:
    - votre-tag-fr
  ar:
    - وسمك-بالعربية
languages:
  - fr                      # lister toutes les langues fournies
source: null                # optionnel : "Titre du livre, p.42"
created_at: 2026-06-23      # date du jour
```

### 4. Écrire les fichiers langue (`{lang}.md`)

Un fichier par langue déclarée dans `metadata.yaml`. Template :

```markdown
# Question

Texte de la question ici.

## Choices

- Option A
- Option B
- Option C
- Option D

## Answer

2

## Explanation

Pourquoi cette réponse est correcte.
```

Règles :
- `Answer` doit être un **entier 1-based** (1 = premier choix).
- Au moins 2 choix ; 4 est la valeur recommandée.
- `Explanation` est obligatoire.

### 5. Valider et builder

```bash
python3 scripts/validate.py   # vérifie la structure
python3 scripts/build.py      # rebuild dist/
```

Le hook pre-commit exécute les deux étapes automatiquement.

---

## Ajouter une catégorie

Créer un dossier avec un `metadata.yaml` :

```yaml
type: category
id: my-category
title_fr: Ma catégorie
title_ar: فئتي
title_en: My category
order: 3                    # optionnel, pour trier (sinon tri alphabétique)
```

---

## Ajouter une formation

Créer un dossier à la racine de `questions/` avec un `metadata.yaml` :

```yaml
type: formation
id: my-formation
title_fr: Ma formation
title_ar: تكويني
title_en: My formation
description_fr: Description courte
description_ar: وصف قصير
description_en: Short description
languages:
  - fr
  - ar
```

---

## Modifier une question existante

Éditer directement le fichier `{lang}.md` concerné. Aucun champ de version à incrémenter.

## Mettre à jour une traduction

Ajouter ou mettre à jour le fichier `{lang}.md` et s'assurer que `metadata.yaml → languages` inclut le code langue.
