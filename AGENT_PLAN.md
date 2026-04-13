# Plan — Architecture Agent Hybride Spark

## Objectif

Transformer Spark en agent hybride unifié : outils manuels (remind, note, todo…)
et outils IA (vault, question libre) accessibles depuis un registre commun, avec
routage automatique en langage naturel à 3 niveaux (regex → agent léger → agent complet).

---

## Statut des étapes

- [x] **Étape 1** — `commands/registry.py` : registre unifié de tous les outils
- [x] **Étape 2** — `commands/ai.py` : agent loop universel + working memory
- [x] **Étape 3** — `commands/spark.py` : fast path regex + agent loop direct
- [x] **Étape 4** — `bot.py` : simplification (plus de redirect)
- [x] **Étape 5** — `result.py` : suppression du champ `redirect` devenu inutile

---

## Architecture finale

```
Input utilisateur
    │
    ├── /cmd   →  dispatch direct  →  handler command  →  Result
    │
    └── texte  →  spark.handle()
                    │
                    ├── 1. Regex fast path (0 tokens)
                    │      patterns : "msg, Xmin", "note que ...", "ajoute X à Y"
                    │      → registry.run_tool() directement
                    │
                    ├── 2. Agent loop (N tokens, multi-steps)
                    │      AI reçoit tous les outils du registre
                    │      → appelle set_reminder / save_note / add_todo_item / ...
                    │
                    └── 3. Fallback : /ai <texte> si aucun outil appelé
```

```
/ai <question>
    │
    └── _run_turn()
          │
          └── agent_loop(ctx, system, history)
                AI reçoit TOUS les outils (core + vault si activé)
                Répond en texte OU appelle des outils OU les deux
```

---

## Fichiers modifiés

### `commands/registry.py` (NOUVEAU)
Registre central de tous les outils :
- `_CORE_REGISTRY` : remind, note, todo (×5), weather, quote
- `_VAULT_REGISTRY` : list/read/write vault notes
- `get_anthropic_tools(ctx)` → liste des schemas Anthropic (vault conditionnel)
- `get_openai_tools(ctx)` → liste des schemas OpenAI-compatible (Groq/GLM)
- `run_tool(name, args, ctx)` → dispatcher → (result_text, action_label)

### `commands/ai.py` (MODIFIÉ)
- **Supprimé** : `_VAULT_TOOLS_ANTHROPIC`, `_VAULT_TOOLS_GROQ`, `_run_tool`,
  `_chat_with_vault`, `_anthropic_vault_loop`, `_groq_vault_loop`, `_glm_vault_loop`
- **Ajouté** : `_get_working_memory(ctx)`, `agent_loop(ctx, system, messages)`,
  `_anthropic_agent_loop()`, `_openai_agent_loop()`
- **Modifié** : `_build_system` injecte le working memory, `_dispatch` appelle
  toujours `agent_loop`, `_run_turn` sans `vault_active`
- **Corrigé** : bug `_compact` (summary non dépaquetée depuis le tuple)

### `commands/spark.py` (MODIFIÉ)
- **Ajouté** : `_REMIND_RE`, `_NOTE_RE`, `_TODO_ADD_RE` + `_try_regex()`
- **Modifié** : `handle()` — regex d'abord, puis `agent_loop`, puis fallback `/ai`
- **Supprimé** : `Result.dispatch()`, plus de re-dispatch via bot.py

### `bot.py` (MODIFIÉ)
- Routage langage naturel simplifié : plus de `redirect`, `spark.handle()` retourne
  directement un `Result.success()`

### `result.py` (MODIFIÉ)
- Supprimé : champ `redirect` et méthode `dispatch()`

---

## Comportement attendu

```
› rappelle-moi de boire dans 20min
⏰ Rappel : boire dans 20min   ← regex fast path, 0 tokens

› ajoute du lait à ma liste courses
✅ Todo : lait → courses       ← regex fast path, 0 tokens

› rappelle-moi de faire les courses et ajoute pain à la liste
⏰ Rappel : faire les courses dans ...   ← agent loop, 2 tool calls
✅ Todo : pain → courses
Spark : C'est fait !

› /ai qu'est-ce que j'ai noté sur Python ?
📖 Lecture : Python.md         ← agent loop avec vault
Spark : Voici ce que tu as noté…
```

---

## Reprendre le travail

Si le travail est interrompu, vérifier dans cet ordre :

1. `git status` — voir quels fichiers sont modifiés
2. Vérifier le statut des étapes ci-dessus
3. Lancer `pytest` pour voir les tests qui passent/échouent
4. Tester manuellement : `spark` → taper du texte libre + `/ai <question>`

Les tests à écrire (non implémentés) :
- `tests/test_registry.py` : chaque tool handler retourne bien (str, str)
- `tests/test_spark_router.py` : regex patterns + agent fallback
- `tests/test_agent_loop.py` : mock API, vérifie que les tools sont appelés

---

## Décisions d'architecture

| Décision | Raison |
|---|---|
| `agent_loop` toujours actif pour `/ai` | L'IA n'appelle des tools que si besoin — overhead minimal |
| Vault tools conditionnels dans le registre | Évite que le routeur accède au vault sans intention explicite |
| Regex avant agent pour le routeur | ~60% des cas courants sans coût token |
| `_chat()` conservé | Utilisé par compact et le router interne (prompt court, pas de tools) |
| Vault tools = core tools dans la même boucle | Simplifie le code, une seule boucle agent par provider |
