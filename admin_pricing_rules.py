"""
KURGIN Pricing Rules V1.

Pure pricing-rule layer for KURGIN Admin MVP.

This module intentionally contains:
- no Streamlit imports;
- no file writes;
- no catalog publication;
- no database logic;
- no automatic price confirmation.

It implements deterministic rules from docs/KURGIN_PRICING_ENGINE_SPEC_V1.md.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from typing import Any, Iterable, Mapping


STATUS_CALCULATED = "calculated"
STATUS_REQUEST_PRICE = "request_price"
STATUS_SCORE_REQUIRED = "score_required"
STATUS_MISSING = "missing"
STATUS_BLOCKED = "blocked"
STATUS_NEEDS_REVIEW = "needs_review"
STATUS_FUTURE_SCOPE = "future_scope"

PUBLIC_ACTION_REQUEST_PRICE = "request_price"
PUBLIC_ACTION_CHECKOUT = "checkout"

PRICING_SECTIONS = {"main", "large"}
ROUND_SHAPES = {"round", "round brilliant", "round brilliant cut", "rbc", "круг"}

DEFAULT_RATE_WARNING_THRESHOLD_RUB = Decimal("3")
DEFAULT_GLOBAL_PRICE_ADJUSTMENT_PERCENT = Decimal("0")
ROUNDING_UNIT_RUB = Decimal("1000")

SCORE_BANDS = [
    (Decimal("0"), Decimal("50"), Decimal("0.5")),
    (Decimal("50"), Decimal("70"), Decimal("0.7")),
    (Decimal("70"), Decimal("80"), Decimal("0.8")),
    (Decimal("80"), Decimal("90"), Decimal("1.0")),
    (Decimal("90"), Decimal("95"), Decimal("1.2")),
    (Decimal("95"), Decimal("98.5"), Decimal("1.4")),
    (Decimal("98.5"), Decimal("100"), Decimal("1.7")),
]

DEFAULT_CARAT_BANDS = [
    (Decimal("1.0"), Decimal("1.5"), "1.00–1.49"),
    (Decimal("1.5"), Decimal("2.0"), "1.50–1.99"),
    (Decimal("2.0"), Decimal("2.5"), "2.00–2.49"),
    (Decimal("2.5"), Decimal("3.0"), "2.50–2.99"),
    (Decimal("3.0"), Decimal("3.5"), "3.00–3.49"),
    (Decimal("3.5"), Decimal("4.0"), "3.50–3.99"),
    (Decimal("4.0"), Decimal("4.5"), "4.00–4.49"),
    (Decimal("4.5"), Decimal("5.0"), "4.50–5.00"),
]


@dataclass(frozen=True)
class PricingResult:
    status: str
    price_status: str | None = None
    raw_calculated_price_rub: int | None = None
    calculated_price_rub: int | None = None
    confirmed_public_price_rub: int | None = None
    price_confirmed: bool = False
    score_coefficient: float | None = None
    carat_band: str = ""
    base_price_usd_per_carat: float | None = None
    public_visible: bool = True
    public_sellable: bool = False
    checkout_enabled: bool = False
    public_action: str = PUBLIC_ACTION_REQUEST_PRICE
    rate_warning: bool = False
    rate_difference_rub: float | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if data["price_status"] is None:
            data["price_status"] = data["status"]
        return data


def _to_decimal(value: Any, default: Decimal | None = None) -> Decimal | None:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return Decimal(1) if value else Decimal(0)

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "—", "-"}:
        return default

    cleaned = (
        text.replace("\u00a0", "")
        .replace(" ", "")
        .replace(",", ".")
        .replace("₽", "")
        .replace("$", "")
        .replace("usd", "")
        .replace("rub", "")
        .replace("rur", "")
    )
    allowed = []
    dot_seen = False
    minus_seen = False
    for char in cleaned:
        if char.isdigit():
            allowed.append(char)
        elif char == "." and not dot_seen:
            allowed.append(char)
            dot_seen = True
        elif char == "-" and not minus_seen and not allowed:
            allowed.append(char)
            minus_seen = True

    number_text = "".join(allowed)
    if number_text in {"", "-", ".", "-."}:
        return default
    try:
        return Decimal(number_text)
    except InvalidOperation:
        return default


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def _normalize_key(value: Any) -> str:
    return _clean_text(value).lower().replace("_", " ").replace("-", " ").strip()


def _get(row: Any, *keys: str, default: Any = "") -> Any:
    if row is None:
        return default

    if isinstance(row, Mapping):
        for key in keys:
            if key in row:
                value = row.get(key)
                if value not in (None, ""):
                    return value
        lower_map = {str(k).lower(): v for k, v in row.items()}
        for key in keys:
            value = lower_map.get(key.lower())
            if value not in (None, ""):
                return value
        return default

    for key in keys:
        if hasattr(row, key):
            value = getattr(row, key)
            if value not in (None, ""):
                return value
    return default


def is_round_shape(shape: Any) -> bool:
    return _normalize_key(shape) in ROUND_SHAPES


def is_main_large_section(section: Any) -> bool:
    return _normalize_key(section) in PRICING_SECTIONS


def is_colored_stone(stone: Mapping[str, Any]) -> bool:
    raw = _get(stone, "is_colored", "colored", default="")
    if isinstance(raw, bool):
        return raw
    raw_text = _normalize_key(raw)
    if raw_text in {"true", "1", "yes", "y", "да"}:
        return True

    color_type = _clean_text(_get(stone, "color_type", "color_hue", "color_intensity", default=""))
    return bool(color_type)


def section_value(stone: Mapping[str, Any]) -> str:
    return _normalize_key(_get(stone, "section", "catalog_section", "category", default=""))


def shape_value(stone: Mapping[str, Any]) -> str:
    return _clean_text(_get(stone, "shape", "Shape", "description", "DESCRIPTION", default=""))


def carat_value(stone: Mapping[str, Any]) -> Decimal | None:
    return _to_decimal(_get(stone, "carat", "weight", "Weight", default=None))


def score_value(stone: Mapping[str, Any]) -> Decimal | None:
    return _to_decimal(
        _get(
            stone,
            "karo_score",
            "kurgin_score",
            "score",
            "KURGIN Score",
            "Karo Score",
            "KURGIN SCORE",
            default=None,
        )
    )


def in_pricing_scope(stone: Mapping[str, Any]) -> tuple[bool, str]:
    section = section_value(stone)
    carat = carat_value(stone)

    if is_colored_stone(stone):
        return False, "colored_stone_excluded"
    if section not in PRICING_SECTIONS:
        return False, f"section_{section or 'missing'}_outside_v1"
    if carat is None or carat <= 0:
        return False, "missing_carat"
    if carat < Decimal("1"):
        return False, "carat_below_1_future_scope"
    if carat > Decimal("5"):
        return False, "carat_above_5_exclusive_scope"
    return True, ""


def score_coefficient(score: Any) -> float | None:
    value = _to_decimal(score)
    if value is None:
        return None
    for low, high, coefficient in SCORE_BANDS:
        if low <= value < high:
            return float(coefficient)
        if high == Decimal("100") and low <= value <= high:
            return float(coefficient)
    return None


def carat_band(carat: Any, bands: Iterable[tuple[Any, Any, str]] | None = None) -> dict[str, Any]:
    value = _to_decimal(carat)
    if value is None:
        return {"label": "", "from": None, "to": None, "matched": False}

    source_bands = bands or DEFAULT_CARAT_BANDS
    normalized_bands: list[tuple[Decimal, Decimal, str]] = []
    for low_raw, high_raw, label in source_bands:
        low = _to_decimal(low_raw)
        high = _to_decimal(high_raw)
        if low is None or high is None:
            continue
        normalized_bands.append((low, high, label))

    for index, (low, high, label) in enumerate(normalized_bands):
        is_last = index == len(normalized_bands) - 1
        if low <= value < high or (is_last and low <= value <= high):
            return {"label": label, "from": float(low), "to": float(high), "matched": True}
    return {"label": "", "from": None, "to": None, "matched": False}


def ceil_to_1000_rub(value: Any) -> int:
    amount = _to_decimal(value, Decimal("0")) or Decimal("0")
    if amount <= 0:
        return 0
    rounded = (amount / ROUNDING_UNIT_RUB).to_integral_value(rounding=ROUND_CEILING) * ROUNDING_UNIT_RUB
    return int(rounded)


def rate_warning(
    manual_rate: Any,
    reference_rate: Any,
    threshold: Any = DEFAULT_RATE_WARNING_THRESHOLD_RUB,
) -> dict[str, Any]:
    manual = _to_decimal(manual_rate)
    reference = _to_decimal(reference_rate)
    limit = _to_decimal(threshold, DEFAULT_RATE_WARNING_THRESHOLD_RUB) or DEFAULT_RATE_WARNING_THRESHOLD_RUB

    if manual is None or reference is None:
        return {
            "rate_warning": False,
            "rate_difference_rub": None,
            "warnings": ("reference_rate_missing",) if reference is None else ("manual_rate_missing",),
        }

    difference = abs(manual - reference)
    return {
        "rate_warning": difference > limit,
        "rate_difference_rub": float(difference),
        "warnings": ("rate_difference_above_threshold",) if difference > limit else (),
    }


def validate_round_main_large_score(stone: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(stone, Mapping):
        return {"blocked": True, "status": STATUS_BLOCKED, "errors": ("invalid_stone_row",)}

    if is_colored_stone(stone):
        return {"blocked": False, "status": "ok", "errors": ()}

    if is_round_shape(shape_value(stone)) and is_main_large_section(section_value(stone)):
        score = score_value(stone)
        if score is None or score <= 0:
            return {
                "blocked": True,
                "status": STATUS_SCORE_REQUIRED,
                "errors": ("KURGIN Score required for Round main/large stone",),
            }
    return {"blocked": False, "status": "ok", "errors": ()}


def apply_score_required_rule(stone: Mapping[str, Any]) -> PricingResult | None:
    validation = validate_round_main_large_score(stone)
    if validation["blocked"]:
        return PricingResult(
            status=STATUS_SCORE_REQUIRED,
            public_visible=True,
            public_sellable=False,
            checkout_enabled=False,
            public_action=PUBLIC_ACTION_REQUEST_PRICE,
            errors=tuple(validation.get("errors", ())),
        )
    return None


def _normalize_price_table(price_table: Any) -> list[Mapping[str, Any]]:
    if price_table is None:
        return []
    if hasattr(price_table, "to_dict"):
        try:
            records = price_table.to_dict("records")
            if isinstance(records, list):
                return records
        except Exception:
            pass
    if isinstance(price_table, Mapping):
        return [price_table]
    if isinstance(price_table, list):
        return [row for row in price_table if isinstance(row, Mapping)]
    if isinstance(price_table, tuple):
        return [row for row in price_table if isinstance(row, Mapping)]
    return []


def _row_active(row: Mapping[str, Any]) -> bool:
    raw = _get(row, "is_active", "active", default=True)
    if isinstance(raw, bool):
        return raw
    text = _normalize_key(raw)
    if text in {"", "true", "1", "yes", "y", "да"}:
        return True
    return False


def _matches_text(row_value: Any, stone_value: Any) -> bool:
    row_text = _normalize_key(row_value)
    if not row_text:
        return True
    return row_text == _normalize_key(stone_value)


def _matches_carat_band(row: Mapping[str, Any], carat: Decimal) -> bool:
    low = _to_decimal(_get(row, "carat_band_from", "carat_from", "from", default=None))
    high = _to_decimal(_get(row, "carat_band_to", "carat_to", "to", default=None))
    if low is None or high is None:
        return False
    return low <= carat < high or (high == Decimal("5") and low <= carat <= high)


def select_base_price(price_table: Any, stone: Mapping[str, Any]) -> dict[str, Any]:
    rows = _normalize_price_table(price_table)
    carat = carat_value(stone)
    if not rows:
        return {"found": False, "status": STATUS_MISSING, "base_price_usd_per_carat": None, "row": None, "error": "price_table_empty"}
    if carat is None:
        return {"found": False, "status": STATUS_MISSING, "base_price_usd_per_carat": None, "row": None, "error": "missing_carat"}

    color = _get(stone, "color", "Color", default="")
    clarity = _get(stone, "clarity", "Clarity", default="")
    section = section_value(stone)

    for row in rows:
        if not _row_active(row):
            continue
        if not _matches_text(_get(row, "section", default=""), section):
            continue
        if not _matches_text(_get(row, "color", "Color", default=""), color):
            continue
        if not _matches_text(_get(row, "clarity", "Clarity", default=""), clarity):
            continue
        if not _matches_carat_band(row, carat):
            continue

        base_price = _to_decimal(
            _get(
                row,
                "base_price_usd_per_carat",
                "base_price",
                "usd_per_carat",
                "price_usd_per_carat",
                "price",
                default=None,
            )
        )
        if base_price is None or base_price <= 0:
            return {
                "found": False,
                "status": STATUS_REQUEST_PRICE,
                "base_price_usd_per_carat": None,
                "row": row,
                "error": "empty_base_price_cell",
            }

        return {
            "found": True,
            "status": "ok",
            "base_price_usd_per_carat": float(base_price),
            "row": row,
            "error": "",
        }

    return {
        "found": False,
        "status": STATUS_MISSING,
        "base_price_usd_per_carat": None,
        "row": None,
        "error": "base_price_not_found",
    }


def apply_empty_cell_rule(reason: str = "empty_base_price_cell") -> PricingResult:
    return PricingResult(
        status=STATUS_REQUEST_PRICE if reason == "empty_base_price_cell" else STATUS_MISSING,
        public_visible=True,
        public_sellable=False,
        checkout_enabled=False,
        public_action=PUBLIC_ACTION_REQUEST_PRICE,
        warnings=(reason,),
    )


def can_calculate_price(stone: Mapping[str, Any], price_table: Any | None = None) -> dict[str, Any]:
    scope_ok, scope_reason = in_pricing_scope(stone)
    if not scope_ok:
        return {"can_calculate": False, "status": STATUS_FUTURE_SCOPE, "errors": (scope_reason,)}

    score_rule = validate_round_main_large_score(stone)
    if score_rule["blocked"]:
        return {"can_calculate": False, "status": STATUS_SCORE_REQUIRED, "errors": tuple(score_rule["errors"])}

    if price_table is not None:
        base = select_base_price(price_table, stone)
        if not base["found"]:
            return {"can_calculate": False, "status": base["status"], "errors": (base["error"],)}

    return {"can_calculate": True, "status": "ok", "errors": ()}


def calculate_price(
    stone: Mapping[str, Any],
    price_table: Any,
    manual_usd_rub_rate: Any,
    reference_cbr_usd_rub_rate: Any | None = None,
    rate_warning_threshold_rub: Any = DEFAULT_RATE_WARNING_THRESHOLD_RUB,
    global_price_adjustment_percent: Any = DEFAULT_GLOBAL_PRICE_ADJUSTMENT_PERCENT,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    scope_ok, scope_reason = in_pricing_scope(stone)
    band = carat_band(carat_value(stone))
    if not scope_ok:
        return PricingResult(
            status=STATUS_FUTURE_SCOPE,
            carat_band=band["label"],
            public_visible=True,
            public_sellable=False,
            checkout_enabled=False,
            public_action=PUBLIC_ACTION_REQUEST_PRICE,
            warnings=(scope_reason,),
        ).to_dict()

    score_rule = apply_score_required_rule(stone)
    if score_rule is not None:
        data = score_rule.to_dict()
        data["carat_band"] = band["label"]
        return data

    manual_rate = _to_decimal(manual_usd_rub_rate)
    if manual_rate is None or manual_rate <= 0:
        return PricingResult(
            status=STATUS_BLOCKED,
            carat_band=band["label"],
            errors=("manual_usd_rub_rate_required",),
        ).to_dict()

    rate_info = rate_warning(manual_rate, reference_cbr_usd_rub_rate, rate_warning_threshold_rub)
    warnings.extend(rate_info.get("warnings", ()))

    base = select_base_price(price_table, stone)
    if not base["found"]:
        result = apply_empty_cell_rule(base.get("error", "base_price_not_found")).to_dict()
        result["carat_band"] = band["label"]
        result["rate_warning"] = rate_info["rate_warning"]
        result["rate_difference_rub"] = rate_info["rate_difference_rub"]
        result["warnings"] = tuple(list(result.get("warnings", ())) + warnings)
        return result

    carat = carat_value(stone)
    if carat is None or carat <= 0:
        errors.append("missing_carat")
        return PricingResult(status=STATUS_BLOCKED, errors=tuple(errors)).to_dict()

    if is_round_shape(shape_value(stone)) and is_main_large_section(section_value(stone)):
        coefficient = score_coefficient(score_value(stone))
        if coefficient is None:
            return PricingResult(
                status=STATUS_SCORE_REQUIRED,
                carat_band=band["label"],
                errors=("KURGIN Score required for Round main/large stone",),
            ).to_dict()
    else:
        coefficient = 1.0

    base_price = _to_decimal(base["base_price_usd_per_carat"])
    adjustment_percent = _to_decimal(global_price_adjustment_percent, Decimal("0")) or Decimal("0")
    multiplier = Decimal("1") + (adjustment_percent / Decimal("100"))

    if base_price is None or base_price <= 0:
        result = apply_empty_cell_rule("empty_base_price_cell").to_dict()
        result["carat_band"] = band["label"]
        return result

    raw = base_price * carat * manual_rate * Decimal(str(coefficient)) * multiplier
    rounded = ceil_to_1000_rub(raw)

    return PricingResult(
        status=STATUS_CALCULATED,
        raw_calculated_price_rub=int(raw.to_integral_value(rounding=ROUND_CEILING)),
        calculated_price_rub=rounded,
        score_coefficient=coefficient,
        carat_band=band["label"],
        base_price_usd_per_carat=float(base_price),
        public_visible=True,
        public_sellable=False,
        checkout_enabled=False,
        public_action=PUBLIC_ACTION_REQUEST_PRICE,
        rate_warning=rate_info["rate_warning"],
        rate_difference_rub=rate_info["rate_difference_rub"],
        warnings=tuple(warnings),
        errors=tuple(errors),
    ).to_dict()


def pricing_result(
    stone: Mapping[str, Any],
    price_table: Any,
    manual_usd_rub_rate: Any,
    reference_cbr_usd_rub_rate: Any | None = None,
    rate_warning_threshold_rub: Any = DEFAULT_RATE_WARNING_THRESHOLD_RUB,
    global_price_adjustment_percent: Any = DEFAULT_GLOBAL_PRICE_ADJUSTMENT_PERCENT,
) -> dict[str, Any]:
    return calculate_price(
        stone=stone,
        price_table=price_table,
        manual_usd_rub_rate=manual_usd_rub_rate,
        reference_cbr_usd_rub_rate=reference_cbr_usd_rub_rate,
        rate_warning_threshold_rub=rate_warning_threshold_rub,
        global_price_adjustment_percent=global_price_adjustment_percent,
    )
