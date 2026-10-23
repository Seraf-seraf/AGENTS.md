# Примеры разделения подготовки и выпуска

Читать при выборе способа доставки. Это небольшие фрагменты для конкретных условий, а не шаблон нового framework. Имена, пути и инструменты брать из проекта; существующие Ansible/Helm deployment не переносить на другую платформу ради соответствия примеру.

## Подготовка окружения Ansible

Условия: Linux-хост, рабочие SSH/become; Docker и Compose устанавливает существующий bootstrap. Нужно подготовить пользователя и каталоги приложения. Единственный параметр окружения `app_root` находится в inventory; вложенные пути вычисляются из него.

```yaml
- name: Подготовить каталоги приложения
  hosts: application
  become: true
  tasks:
    - name: Создать группу приложения
      ansible.builtin.group:
        name: app
        system: true

    - name: Создать пользователя приложения
      ansible.builtin.user:
        name: app
        group: app
        system: true
        create_home: false
        shell: /usr/sbin/nologin

    - name: Подготовить приватные каталоги
      ansible.builtin.file:
        path: "{{ app_root }}/{{ item }}"
        state: directory
        owner: app
        group: app
        mode: "0700"
      loop:
        - config
        - data
```

Модули сами приводят ресурсы к нужному состоянию; дополнительные `stat`/`assert` до и после каждой task не нужны. Повторную идемпотентность проверяют при разработке в изолированной среде. Для изменяемого системного конфига используют `copy`/`template`, штатный `validate` и handler по факту изменения. Например, полный nginx-конфиг проверяют через `nginx -t -c %s` до установки, затем выполняют reload.

Управление приложением выполняет существующий deploy-пользователь с уже настроенными правами; служебный `app` не становится SSH-пользователем автоматически. Если файлы монтируются в контейнер, владельца согласуют с его UID/GID. Этот пример не назначает UID, sudo или доступ к Docker по предположению.

## Выпуск готового сервиса через workflow

Условия: один TEST-хост, короткий перерыв допустим. Существующий доверенный SSH-шаг уже настроил ключ и проверку known_hosts. Compose с закреплённым image digest и закрытый конфиг payment уже доставлены штатным способом в `/srv/catalog`; конфиг имеет владельца и права, совместимые с контейнером. БД и роль готовы. Image предоставляет команды `serve`/`migrate`, а Compose — healthcheck приложения. Его настройки интервала и retries вместе с timeout выпуска ограничивают ожидание.

Фрагмент GitHub Actions использует один вход транспорта `DEPLOY_TARGET`, заданный существующим workflow. Команды запускаются на сервере, а последовательностью управляет workflow:

```yaml
concurrency:
  group: catalog-test-deploy
  cancel-in-progress: false

steps:
  - name: Получить выбранный образ payment
    run: ssh "$DEPLOY_TARGET" 'cd /srv/catalog && docker compose pull payment'

  - name: Применить миграции payment
    run: ssh "$DEPLOY_TARGET" 'cd /srv/catalog && docker compose run --rm --no-deps payment migrate'

  - name: Запустить payment и дождаться готовности
    run: ssh "$DEPLOY_TARGET" 'cd /srv/catalog && docker compose up -d --no-deps --wait --wait-timeout 120 payment'
```

`concurrency` относится к deploy job; `steps` — его шаги. Фрагмент вставляют в существующий job. Значение `120` — пример фиксированного бюджета ожидания в секундах; при необходимости настройки его заменяют одним параметром с единицами в имени. `--wait` используется только с версией Compose, которая его поддерживает, и корректным healthcheck: статус running без него не доказывает readiness. Поддержку нужных возможностей устанавливают при подготовке runtime.

Ошибка миграции останавливает job до запуска новой версии. Повторное `migrate` использует журнал мигратора; отдельный `first_install` не нужен. Timeout готовности завершает выпуск ошибкой. Для восстановления применяют принятую процедуру возврата совместимого image и конфига, учитывая уже выполненные миграции. Пример не обещает zero downtime или автоматический откат данных. Если deployment запускается также вне workflow, одной CI concurrency недостаточно — нужен общий механизм сериализации существующих исполнителей.

Конфиг payment приходит готовым либо из шаблона по его контракту; Laravel получает только URL и клиентские credentials. Нет оснований создавать Laravel CLI, воспроизводящий внутреннюю Go-схему, шифрование или подготовку merchant. При отсутствии нужного интерфейса сервиса явно обозначают недостающую операцию, а не прячут её реализацию в доставке.

## Когда сохранить другой подход

- **Ansible уже развёртывает приложение**, в том числе по вызову операторов без CI: конфиг добавляют в существующую роль. Workflow вызывает её; миграции и readiness повторно в workflow не реализуют.
- **Helm управляет workload, migration Job и readinessProbe**: изменение mount остаётся в chart. Не добавляют Ansible-роль или второй migration job для той же операции.
- **Нужен rolling rollout нескольких узлов или непрерывная доступность**: выбирают соответствующую стратегию и её проверки. Это отдельное требование к выпуску, а не обязательное следствие добавления контейнера.

## Основания

- [The Zen of Ansible](https://www.redhat.com/en/blog/the-zen-of-ansible): декларативное состояние, понятные инструкции и соглашения вместо избыточных настроек.
- [Ansible Good Practices](https://redhat-cop.github.io/automation-good-practices/): различать defaults, параметры inventory и наблюдаемое состояние; выбирать рекомендации по масштабу задачи.
- [Официальный пример rolling deployment](https://docs.ansible.com/projects/ansible/latest/playbook_guide/guide_rolling_upgrade.html): Ansible поддерживает полноценную оркестрацию; разделение подготовки и workflow здесь является выбранным подходом по умолчанию.
- [Compose в production](https://docs.docker.com/compose/how-tos/production/): обновление отдельного сервиса через штатный `up --no-deps`.
- [Syntax-check в ansible-lint](https://docs.ansible.com/projects/lint/rules/syntax-check/): уже входит в проверку playbooks, отдельный одинаковый gate не обязателен.
