# PUBLISH_RULES.md

## Публикация не входит в Этап 1

Импорт сохраняет камни в админке, но не публикует их.

## Базовое правило публичного экспорта

Камень попадает в публичный экспорт только если:

```text
status = published
availability_status = in_stock
catalog_section.is_public = true
published_price заполнена
обязательные публичные поля заполнены
```

Не попадают: `reserved`, `sold`, `removed`, `archived`, `draft`, `ready`, камни из скрытого раздела, камни без `published_price`, камни вне текущей версии.

## ROUND

ROUND публикуется с KURGIN Score, если Score импортирован из Excel.

## Не ROUND

Не ROUND может публиковаться без KURGIN Score.

## Issues

`HIGH_SCORE_DIAMETER_REVIEW` не блокирует публикацию, но показывает рекомендацию проверить diameter/spread/класс.

`UNSUPPORTED_SHAPE` не ошибка, а разделение ROUND и других форм.
