---
name: verify-backend-change
description: Verify backend business-logic changes with focused tests, type checks, changed-file linting, isolated database data, and a manual GraphQL operation when applicable. Use after changing an API, service, repository, migration, database query, GraphQL resolver or schema, worker, integration, or other backend behavior. Do not create persistent seeders unless requested.
---

# Verify Backend Change

Проверять изменённое поведение минимальным достаточным набором действий и оставлять воспроизводимый сценарий ручной проверки.

## Определить область проверки

1. Изучить итоговый diff, manifest и lock-файлы, локальные инструкции и существующие цели `Makefile`.
2. Сформулировать contract delta: источник истины, наблюдаемое поведение, inputs/outputs, units, boundaries, errors, authorization и compatibility.
3. Классифицировать изменение: behavior fix/feature, behavior-preserving refactor, public contract, config, dependency, data/migration или infrastructure. Не принимать название коммита за доказательство типа изменения.
4. Сопоставить изменённые ветви бизнес-логики с существующими тестами, публичными контрактами и всеми producer/consumer.
5. Начать с самой узкой проверки и расширять её только соразмерно риску.

## Зафиксировать регрессию или поведение

- Для дефекта сначала получить падающий тест или воспроизводимый scenario, который отличает ошибочное поведение от правильного.
- Для рефакторинга сначала выполнить characterization tests и убедиться, что expected output, errors и side effects не меняются.
- Не менять ожидаемый результат теста только потому, что новая реализация возвращает другое значение. Сначала подтвердить изменение требования или контракта.
- Реализацию и регрессионный тест одного поведения проверять вместе; независимые изменения не маскировать одним зелёным suite.

## Выполнить проверки

- Использовать штатные команды проекта; не создавать временный runner без необходимости.
- Запустить релевантные unit или integration tests, затем type check или build, если изменение зависит от них.
- Для алгоритмического лимита проверить `N-1`, `N`, `N+1`, пустой input, oversized элемент, пересечение внутренних границ, повтор и детерминированность. Указывать единицы измерения в test names или test data.
- Для lifecycle проверить разрешённые и запрещённые transitions, concurrent call, replay, timeout/cancel и failure до и после первого side effect.
- Для error mapping проверить outward code/status/retryability для known domain/conflict errors отдельно от unknown infrastructure failure.
- Для authorization проверить allow и deny по каждой затронутой action, отсутствие обхода через соседний endpoint и привязку grant/context к actor, resource и action.
- Для public API, GraphQL или message schema найти canonical definition и проверить совместимость scalar/type, nullability, enum, names и consumer serialization.
- Для config/env rename найти все readers, writers, examples, deployment templates и docs. Отдельно проверить, что rename не изменил значение, endpoint, topology или security semantics.
- Для новой runtime dependency проверить manifest, lock-file, production package/image, фактический entrypoint и запуск с production-only dependencies.
- Для внешнего сервиса или offline asset проверить preflight и отличить unavailable environment от application defect.
- Для логирования проверить наличие безопасного structured context и отсутствие credentials, secrets, необезличенного пользовательского текста и полного external payload.
- Проверять path, cwd, symlink semantics, permissions и environment в том context, где реально исполняется код, а не только в локальном shell.
- Запускать formatter и lint только для изменённых файлов или строк, когда инструмент это поддерживает.
- Не исправлять и не форматировать несвязанный код.
- Если падение существовало до изменения, подтвердить это и отделить его от новой регрессии.
- Если найден дефект текущего изменения и задача включает реализацию, исправить его и повторить проверку; иначе только сообщить о нём.

## Проверить данные

Для логики, зависящей от БД:

1. Использовать только изолированную локальную или test БД.
2. Создать минимальные временные данные через уже существующий API, factory, fixture-механизм или точный SQL.
3. Проверить каноническое business field и пограничные записи, которые surrogate-фильтр по времени, статусу или косвенному признаку мог бы ошибочно исключить.
4. Для stateful операции проверить итоговое состояние всех затронутых записей после success, conflict, timeout и partial failure.
5. Не изменять shared, staging или production БД без отдельного явного запроса.
6. Не добавлять постоянный seeder или fixture только ради разовой проверки.
7. Удалить временные данные, если они не откатываются транзакцией или сбросом test-окружения.

Если окружение недоступно, подготовить точные входные данные и команды, но не утверждать, что проверка выполнена.

## Проверить test topology

- Убедиться, что изменённый тест входит хотя бы в один обязательный suite и не попадает случайно в несколько одинаковых suites.
- Если suite требует БД, containers, browser или внешнюю сеть, проверить capability назначенного runner.
- Не считать release защищённым тестом, который больше не находится в gate graph.
- Не отключать или исключать падающую обязательную suite ради зелёного pipeline без явного risk acceptance, срока и компенсирующей проверки.

## Подготовить ручную GraphQL-проверку

Если задача затрагивает GraphQL, привести в финальном ответе готовый `query` или `mutation` и отдельный JSON с variables. Использовать реальные имена и types из схемы, проверив их в canonical definition; не придумывать поля и scalar.

## Отчитаться

Указать:

- какой contract delta проверен;
- какие boundary, failure и replay scenarios проверены;
- какие команды действительно выполнены и их результат;
- какие данные использованы;
- какие producer/consumer и production artifacts проверены;
- GraphQL operation для ручной проверки, когда применимо;
- непроверенные ограничения, unavailable prerequisites и существующие падения.
