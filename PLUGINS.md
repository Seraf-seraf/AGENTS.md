# Skills и plugins

Актуальность рекомендаций: 26 сентября 2026 года.

## Baseline

| Компонент | Состояние | Назначение | Накладные расходы |
|---|---|---|---|
| GitHub plugin | включить | PR, CI, review comments и публикация по запросу | Низкие в простое; средние при чтении PR и Actions |
| Browser plugin | включить | Проверка изменённого frontend и локальных web-сценариев | Низкие в простое; высокие при длинном цикле snapshots |
| Figma plugin | включить | Design-to-code и редкие frontend-задачи | Метаданные нескольких skills; основные расходы только при вызове |
| OpenAI Docs skill | использовать встроенный | Актуальные настройки Codex и API | Поиск и чтение документации только при срабатывании |
| Личный skills-only plugin | установить | Архитектура, backend-проверка, CI/CD и Ansible, русские commits | Четыре коротких описания skills; body загружается по необходимости |
| Computer Use plugin | выключить | Управление Windows-приложениями | Может создавать длинные визуальные циклы; Browser обычно достаточно |

В `.codex/config.toml` зафиксировано включение уже установленных GitHub, Browser и Figma и отключение Computer Use. Запись `enabled = true` не устанавливает отсутствующий plugin.

## Устанавливать по проекту

| Plugin | Когда устанавливать | Почему не baseline |
|---|---|---|
| Codex Security | Перед отдельным security review или регулярным аудитом | Глубокий scan — самостоятельная дорогая задача, а не обязательный post-step |
| Sentry | Проект уже отправляет события в Sentry | Без реальных данных connector не нужен |
| PostHog | Проект использует PostHog и нужна продуктовая аналитика | Не относится к обычной backend-разработке |
| Cloudflare | Код развёртывается в Cloudflare | Инфраструктурно-специфичен |
| Vercel | Frontend или API развёртываются в Vercel | Инфраструктурно-специфичен |
| Supabase | Supabase является частью проекта | Не заменять им обычный PostgreSQL по умолчанию |
| Neon Postgres | База проекта размещена в Neon | Нужен только для соответствующей инфраструктуры |
| Slack, Notion, Google Drive | Задача требует приватного рабочего контекста | Требуют авторизации и передают данные внешнему сервису |

## Не включать глобально

- специализированные ML/Ultralytics plugins без реальной работы с ними;
- plugins с обязательным cross-model review на каждую задачу;
- hooks, автоматически форматирующие весь репозиторий или блокирующие обычные Git-операции;
- дублирующие browser/computer-use инструменты;
- connector plugins «на будущее» без подключённого сервиса.

## Установка plugins

Plugins устанавливаются через каталог Codex в desktop app или через `/plugins` в интерактивном Codex CLI. После установки нужно начать новую сессию. Конфигурация в этом репозитории управляет только состоянием уже установленного plugin; она не заменяет установку и OAuth.

## Личный skills-only plugin

Каталог `.agents/` является корнем portable plugin: `.agents/plugin.json` задаёт identity, а `.agents/skills/` содержит workflows. MCP этому plugin не нужен.

В пакет входят:

- `review-backend-architecture` — архитектурный review и проектирование;
- `verify-backend-change` — релевантные тесты, локальные данные и ручной GraphQL-запрос;
- `prepare-russian-commit` — Conventional Commit на русском без автоматического push;
- `ci-cd-ansible` — CI/CD, deployment, release, rollback и Ansible.

Для загрузки в ChatGPT нужно архивировать содержимое `.agents/`, а не сам каталог: в корне `.zip`, `.tar.gz` или `.tgz` должны находиться `plugin.json` и `skills/`. Те же skills остаются пригодны для standalone-установки в `~/.agents/skills`.
