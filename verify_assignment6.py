"""Numerical and convention checks. Run from this folder with Python 3.11."""
import contextlib
import io
import json
import platform

import numpy as np
import pandas as pd
import QuantLib as ql

from fixedincomelib.date import Date, add_period
from fixedincomelib.market.registries import IndexFixingsManager


def main():
    ns = {}
    with open('hw6_interest_rate_products.ipynb', encoding='utf-8') as f:
        notebook = json.load(f)
    with contextlib.redirect_stdout(io.StringIO()):
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                exec(''.join(cell['source']), ns)
    model, params = ns['model'], ns['parameters']
    funding = ns['FUNDING_INDEX']

    def pv(product, m=model):
        return ns['qfCreateValueReport'](m, product, params, 'PV')[0][1]

    def fixed_pv(leg, m=model):
        return sum(cf.notional * cf.accrued * leg.fixed_rate
                   * m.discount_factor(funding, cf.payment_date)
                   for cf in (leg.cashflow(i) for i in range(leg.num_cashflows())))

    def floating_pv(leg, m=model):
        result = 0.0
        for i in range(leg.num_cashflows()):
            cf = leg.cashflow(i)
            # All coupon boundaries here are index business days. Daily
            # projected compound factors telescope to this endpoint ratio.
            ratio = m.discount_factor(cf.on_index, cf.effective_date) / m.discount_factor(cf.on_index, cf.termination_date)
            tau = cf.on_index.dayCounter().yearFraction(cf.effective_date, cf.termination_date)
            result += cf.notional * (ratio - 1 + tau * cf.spread) * m.discount_factor(funding, cf.payment_date)
        return result

    swap, basis = ns['swap'], ns['basis_swap']
    expected_swap = fixed_pv(swap.fixed_leg) - floating_pv(swap.floating_leg)
    expected_basis = floating_pv(basis.floating_leg_1) - floating_pv(basis.floating_leg_2)
    np.testing.assert_allclose(pv(swap), expected_swap, rtol=1e-10, atol=1e-7)
    np.testing.assert_allclose(pv(basis), expected_basis, rtol=1e-10, atol=1e-7)
    print('PASS 1: notebook assertions and independent discounted-coupon formulas.')

    for p in [swap, basis]:
        c = p.serialize()
        for direction, scale in [('PAY', 1), ('RECEIVE', -1), ('RECEIVE', 2)]:
            changed = dict(c, NOTIONAL=c['NOTIONAL'] * scale)
            changed['PAY_OR_REC' if p is swap else 'PAY_OR_REC_LEG_1'] = direction
            q = type(p).deserialize(changed)
            expected = (-1 if direction == 'PAY' else 1) * scale * pv(p)
            np.testing.assert_allclose(pv(q), expected, atol=1e-7)
        np.testing.assert_allclose(pv(type(p).deserialize(c)), pv(p), atol=1e-8)
        report = ns['qfCreateCashflowsReport'](model, p, params).display()
        np.testing.assert_allclose(report['PV'].sum(), pv(p), atol=1e-7)
    print('PASS 2: pay/receive reversal, signed/scaled notionals, serialization and report totals.')

    # Independently calculate the par fixed rate and the value of 1 bp spread.
    annuity = fixed_pv(swap.fixed_leg) / swap.fixed_rate
    par = floating_pv(swap.floating_leg) / annuity
    at_par = type(swap).deserialize(dict(swap.serialize(), FIXED_RATE=par))
    np.testing.assert_allclose(pv(at_par), 0, atol=1e-7)
    bumped = type(basis).deserialize(dict(basis.serialize(), SPREAD_OVER_LEG_1=basis.spread + 0.0001))
    spread_annuity = sum(basis.notional * basis.on_index_1.dayCounter().yearFraction(
        basis.floating_leg_1.cashflow(i).effective_date, basis.floating_leg_1.cashflow(i).termination_date)
        * model.discount_factor(funding, basis.floating_leg_1.cashflow(i).payment_date)
        for i in range(basis.floating_leg_1.num_cashflows()))
    np.testing.assert_allclose(pv(bumped) - pv(basis), 0.0001 * spread_annuity, atol=1e-7)
    print('PASS 3: par swap has zero PV; a 1 bp basis move equals its discounted spread annuity.')

    factory = ns['qfCreateProductFromDataConvention']
    for convention, quote in [('USD-SOFR-OIS', ns['FIXED_RATE']), (ns['BASIS_CONVENTION'], ns['BASIS_SPREAD'])]:
        conv = ns['DataConventionRegistry']().get(convention)
        for axis in ['1Y', '3Mx1Y', '2026-04-02x2027-04-02']:
            created = factory(ns['VALUE_DATE'], convention, axis, quote, notional=ns['NOTIONAL'])
            if axis == '1Y':
                assert created.effective_date.ISO() == ns['VALUE_DATE']
            else:
                assert created.effective_date.ISO() == ns['EFFECTIVE_DATE']
                assert created.termination_date.ISO() == ns['SWAP_END_DATE']
            assert created.pay_offset == conv.payment_offset
            assert created.compounding_method == conv.compounding_method
            assert created.last_date >= created.termination_date
            if convention == ns['BASIS_CONVENTION']:
                assert created.on_index_1.name() == conv.index_1.name()
                assert created.on_index_2.name() == conv.index_2.name()
                if axis != '1Y':
                    assert created.floating_leg_1.num_cashflows() == 4
                    assert created.floating_leg_2.num_cashflows() == 4
            else:
                if axis != '1Y':
                    assert created.fixed_leg.num_cashflows() == 1
                    assert created.floating_leg.num_cashflows() == 1
            assert np.isfinite(pv(created))
    mixed_swap = type(swap).deserialize(dict(swap.serialize(), ACCRUAL_PERIOD='6M', FLOATING_LEG_ACCRUAL_PERIOD='3M'))
    assert mixed_swap.fixed_leg.num_cashflows() == 2
    assert mixed_swap.floating_leg.num_cashflows() == 4
    np.testing.assert_allclose(pv(mixed_swap), fixed_pv(mixed_swap.fixed_leg) - floating_pv(mixed_swap.floating_leg), atol=1e-7)
    mixed_basis = type(basis).deserialize(dict(basis.serialize(), ACCRUAL_PERIOD_2='6M'))
    assert mixed_basis.floating_leg_1.num_cashflows() == 4
    assert mixed_basis.floating_leg_2.num_cashflows() == 2
    np.testing.assert_allclose(pv(mixed_basis), floating_pv(mixed_basis.floating_leg_1) - floating_pv(mixed_basis.floating_leg_2), atol=1e-7)
    print('PASS 4: spot/forward/explicit factory dates, conventions, payment offsets and different leg frequencies.')

    def model_at(value_date):
        inputs = []
        for name, values in [('SOFR-1B-IFR', [0.03, 0.04, 0.05]), ('FF-1B-IFR', [0.028, 0.037]), ('SOFR-1B-FUNDING-IFR', [0, 0.001])]:
            tenors = ['1Y', '2Y', '3Y'][:len(values)]
            inputs.append(ns['qfCreateData1D']('INSTANTANEOUS FORWARD RATE', name, pd.DataFrame({'values': values}, index=tenors)))
        return ns['qfCreateModel'](value_date.ISO(), 'YIELD_CURVE', ns['qfCreateDataCollection'](inputs), ns['build_methods'])

    for p, Engine in [(swap, ns['ValuationEngineProductRfrSwap']), (basis, ns['ValuationEngineProductOvernightIndexBasisSwap'])]:
        m = model_at(p.last_date)
        engine = Engine(m, params, p, ns['ValuationRequest'].PV)
        legs = engine._legs() if p is basis else [('Fixed', 1, engine.fixed_leg_engine_), ('Floating', -1, engine.floating_leg_engine_)]
        expected_cash = 0.0
        for _, sign, leg_engine in legs:
            for i, index_engine in enumerate(leg_engine.index_engines_):
                cf = leg_engine.stream_.cashflow(i)
                if cf.payment_date != p.last_date:
                    continue
                if index_engine is None:
                    amount = cf.notional * cf.accrued * leg_engine.stream_.fixed_rate
                else:
                    rate = 0.031 if 'SOFR' in cf.on_index.name() else 0.027
                    factors = []
                    for _, _, fixing_date, accrual, _ in index_engine.intervals_:
                        IndexFixingsManager().insert_fixing(cf.on_index, fixing_date, rate)
                        factors.append(1 + accrual * rate)
                    tau = cf.on_index.dayCounter().yearFraction(cf.effective_date, cf.termination_date)
                    amount = cf.notional * (np.prod(factors) - 1 + tau * cf.spread)
                expected_cash += sign * amount
        engine.calculate_value()
        np.testing.assert_allclose([engine.value, engine.cash], [expected_cash, expected_cash], atol=1e-7)
        m = model_at(Date(p.last_date.serialNumber() + 1))
        engine = Engine(m, params, p, ns['ValuationRequest'].PV)
        engine.calculate_value()
        np.testing.assert_allclose([engine.value, engine.cash], [0, 0], atol=1e-12)
    print('PASS 5: same-day settlement with observed fixings and zero PV/cash after final payment.')

    # Check the algebra of the written FX answer with synthetic inputs.
    spot, g, u, e, h, n = 1.10, 0.96, 0.95, 0.97, 0.955, 1e6
    usd_gbp, eur_gbp = g*u/h, g*e/h
    fair = spot*e/u
    np.testing.assert_allclose(spot*eur_gbp/usd_gbp, fair)
    np.testing.assert_allclose(n*(spot*eur_gbp-fair*usd_gbp), 0, atol=1e-8)
    strike = 1.12
    np.testing.assert_allclose(n*(spot*eur_gbp-strike*usd_gbp), n*g/h*(spot*e-strike*u))
    print('PASS 6: FX collateral transformation, fair-strike cancellation and zero value at par.')
    print(f'Python {platform.python_version()} | NumPy {np.__version__} | pandas {pd.__version__} | QuantLib {ql.__version__}')
    print(f'FRA PV: {pv(ns["fra"]):.12f}')
    print(f'RFR swap PV: {pv(swap):.12f}')
    print(f'Overnight basis swap PV: {pv(basis):.12f}')
    print(f'Par fixed rate: {par:.12f}')


if __name__ == '__main__':
    main()
