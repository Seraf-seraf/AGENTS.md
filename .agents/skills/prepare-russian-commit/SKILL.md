---
name: prepare-russian-commit
description: Prepare or create a Conventional Commit with a concise Russian description based on the actual Git diff. Use only when the user explicitly asks to draft a commit message, create a commit, or split changes into commits. Preserve unrelated work, verify the intended scope, omit AI attribution, and never push unless separately requested.
---

# Prepare Russian Commit

Подготавливать коммит только по явному запросу пользователя.

## Изучить изменения

1. Проверить `git status`, staged diff и unstaged diff.
2. Определить логическую причину и contract delta, а не перечислять файлы или повторять формулировку задачи.
3. Сопоставить implementation, tests, schema, config, generated artifacts и docs, относящиеся к одному поведению.
4. Отделить пользовательские и несвязанные изменения. Не включать их в staging и не откатывать.
5. Если запрошен реальный коммит, убедиться, что релевантные проверки выполнены или явно сообщить, чего не удалось проверить.

## Определить границы коммита

- Один коммит должен иметь одну семантическую причину изменения, которую можно закончить фразой «чтобы …» без союза между независимыми целями.
- Реализацию и регрессионный тест одного поведения держать вместе.
- Разделять независимые fixes, API/config rename, topology/security change, dependency/build change, formatting и cleanup.
- Не маскировать behavior change типом `refactor`. `refactor` допустим, только если неизменны наблюдаемый результат, errors, данные, API, configuration contract и security semantics.
- Если изменение одновременно исправляет дефект и перестраивает код, сначала выделить минимальный behavior fix с тестом, затем отдельный behavior-preserving refactor, если история от этого становится понятнее.
- Перед staging перечислить точные files или hunks каждого будущего коммита и проверить, что ни один файл не содержит смешанных причин.

## Сформировать сообщение

Использовать формат:

```text
type(scope): краткое действие на русском
```

- Выбирать из `feat`, `fix`, `refactor`, `test`, `docs`, `build`, `ci`, `chore`, `perf`.
- Использовать scope только когда он уточняет область изменения.
- Subject, состоящий только из типа — `fix`, `chore` или `refactor`, — запрещён.
- Subject должен называть изменённый контракт или компонент и наблюдаемый результат, а не действие над файлами.
- Описывать результат в повелительной или инфинитивной форме, без точки в конце.
- Добавлять body для причины, источника требования, существенного компромисса, миграции, operational limitation или причины отказа от альтернативы.
- В body не пересказывать diff; объяснять, почему изменение понадобилось и какие invariants сохранены.
- Добавлять `BREAKING CHANGE:` только при реальном нарушении совместимости и описывать migration path.
- Не добавлять подписи, co-author или упоминания об участии ИИ.

Примеры:

```text
feat(payments): добавить идемпотентную обработку
fix(api): сохранить conflict error при повторном запросе
refactor(worker): централизовать проверку доступа без смены поведения
ci(tests): назначить integration suite runner с Docker
```

## Создать коммит

Если пользователь попросил именно коммит:

1. Добавить в staging только относящиеся к одной причине файлы или hunks.
2. Проверить `git diff --cached --check` и перечитать staged diff как самостоятельный changeset.
3. Создать один логический коммит, если пользователь не запросил другое разбиение.
4. Повторно проверить status и сообщить hash, точное сообщение и оставшиеся unstaged/untracked изменения.
5. Не выполнять push, rebase, reset, amend или изменение истории без отдельного явного запроса.

Если пользователь попросил только сообщение, не изменять index или историю Git.
