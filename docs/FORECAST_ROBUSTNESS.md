# Noisy and sparse forecast validation

Seed 20261019; six 600-day synthetic histories and one 40-day insufficient-history case. No owner data or real-world accuracy claim. Four non-overlapping outer folds per valid horizon; three earlier selection folds. Each candidate receives the same chronological training and test data. MAE is horizon net-movement error; WAPE denominator is the sum of absolute actual horizon net movements. Near-zero net denominators are flagged.

Raw adaptive selection beat moving average in 7 of 24 valid dataset/horizon pairs, lost in 9, and tied in 8. It does not demonstrate a universal improvement. Deployment now retains moving average unless the currently selected candidate also clears a stable 5% historical MAE improvement gate with at least three folds. Reused validation is selection evidence, not an independent accuracy estimate of that additional gate.

| Synthetic data | Days | Folds | Net denominator | Unstable | Baseline MAE / WAPE | Raw adaptive MAE / WAPE | Deployment selection |
|---|---:|---:|---:|---|---|---|---|
| stationary_noise | 7 | 4 | 2428.78 | False | 165.14 / 27.20% | 122.41 / 20.16% | last_week |
| stationary_noise | 15 | 4 | 5100.78 | False | 336.97 / 26.42% | 393.36 / 30.85% | weekday |
| stationary_noise | 30 | 4 | 9671.89 | False | 296.70 / 12.27% | 296.70 / 12.27% | moving_average |
| stationary_noise | 90 | 4 | 25215.06 | False | 788.97 / 12.52% | 799.34 / 12.68% | weekday |
| weekly_noise | 7 | 4 | 2990.66 | False | 282.22 / 37.75% | 380.86 / 50.94% | moving_average |
| weekly_noise | 15 | 4 | 6628.84 | False | 260.32 / 15.71% | 377.05 / 22.75% | moving_average |
| weekly_noise | 30 | 4 | 14182.94 | False | 242.01 / 6.83% | 104.25 / 2.94% | weekday |
| weekly_noise | 90 | 4 | 42051.51 | False | 745.52 / 7.09% | 697.46 / 6.63% | weekday |
| trend_break | 7 | 4 | 5030.80 | False | 100.16 / 7.96% | 137.95 / 10.97% | moving_average |
| trend_break | 15 | 4 | 10357.98 | False | 136.40 / 5.27% | 384.11 / 14.83% | moving_average |
| trend_break | 30 | 4 | 22656.31 | False | 1752.98 / 30.95% | 1725.40 / 30.46% | moving_average |
| trend_break | 90 | 4 | 39929.98 | False | 2656.58 / 26.61% | 2656.58 / 26.61% | moving_average |
| sparse_invoices | 7 | 4 | 3157.05 | False | 883.95 / 112.00% | 883.95 / 112.00% | moving_average |
| sparse_invoices | 15 | 4 | 893.67 | False | 411.66 / 184.26% | 373.72 / 167.27% | exponential |
| sparse_invoices | 30 | 4 | 2797.60 | False | 1037.65 / 148.36% | 1037.65 / 148.36% | moving_average |
| sparse_invoices | 90 | 4 | 7553.08 | False | 1278.94 / 67.73% | 1203.42 / 63.73% | weekday |
| near_zero_net | 7 | 4 | 16.73 | True | 3.58 / 85.61% | 3.68 / 87.92% | moving_average |
| near_zero_net | 15 | 4 | 17.20 | True | 5.09 / 118.37% | 3.06 / 71.12% | moving_average |
| near_zero_net | 30 | 4 | 54.24 | True | 15.76 / 116.24% | 15.76 / 116.24% | moving_average |
| near_zero_net | 90 | 4 | 75.46 | True | 27.99 / 148.37% | 29.08 / 154.13% | moving_average |
| volatile_shocks | 7 | 4 | 3691.81 | False | 753.28 / 81.62% | 753.28 / 81.62% | moving_average |
| volatile_shocks | 15 | 4 | 7070.64 | False | 1362.05 / 77.05% | 1362.05 / 77.05% | moving_average |
| volatile_shocks | 30 | 4 | 9435.99 | False | 2556.98 / 108.39% | 2596.98 / 110.09% | moving_average |
| volatile_shocks | 90 | 4 | 26380.71 | False | 2170.05 / 32.90% | 2170.05 / 32.90% | moving_average |
| short_history | 7 | 0 | 0.00 | True | None / None% | None / None% | moving_average |
| short_history | 15 | 0 | 0.00 | True | None / None% | None / None% | moving_average |
| short_history | 30 | 0 | 0.00 | True | None / None% | None / None% | moving_average |
| short_history | 90 | 0 | 0.00 | True | None / None% | None / None% | moving_average |

All five methods and fold cutoffs/predictions are saved in `test-results/final-forecast-robustness.json`. Reproduce with `DEBUG=true python -m scripts.evaluate_forecast_robustness`. No actual missing day is known to be zero: the ledger-only experiment interprets missing entries as zero and therefore cannot validate unrecorded trading.

`test_nested_evaluation_outer_tail_cannot_change_earlier_folds` mutates the final actual observation and verifies earlier fold predictions/selections remain unchanged. `test_moving_average_matches_original_activity_start_denominator` verifies agreement with the original engine denominator. Sparse, zero-denominator and short histories retain explicit limitations.

## All-method metrics

| Dataset | Days | Method | MAE | WAPE |
|---|---:|---|---:|---:|
| stationary_noise | 7 | moving_average | 165.14 | 27.20 |
| stationary_noise | 7 | last_week | 104.56 | 17.22 |
| stationary_noise | 7 | exponential | 141.86 | 23.36 |
| stationary_noise | 7 | weekday | 163.51 | 26.93 |
| stationary_noise | 7 | adaptive | 122.41 | 20.16 |
| stationary_noise | 15 | moving_average | 336.97 | 26.42 |
| stationary_noise | 15 | last_week | 330.90 | 25.95 |
| stationary_noise | 15 | exponential | 393.39 | 30.85 |
| stationary_noise | 15 | weekday | 317.55 | 24.90 |
| stationary_noise | 15 | adaptive | 393.36 | 30.85 |
| stationary_noise | 30 | moving_average | 296.70 | 12.27 |
| stationary_noise | 30 | last_week | 465.83 | 19.27 |
| stationary_noise | 30 | exponential | 689.14 | 28.50 |
| stationary_noise | 30 | weekday | 316.35 | 13.08 |
| stationary_noise | 30 | adaptive | 296.70 | 12.27 |
| stationary_noise | 90 | moving_average | 788.97 | 12.52 |
| stationary_noise | 90 | last_week | 2694.62 | 42.75 |
| stationary_noise | 90 | exponential | 2633.24 | 41.77 |
| stationary_noise | 90 | weekday | 676.94 | 10.74 |
| stationary_noise | 90 | adaptive | 799.34 | 12.68 |
| weekly_noise | 7 | moving_average | 282.22 | 37.75 |
| weekly_noise | 7 | last_week | 322.36 | 43.12 |
| weekly_noise | 7 | exponential | 431.19 | 57.67 |
| weekly_noise | 7 | weekday | 279.86 | 37.43 |
| weekly_noise | 7 | adaptive | 380.86 | 50.94 |
| weekly_noise | 15 | moving_average | 260.32 | 15.71 |
| weekly_noise | 15 | last_week | 318.08 | 19.19 |
| weekly_noise | 15 | exponential | 615.90 | 37.17 |
| weekly_noise | 15 | weekday | 265.78 | 16.04 |
| weekly_noise | 15 | adaptive | 377.05 | 22.75 |
| weekly_noise | 30 | moving_average | 242.01 | 6.83 |
| weekly_noise | 30 | last_week | 535.06 | 15.09 |
| weekly_noise | 30 | exponential | 962.10 | 27.13 |
| weekly_noise | 30 | weekday | 104.25 | 2.94 |
| weekly_noise | 30 | adaptive | 104.25 | 2.94 |
| weekly_noise | 90 | moving_average | 745.52 | 7.09 |
| weekly_noise | 90 | last_week | 2551.11 | 24.27 |
| weekly_noise | 90 | exponential | 2851.38 | 27.12 |
| weekly_noise | 90 | weekday | 597.26 | 5.68 |
| weekly_noise | 90 | adaptive | 697.46 | 6.63 |
| trend_break | 7 | moving_average | 100.16 | 7.96 |
| trend_break | 7 | last_week | 123.95 | 9.86 |
| trend_break | 7 | exponential | 176.92 | 14.07 |
| trend_break | 7 | weekday | 102.15 | 8.12 |
| trend_break | 7 | adaptive | 137.95 | 10.97 |
| trend_break | 15 | moving_average | 136.40 | 5.27 |
| trend_break | 15 | last_week | 616.49 | 23.81 |
| trend_break | 15 | exponential | 703.24 | 27.16 |
| trend_break | 15 | weekday | 192.98 | 7.45 |
| trend_break | 15 | adaptive | 384.11 | 14.83 |
| trend_break | 30 | moving_average | 1752.98 | 30.95 |
| trend_break | 30 | last_week | 1296.54 | 22.89 |
| trend_break | 30 | exponential | 1084.84 | 19.15 |
| trend_break | 30 | weekday | 1715.49 | 30.29 |
| trend_break | 30 | adaptive | 1725.40 | 30.46 |
| trend_break | 90 | moving_average | 2656.58 | 26.61 |
| trend_break | 90 | last_week | 4088.24 | 40.95 |
| trend_break | 90 | exponential | 3348.68 | 33.55 |
| trend_break | 90 | weekday | 2528.66 | 25.33 |
| trend_break | 90 | adaptive | 2656.58 | 26.61 |
| sparse_invoices | 7 | moving_average | 883.95 | 112.00 |
| sparse_invoices | 7 | last_week | 1543.98 | 195.62 |
| sparse_invoices | 7 | exponential | 1393.56 | 176.56 |
| sparse_invoices | 7 | weekday | 911.74 | 115.52 |
| sparse_invoices | 7 | adaptive | 883.95 | 112.00 |
| sparse_invoices | 15 | moving_average | 411.66 | 184.26 |
| sparse_invoices | 15 | last_week | 290.92 | 130.21 |
| sparse_invoices | 15 | exponential | 322.08 | 144.16 |
| sparse_invoices | 15 | weekday | 349.38 | 156.38 |
| sparse_invoices | 15 | adaptive | 373.72 | 167.27 |
| sparse_invoices | 30 | moving_average | 1037.65 | 148.36 |
| sparse_invoices | 30 | last_week | 3685.32 | 526.93 |
| sparse_invoices | 30 | exponential | 2840.50 | 406.13 |
| sparse_invoices | 30 | weekday | 1269.03 | 181.45 |
| sparse_invoices | 30 | adaptive | 1037.65 | 148.36 |
| sparse_invoices | 90 | moving_average | 1278.94 | 67.73 |
| sparse_invoices | 90 | last_week | 9290.86 | 492.03 |
| sparse_invoices | 90 | exponential | 5270.35 | 279.11 |
| sparse_invoices | 90 | weekday | 829.89 | 43.95 |
| sparse_invoices | 90 | adaptive | 1203.42 | 63.73 |
| near_zero_net | 7 | moving_average | 3.58 | 85.61 |
| near_zero_net | 7 | last_week | 4.12 | 98.57 |
| near_zero_net | 7 | exponential | 3.12 | 74.69 |
| near_zero_net | 7 | weekday | 3.47 | 82.95 |
| near_zero_net | 7 | adaptive | 3.68 | 87.92 |
| near_zero_net | 15 | moving_average | 5.09 | 118.37 |
| near_zero_net | 15 | last_week | 6.90 | 160.36 |
| near_zero_net | 15 | exponential | 3.06 | 71.12 |
| near_zero_net | 15 | weekday | 5.51 | 128.20 |
| near_zero_net | 15 | adaptive | 3.06 | 71.12 |
| near_zero_net | 30 | moving_average | 15.76 | 116.24 |
| near_zero_net | 30 | last_week | 25.99 | 191.67 |
| near_zero_net | 30 | exponential | 25.84 | 190.57 |
| near_zero_net | 30 | weekday | 16.37 | 120.74 |
| near_zero_net | 30 | adaptive | 15.76 | 116.24 |
| near_zero_net | 90 | moving_average | 27.99 | 148.37 |
| near_zero_net | 90 | last_week | 59.06 | 313.07 |
| near_zero_net | 90 | exponential | 27.89 | 147.82 |
| near_zero_net | 90 | weekday | 25.92 | 137.39 |
| near_zero_net | 90 | adaptive | 29.08 | 154.13 |
| volatile_shocks | 7 | moving_average | 753.28 | 81.62 |
| volatile_shocks | 7 | last_week | 1301.44 | 141.01 |
| volatile_shocks | 7 | exponential | 1390.11 | 150.62 |
| volatile_shocks | 7 | weekday | 759.85 | 82.33 |
| volatile_shocks | 7 | adaptive | 753.28 | 81.62 |
| volatile_shocks | 15 | moving_average | 1362.05 | 77.05 |
| volatile_shocks | 15 | last_week | 3355.54 | 189.83 |
| volatile_shocks | 15 | exponential | 3394.95 | 192.06 |
| volatile_shocks | 15 | weekday | 1393.31 | 78.82 |
| volatile_shocks | 15 | adaptive | 1362.05 | 77.05 |
| volatile_shocks | 30 | moving_average | 2556.98 | 108.39 |
| volatile_shocks | 30 | last_week | 2848.87 | 120.77 |
| volatile_shocks | 30 | exponential | 3151.97 | 133.61 |
| volatile_shocks | 30 | weekday | 2665.06 | 112.97 |
| volatile_shocks | 30 | adaptive | 2596.98 | 110.09 |
| volatile_shocks | 90 | moving_average | 2170.05 | 32.90 |
| volatile_shocks | 90 | last_week | 3378.75 | 51.23 |
| volatile_shocks | 90 | exponential | 3037.87 | 46.06 |
| volatile_shocks | 90 | weekday | 2204.67 | 33.43 |
| volatile_shocks | 90 | adaptive | 2170.05 | 32.90 |
| short_history | 7 | moving_average | None | None |
| short_history | 7 | last_week | None | None |
| short_history | 7 | exponential | None | None |
| short_history | 7 | weekday | None | None |
| short_history | 7 | adaptive | None | None |
| short_history | 15 | moving_average | None | None |
| short_history | 15 | last_week | None | None |
| short_history | 15 | exponential | None | None |
| short_history | 15 | weekday | None | None |
| short_history | 15 | adaptive | None | None |
| short_history | 30 | moving_average | None | None |
| short_history | 30 | last_week | None | None |
| short_history | 30 | exponential | None | None |
| short_history | 30 | weekday | None | None |
| short_history | 30 | adaptive | None | None |
| short_history | 90 | moving_average | None | None |
| short_history | 90 | last_week | None | None |
| short_history | 90 | exponential | None | None |
| short_history | 90 | weekday | None | None |
| short_history | 90 | adaptive | None | None |
