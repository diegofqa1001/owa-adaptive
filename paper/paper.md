---
title: 'owa-adaptive: A regime-adaptive OWA recommendation engine with behavioral risk profiles for equity portfolios under uncertainty'
tags:
  - Python
  - ordered weighted averaging
  - behavioral finance
  - portfolio selection
  - decision under uncertainty
authors:
  - name: Diego Fernando Quintero Avellaneda
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: Universidad Nacional de Colombia, Sede Manizales, Colombia
    index: 1
date: 15 June 2026
bibliography: paper.bib
---

# Summary

`owa-adaptive` is an open-source Python package that recommends equity portfolios by aggregating
multicriteria asset scores with Ordered Weighted Averaging (OWA) operators whose attitude (*orness*) is
determined by a taxonomy of eight **behavioral risk profiles** and dynamically modulated by the **market
regime** inferred from uncertainty signals (VIX and Economic Policy Uncertainty). The package implements an
**induced OWA (IOWA)** adaptation mechanism, a **spectral correction** (ZCA whitening) that decorrelates the
criteria to diagnose and mitigate the multicriteria "investor inversion" effect, and a reproducible backtesting
harness. It ships with a synthetic, seed-fixed
market panel so that every result is reproducible offline, alongside optional loaders for real data.

# Statement of need

Financial decision support under uncertainty must reconcile two facts that standard mean–variance pipelines
ignore: investors differ in *attitude* (a behavioral construct), and that attitude should *adapt* to the market
regime. OWA operators [@Yager1988] provide a principled, interpretable way to encode attitude through the
orness measure and linguistic quantifiers [@Yager1996], but three gaps remain in available tooling: (i) no
package maps **behavioral profiles** to OWA weights in a calibrated, auditable way; (ii) the **induced**
variant [@YagerFilev1999] is rarely wired to *observable* regime signals; and (iii) correlated criteria can
**invert** the intended risk ordering, an effect not addressed by existing libraries. `owa-adaptive` closes
these gaps with a tested, documented, end-to-end engine usable from a Python API, a REST API, or an
interactive dashboard.

# Functionality

- **Behavioral taxonomy.** Eight profiles (Guardian→Visionary) over seven behavioral dimensions, with a fixed,
  monotone bridge from a dimension vector to a target orness in `[0.158, 0.865]`, and Kendall's *W* for
  inter-judge agreement.
- **RIM quantifier weights and maximum-entropy weights.** Power-quantifier weights solved for a target orness,
  plus the analytic maximum-entropy solution [@FullerMajlender2001].
- **Regime-adaptive IOWA.** A regime stress index `s(t)` derived from standardized VIX/EPU contracts the
  effective orness toward a defensive floor, monotonically.
- **Spectral correction.** A ZCA whitening that **decorrelates** the criteria; an **inversion index** (Spearman
  rank correlation between profile orness and realized portfolio risk) **diagnoses** the multicriteria inversion.
  Full restoration of monotonicity corresponds to constructed scenarios with correlation-induced inversion (per
  the A3 theorem); on the generic synthetic panel the index diagnoses the effect without guaranteeing its
  correction.
- **Validation.** Rolling-window backtesting with Sharpe, maximum drawdown, and a risk-calibration RMSE, plus
  adaptive-vs-static comparison.

# Reproducibility

A single global seed governs the synthetic panel and all figures. Figures use the Okabe–Ito color palette on a
white background. `pytest` covers operator properties, weight calibration, the behavioral bridge, adaptation
monotonicity, spectral decorrelation, and panel reproducibility.

# Acknowledgements

Doctoral research advised by P. J. Ramírez-Angulo and E. León-Castro.

# References
