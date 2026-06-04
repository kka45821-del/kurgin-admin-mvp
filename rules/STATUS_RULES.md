# STATUS_RULES.md

## Не смешивать статусы

Нельзя смешивать `status`, `availability_status`, `score_status`, `validation_status`.

## status

Состояние записи в админке:

```text
draft — Черновик
ready — Готов
published — Опубликован
archived — Архив
```

После импорта: `status = draft`.

## availability_status

Товарное состояние камня:

```text
in_stock — В наличии
reserved — Забронирован
sold — Продан
removed — Снят с продажи
```

После импорта: `availability_status = in_stock`.

## score_status

Для ROUND: `calculated`.

Для не ROUND: `not_available_for_shape`.

## validation_status

```text
ok
warning
blocking_error
```

`Issues` из Excel не блокирует публикацию автоматически.

## Важные различия

```text
published ≠ продаётся
status ≠ наличие
нет KURGIN Score у не ROUND ≠ нельзя публиковать
Issues ≠ автоматический запрет
```
