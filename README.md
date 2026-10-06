# Персональная конфигурация OpenAI Codex

Компактная конфигурация для backend-разработки и архитектурных задач с периодической работой над frontend. Репозиторий содержит персональные инструкции, экономные настройки Codex и узкий allowlist безопасных команд.

## Состав

- `AGENTS.md` — глобальные инженерные предпочтения.
- `.codex/config.toml` — шаблон пользовательского `~/.codex/config.toml`.
- `.codex/rules/allowlist.rules` — разрешения только для поиска и чтения состояния Git.
- `.agents/plugin.json` — portable manifest личного skills-only plugin.
- `.agents/plugins/marketplace.json` — repo marketplace для установки plugin напрямую из этого репозитория.
- `.agents/skills/` — skills этого plugin и одновременно standalone workflows для Codex, включая специализированный `ci-cd-ansible`.
- `PLUGINS.md` — конкретный baseline и условные plugins.

Глобальный `AGENTS.md` содержит устойчивые общие инженерные правила и короткие указатели. Подробные правила CI/CD и Ansible вынесены в `.agents/skills/ci-cd-ansible/SKILL.md`: они загружаются только для задач про CI/CD, GitLab CI, deployment, release, rollback, Ansible, playbooks, roles и связанную инфраструктуру. Это уменьшает постоянный контекст без потери строгости специализированного процесса.

Для длинной многоэтапной работы или задачи с высокой вероятностью compaction Codex должен создать временный `.codex-task-state.md` в корне workspace. В нём хранятся только цель, acceptance criteria, подтверждённые этапы и решения, изменённые файлы, результаты проверок, blocker и следующий шаг. После compaction state-файл помогает восстановить рабочее состояние, проверить `git status` и релевантный diff и продолжить без повторного исследования завершённых этапов. Для каждой обычной короткой задачи этот файл создавать не следует; после завершения его нужно удалить и не коммитить.

Для многоэтапных задач `AGENTS.md` разделяет контекст и разрешённый scope: общий roadmap не даёт разрешение автоматически выполнять следующие шаги. Каждый пункт явного плана должен иметь отдельную цель, разрешённые действия, исключения и проверяемый stop criterion. После достижения критерия текущего шага агент останавливается, если пользователь не поручил выполнять следующие этапы или весь план.

Codex читает глобальный `~/.codex/AGENTS.md` во всех проектах, а более близкие к рабочей директории `AGENTS.md` дополняют или переопределяют его. Проектный `.codex/config.toml` и правила работают только для доверенного репозитория. Это соответствует [официальному описанию AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [config.toml](https://learn.chatgpt.com/docs/config-file/config-reference) и [rules](https://learn.chatgpt.com/docs/agent-configuration/rules).

## Установка

Не копируйте конфигурацию поверх существующей вслепую. Сначала сохраните текущие файлы или перенесите из них нужные секции plugins, MCP и приложений.

Для глобальной установки из WSL:

```bash
mkdir -p ~/.codex/rules ~/.agents/skills
cp AGENTS.md ~/.codex/AGENTS.md
cp .codex/config.toml ~/.codex/config.toml
cp .codex/rules/allowlist.rules ~/.codex/rules/allowlist.rules
cp -R .agents/skills/. ~/.agents/skills/
```

Команды перезаписывают одноимённые файлы, поэтому сначала сравните их с уже установленной конфигурацией. После изменения rules перезапустите Codex. Для локальных skills в отдельном проекте оставьте их в `<project>/.agents/skills`; Codex обнаружит их без глобального копирования.

### Установка как ChatGPT/Codex plugin

Каталог `.agents/` является корнем portable skills-only plugin, а `.agents/plugins/marketplace.json` публикует его как repo marketplace.

Добавить marketplace из репозитория:

```bash
codex plugin marketplace add Seraf-seraf/AGENTS.md --ref main
```

Проверить подключённые marketplaces:

```bash
codex plugin marketplace list
```

После добавления marketplace установите `seraf-backend-engineering` через каталог plugins Codex. Если repo marketplace недоступен в используемом клиенте, остаётся portable-вариант: архивировать содержимое `.agents/`, чтобы `plugin.json` и `skills/` лежали в корне архива.

PowerShell из корня репозитория:

```powershell
Push-Location .agents
Compress-Archive -Path plugin.json,skills -DestinationPath ..\seraf-backend-engineering.zip -Force
Pop-Location
```

Ожидаемая структура архива:

```text
seraf-backend-engineering.zip
├── plugin.json
└── skills/
```

## Почему выбран такой config

- `gpt-6-luna` используется как основной исполнитель, модель для `/review` и default model для subagents, чтобы поведение между реализацией и ревью было предсказуемым.
- Reasoning effort намеренно не фиксируется в `config.toml`: уровень выбирается под конкретную задачу или сессию.
- `approvals_reviewer = "user"` — исключает отдельный reviewer-subagent на каждое eligible approval.
- `workspace-write` + сеть — позволяет обычную разработку и сверку документации, сохраняя границу workspace.
- не более двух subagents — ограничивает параллельный расход; `AGENTS.md` требует по умолчанию работать одним агентом.
- compaction при `240000` и scope `total` оставлен как консервативный порог для длинных сессий. Это operational limit для управления контекстом, а не финансовый или модельный hard limit.

`model_auto_compact_token_limit` запускает compaction истории, но не гарантирует верхнюю границу размера отдельного запроса или расходов: системный prefix, результаты инструментов и другие части контекста также занимают место.

## Skills и plugins

Skills используют progressive disclosure: сначала в контекст попадают имя и краткое описание, а полный `SKILL.md` читается только при срабатывании. Официальная документация ограничивает исходный список skills 2% context window или 8 000 символами при неизвестном окне. Поэтому важнее ограничивать фактические вызовы тяжёлых workflows, чем удалять несколько полезных skills. См. [Build skills](https://learn.chatgpt.com/docs/build-skills).

Инфраструктурные правила не дублируются в глобальном `AGENTS.md`: при релевантной задаче загружается `ci-cd-ansible`, а для остальных задач постоянный контекст остаётся короче.

Рекомендуемый baseline:

- GitHub — PR, review comments, CI и публикация по явному запросу;
- Browser — только для реальной UI/E2E-проверки;
- OpenAI Docs — для актуальных настроек Codex и OpenAI API;
- Figma/frontend skills — включать в работу только для UI-задач.

Устанавливать по потребности проекта:

- Codex Security — для отдельного security review, а не на каждую задачу;
- Sentry и PostHog — если проект уже использует соответствующий сервис;
- Cloudflare, Vercel, Supabase или Neon — только при наличии этой инфраструктуры;
- Slack, Notion, Google Drive и календари — для задач, где действительно нужны приватные данные из этих систем.

В `config.toml` зафиксирован baseline уже установленных plugins: GitHub, Browser и Figma включены, Computer Use выключен. Эти записи не устанавливают bundles и не выполняют авторизацию. Полная матрица решений находится в `PLUGINS.md`; специализированный plugin не стоит подключать глобально только из-за одного возможного сценария.

## Граница allowlist

Автоматически разрешены только `rg --files` и несколько инспекционных подкоманд Git. Обычный поиск `rg` остаётся внутри sandbox: широкий внешний allowlist разрешил бы опасный `--pre` с запуском произвольного preprocessor. В allowlist также намеренно не входят:

- `python -c`, shell-интерпретаторы и package-manager scripts — выполняют произвольный код;
- `make`, тесты и линтеры — выполняют код репозитория;
- Docker — обращается к общему daemon и может менять состояние;
- `git fetch`, `add`, `commit`, `push`, `reset`, `clean` — используют сеть или изменяют Git/рабочие файлы;
- `gh` — обращается к удалённым приватным данным.

Такие команды остаются доступны в sandbox либо требуют обычного пользовательского approval при выходе за его границы.
