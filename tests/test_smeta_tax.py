"""Tax calculator: regimes, limits, progressive NDFL, contributions, best-regime choice."""
from decimal import Decimal

import pytest

from smeta.tax import (
    NPD, OSNO_IP, OSNO_OOO, USN6, USN15, Money, TaxRates, calculate, compare, compare_text,
    insurance_contributions, ip_contributions, ndfl,
)

RATES_CSV = """year;key;value;note
2025;vat_rate;20;НДС
2025;usn_income_rate;6;УСН доходы
2025;usn_profit_rate;15;УСН доходы-расходы
2025;usn_min_tax_rate;1;Минимальный налог
2025;usn_income_limit;450000000;Лимит УСН
2025;usn_vat_threshold;60000000;Порог НДС на УСН
2025;usn_vat_rate_low;5;НДС на УСН до 250 млн
2025;usn_vat_rate_mid;7;НДС на УСН до 450 млн
2025;usn_vat_low_limit;250000000;Граница 5/7
2025;profit_tax_rate;25;Налог на прибыль
2025;ndfl_brackets;2400000:13,5000000:15,20000000:18,50000000:20,:22;НДФЛ
2025;insurance_rate;30;Взносы
2025;insurance_reduced_rate;15.1;Взносы сверх базы
2025;insurance_base_limit;2759000;Предельная база
2025;accident_rate;0;Травматизм
2025;ip_fixed;53658;Фиксированные взносы ИП
2025;ip_extra_rate;1;1 % сверх порога
2025;ip_extra_threshold;300000;Порог
2025;ip_extra_cap;300888;Максимум 1 %
2025;npd_rate_org;6;НПД
2025;npd_limit;2400000;Лимит НПД
"""


@pytest.fixture
def rates(tmp_path) -> TaxRates:
    path = tmp_path / "rates.csv"
    path.write_text(RATES_CSV, encoding="utf-8")
    return TaxRates.load(2025, path)


# ---------- rates file ----------


def test_rates_fall_back_to_the_latest_year_and_say_so(tmp_path):
    path = tmp_path / "rates.csv"
    path.write_text(RATES_CSV, encoding="utf-8")
    loaded = TaxRates.load(2031, path)
    assert loaded.year == 2025
    assert loaded.stale
    result = calculate(USN6, Money(revenue=Decimal(1000000)), loaded)
    assert any("2031" in note for note in result.notes)


def test_shipped_rates_cover_the_current_year():
    loaded = TaxRates.load()
    assert loaded.num("vat_rate") == 20
    assert loaded.num("usn_income_rate") == 6
    assert "налог" in loaded.as_text().lower()


# ---------- building blocks ----------


def test_progressive_ndfl(rates):
    assert ndfl(Decimal(1000000), rates) == Decimal("130000.00")          # 13 %
    assert ndfl(Decimal(3000000), rates) == Decimal("402000.00")          # 2.4M*13 + 0.6M*15
    assert ndfl(Decimal(6000000), rates) == Decimal("882000.00")          # +1M*18 выше 5 млн
    assert ndfl(Decimal(60000000), rates) == Decimal("11602000.00")       # все пять ступеней


def test_contributions_use_the_reduced_rate_above_the_base(rates):
    low, _ = insurance_contributions(Money(revenue=Decimal(0), payroll=Decimal(1000000)), rates)
    assert low == Decimal("300000.00")
    high, notes = insurance_contributions(Money(revenue=Decimal(0), payroll=Decimal(4000000)), rates)
    assert high == Decimal("2759000") * Decimal("0.30") + Decimal("1241000") * Decimal("0.151")
    assert any("предельной базы" in note for note in notes)


def test_ip_own_contributions_are_capped(rates):
    assert ip_contributions(Money(revenue=Decimal(0)), rates, Decimal(200000)) == Decimal(53658)
    assert ip_contributions(Money(revenue=Decimal(0)), rates, Decimal(1300000)) == Decimal(53658 + 10000)
    huge = ip_contributions(Money(revenue=Decimal(0)), rates, Decimal(100000000))
    assert huge == Decimal(53658) + Decimal(300888)


# ---------- regimes ----------


def test_usn6_reduction_is_capped_at_half_the_tax(rates):
    inputs = Money(revenue=Decimal(1000000), payroll=Decimal(300000))
    result = calculate(USN6, inputs, rates)
    assert result.items["Страховые взносы с ФОТ"] == Decimal("90000.00")
    assert result.items["УСН 6 %"] == Decimal("30000.00")                 # 60000 − 50 %
    assert result.net(inputs) == Decimal(1000000) - 300000 - 90000 - 30000


def test_ip_without_employees_offsets_the_whole_tax(rates):
    inputs = Money(revenue=Decimal(900000), employees=False, ip=True)
    result = calculate(USN6, inputs, rates)
    assert result.items["Взносы ИП за себя"] == Decimal(53658 + 6000)
    assert result.items["УСН 6 %"] == Decimal("0.00")                     # 54000 < взносы


def test_usn15_minimum_tax(rates):
    thin = Money(revenue=Decimal(1000000), materials=Decimal(960000), suppliers_with_vat=False)
    result = calculate(USN15, thin, rates)
    assert result.items["УСН 15 %"] == Decimal("10000.00")                # 1 % от дохода > 15 % от 40 тыс
    assert any("минимальный налог" in note for note in result.notes)
    fat = Money(revenue=Decimal(1000000), materials=Decimal(500000), suppliers_with_vat=False)
    assert calculate(USN15, fat, rates).items["УСН 15 %"] == Decimal("75000.00")


def test_usn_vat_appears_above_the_threshold(rates):
    inputs = Money(revenue=Decimal(5000000), annual_revenue=Decimal(100000000))
    result = calculate(USN6, inputs, rates)
    assert result.items["НДС на УСН"] == Decimal("250000.00")             # 5 %
    inputs_mid = Money(revenue=Decimal(5000000), annual_revenue=Decimal(300000000))
    assert calculate(USN6, inputs_mid, rates).items["НДС на УСН"] == Decimal("350000.00")   # 7 %


def test_usn_blocked_above_the_income_limit(rates):
    result = calculate(USN15, Money(revenue=Decimal(1000000), annual_revenue=Decimal(500000000)), rates)
    assert result.blocked and "лимит" in result.blocked.lower()


def test_osno_vat_nets_out_input_vat(rates):
    inputs = Money(revenue=Decimal(1200000), vat_in_revenue=Decimal(200000),
                   materials=Decimal(600000), payroll=Decimal(0))
    result = calculate(OSNO_OOO, inputs, rates)
    assert inputs.input_vat == Decimal("100000.00")
    assert result.items["НДС к уплате"] == Decimal("100000.00")
    profit = inputs.revenue_net - inputs.costs_net
    assert result.items["Налог на прибыль"] == (profit * Decimal("0.25")).quantize(Decimal("0.01"))


def test_osno_without_vat_in_the_estimate_warns(rates):
    result = calculate(OSNO_OOO, Money(revenue=Decimal(1000000)), rates)
    assert any("нет НДС" in note for note in result.notes)


def test_osno_ip_pays_own_contributions_and_ndfl(rates):
    inputs = Money(revenue=Decimal(3600000), vat_in_revenue=Decimal(600000),
                   materials=Decimal(1200000), payroll=Decimal(500000), ip=True)
    result = calculate(OSNO_IP, inputs, rates)
    assert "Взносы ИП за себя" in result.items
    assert result.items["НДФЛ"] > 0
    assert result.total == sum(result.items.values())


def test_npd_limits(rates):
    assert calculate(NPD, Money(revenue=Decimal(3000000), annual_revenue=Decimal(3000000)), rates).blocked
    with_staff = calculate(NPD, Money(revenue=Decimal(500000), payroll=Decimal(200000)), rates)
    assert "работник" in with_staff.blocked
    solo = calculate(NPD, Money(revenue=Decimal(500000), employees=False), rates)
    assert solo.items["НПД 6 %"] == Decimal("30000.00")


# ---------- comparison ----------


def test_compare_puts_the_cheapest_first_and_blocked_last(rates):
    inputs = Money(revenue=Decimal(5000000), vat_in_revenue=Decimal(833333),
                   materials=Decimal(2000000), payroll=Decimal(1000000),
                   annual_revenue=Decimal(20000000))
    results = compare(inputs, rates)
    assert not results[0].blocked
    assert results[0].total <= results[1].total
    assert results[-1].blocked                       # НПД с таким доходом невозможен
    text = compare_text(inputs, rates)
    assert "Выгоднее всего" in text
    assert "Разница с худшим" in text


def test_burden_and_net_are_consistent(rates):
    inputs = Money(revenue=Decimal(1000000), materials=Decimal(300000), payroll=Decimal(200000))
    result = calculate(USN6, inputs, rates)
    assert result.burden(inputs) == (result.total / Decimal(1000000) * 100).quantize(Decimal("0.1"))
    assert result.net(inputs) == Decimal(1000000) - 300000 - 200000 - result.total
