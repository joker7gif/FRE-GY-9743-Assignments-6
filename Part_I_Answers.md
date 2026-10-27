# FRE-GT-9743 Assignment 6
Chuyu Wu

## EUR/USD FX Forward Collateralised in GBP

### Setup and notation
I take EUR/USD to mean USD per EUR. At maturity T, the long-EUR forward receives N euros and pays NK dollars, where K is the contractual strike. Let S(t) be the current USD price of one euro. I report the value in USD.

Write P(A|C) for the time-t value, in currency A, of one unit of A paid at T under collateral currency C. The common arguments (t,T) are suppressed. These are effective collateral-adjusted discount factors, not just the local OIS discount factors.

I assume full cash collateralisation, remuneration at the applicable overnight rate, a fixed GBP collateral currency, and no default, transaction costs or collateral-switch option. For the curve reconstruction in Q3, I explicitly use the deterministic funding-spread / FX-forward-invariance approximation.

### 1. Valuation formula
First value the two contractual payments using the same GBP collateral agreement. Receiving N EUR is worth N P(EUR|GBP) euros today; converting this present value at spot gives N S(t) P(EUR|GBP) dollars. The USD payment has present value NK P(USD|GBP). Therefore,

    V_USD(t) = N [S(t) P(EUR|GBP) - K P(USD|GBP)].

The opposite trade has the negative of this value. The collateral currency determines the effective discount curves; it does not change the currency of the contractual payments. Using SONIA alone to discount both payments would omit their currency funding basis.

Equivalently, under the USD pricing measure, define c_USD as the USD collateral rate and b_USD,GBP as the additional spread needed for GBP collateral. The effective discounting rate is c_USD + b_USD,GBP, so [1]

    V_USD(t) = N E_t^Q_USD[exp(-integral_t^T
                     (c_USD(u) + b_USD,GBP(u)) du) * (S(T) - K)].

This expectation is the general pricing statement. The two effective bond prices in the first formula already contain the relevant funding and dependence effects.

### 2. Fair forward strike
The fair strike makes the initial value zero. Since P(USD|GBP) is positive,

    K_fair = S(t) P(EUR|GBP) / P(USD|GBP).
    V_USD(t) = N P(USD|GBP) (K_fair - K).

Thus a long-EUR forward has positive value when its contractual strike is below the current fair forward. At maturity the discount factors become one and the value reduces to N(S(T)-K), as required.

### 3. Are the supplied discount factors sufficient?
In the usual deterministic curve framework, yes, provided the current EUR/USD spot rate and the contract terms are also known. I interpret df[GBP,USD] as P(GBP|USD) and df[EUR,USD] as P(EUR|USD). The first currency is the payment currency and the second is the collateral currency.

For compactness, define

    g = df_SONIA = P(GBP|GBP),
    u = df_SOFR = P(USD|USD),
    e = df[EUR,USD] = P(EUR|USD),
    h = df[GBP,USD] = P(GBP|USD).

FX-forward invariance means that changing the collateral currency leaves the fair FX forward unchanged within this curve approximation [2]. Applying it first to GBP/USD gives

    P(GBP|GBP) / P(USD|GBP) = P(GBP|USD) / P(USD|USD).
    P(USD|GBP) = g u / h.

Next apply it to EUR/USD:

    P(EUR|GBP) / P(USD|GBP) = P(EUR|USD) / P(USD|USD).
    P(EUR|GBP) = g e / h.

Substituting these results into Q1 and Q2 gives

    V_USD(t) = N (g / h) [S(t) e - K u].
    K_fair = S(t) e / u.

The GBP collateral adjustment g/h scales the off-market value of this trade, but cancels from its fair strike in this approximation. The EuroSTR discount factor is not additionally needed once the effective EUR-under-USD curve e has already been built. It can still be an input to that curve's construction.

As a consistency check, at K = S(t)e/u the value is zero. If cross-currency funding basis is zero, h = g and e is the EUR OIS discount factor. The formulas then reduce to the ordinary covered-interest-parity result.

The qualification matters: FX-forward invariance across different collateral currencies is an assumption, not a general consequence of triangular FX arbitrage. In a model with stochastic currency funding spreads and dependence on FX and interest rates, the five initial discount curves alone need not identify P(EUR|GBP) and P(USD|GBP). In that setting I would need those GBP-collateral curves directly, or a calibrated joint model / additional market information. The general formulas in Q1 and Q2 still apply [1].

My conclusion is therefore: the supplied curves are sufficient for the standard deterministic construction, with spot FX supplied separately; they are not unconditionally sufficient for an unrestricted stochastic collateral model.

### References
[1] Fujii, M. and Takahashi, A. (2015). A General Framework for the Benchmark Pricing in a Fully Collateralized Market, Sections 2 and 5.1. https://arxiv.org/abs/1508.06339

[2] Burgess, N. Synthetic Forward FX Replication & Collateralized Discount Factors, slides 6 and 9-10. https://nicholasburgess.co.uk/wp-content/uploads/2025/04/synthetic-fx-forward-replication.pdf
