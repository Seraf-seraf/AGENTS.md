---
name: prepare-russian-commit
description: Prepare or create a Conventional Commit with a concise Russian description based on the actual Git diff. Use only when the user explicitly asks to draft a commit message, create a commit, or split changes into commits. Preserve unrelated work, verify the intended scope, omit AI attribution, and never push unless separately requested.
---

# Prepare Russian Commit

Подготавливать коммит только по явному запросу пользователя.

## Изучить изменения

1. Проверить `git status`, staged diff и unstaged diff.
2. Определить логическую причину изменения, а не перечислять изменённые файлы.
3. Отделить пользовательские и несвязанные изменения. Не включать их в staging и не откатывать.
4. Если запрошен реальный коммит, убедиться, что релевантные проверки выполнены или явно сообщить, чего не удалось проверить.

## Сформировать сообщение

Использовать формат:

```text
type(scope): краткое действие на русском
```

- Выбирать из `feat`, `fix`, `refactor`, `test`, `docs`, `build`, `ci`, `chore`, `perf`.
- Использовать scope только когда он уточняет область изменения.
- Описывать результат в повелительной или инфинитивной форме, без точки в конце.
- Добавлять body только для причины, существенного компромисса или нетривиальной миграции.
- Добавлять `BREAKING CHANGE:` только при реальном нарушении совместимости.
- Не добавлять подписи, co-author или упоминания об участии ИИ.

Примеры:

```text
feat(payments): добавить идемпотентную обработку
fix(api): исправить проверку прав пользователя
refactor(worker): упростить повторную обработку событий
```

## Создать коммит

Если пользователь попросил именно коммит:

1. Добавить в staging только относящиеся к задаче файлы или hunks.
2. Создать один логический коммит, если пользователь не запросил другое разбиение.
3. Повторно проверить status и сообщить hash и точное сообщение.
4. Не выполнять push, rebase, reset, amend или изменение истории без отдельного явного запроса.

Если пользователь попросил только сообщение, не изменять index или историю Git.
