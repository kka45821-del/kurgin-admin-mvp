# KURGIN Pricing Formula v0.2

## 1. Назначение

Pricing Formula v0.2 фиксирует принцип, что маржа специалиста не должна быть одним фиксированным процентом.

Маржа специалиста должна зависеть от двух факторов:

- cost tier;
- KURGIN Score tier.

Это документ проектирования. Он не меняет код, не подтверждает цены и не публикует priced catalog.

## 2. Базовая логика

В v0.2 маржа специалиста считается не напрямую, а через базовую маржу по cost tier и мягкий модификатор по KURGIN Score.

```text
base_specialist_margin_percent = margin percent from cost tier

score_margin_modifier = modifier from KURGIN Score tier

final_specialist_margin_percent = base_specialist_margin_percent × score_margin_modifier
```

## 3. Score margin modifier

Модификатор маржи по KURGIN Score:

| KURGIN Score tier | score_margin_modifier |
|---:|---:|
| 0–50 | 0.50 |
| 50–70 | 0.65 |
| 70–80 | 0.80 |
| 80–90 | 1.00 |
| 90–95 | 1.10 |
| 95–98.5 | 1.20 |
| 98.5–100 | 1.30 |

## 4. Смысл правила

Логика правила:

- чем ниже KURGIN Score, тем меньше маржа специалиста;
- чем выше KURGIN Score, тем больше маржа специалиста;
- это мотивирует специалистов продавать более качественные камни;
- специалист получает больший экономический смысл работать с сильными камнями, а не только с дешёвыми или случайными позициями.

## 5. Важное ограничение

KURGIN Score уже влияет на стоимость через `score_coefficient`.

Поэтому `score_margin_modifier` должен быть мягким и управляемым, чтобы не раздувать цену слишком резко.

Контрольное правило:

```text
Score coefficient changes stone pricing.
Score margin modifier changes specialist economics.
Do not let both layers inflate price aggressively at the same time.
```

## 6. Применение

На текущем этапе score-based margin modifier применяется только к:

```text
specialist_client_display_price_rub
```

Не применять пока к:

```text
public_price_rub
specialist_purchase_price_rub
```

Исключения возможны только после отдельного решения и отдельного scope.

## 7. Не применять сейчас

В рамках этого документа не делается:

- кодовая реализация;
- подтверждение цен;
- публикация priced catalog;
- роли;
- личный кабинет специалиста;
- checkout;
- оплата;
- reserve;
- public Index UI;
- изменение Analyzer;
- изменение public catalog display.

## 8. Пример расчёта

Пример:

```text
cost tier margin = 12%
KURGIN Score = 96.2
score_margin_modifier = 1.20

final_specialist_margin_percent = 12% × 1.20 = 14.4%
```

Другой пример:

```text
cost tier margin = 12%
KURGIN Score = 76.0
score_margin_modifier = 0.80

final_specialist_margin_percent = 12% × 0.80 = 9.6%
```

## 9. Rationale

Такой подход сохраняет контролируемость:

- cost tier задаёт базовую экономику;
- KURGIN Score добавляет качественный стимул;
- низкий Score не получает такую же маржу, как сильный камень;
- высокий Score получает премиальный стимул, но в мягком диапазоне.

## 10. Future implementation notes

Будущая реализация должна быть отдельным кодовым пакетом и должна включать:

- явную таблицу cost tiers;
- явную таблицу score margin modifiers;
- preview перед применением;
- audit log;
- запрет автоматической публикации;
- тесты на крайние Score значения;
- проверку, что public_price_rub не меняется без отдельного решения.

## 11. Контрольное правило

```text
Specialist margin is dynamic, but controlled.
Public price is not changed by this document.
```

Formula v0.2 фиксирует принцип расчёта, но не запускает коммерческое применение без отдельного утверждения.
