;; Example MeTTa rules — human readable / doc for mapping to real MeTTa syntax

(rule accept_by_return_and_risk
  (Investor ?INV (risk_tolerance ?R))
  (Asset ?A (expected_return ?ER) (volatility ?V))
  =>
  (let thresholds = (risk_thresholds_for ?R))
  (if (and (>= ?ER thresholds.min_return) (<= ?V thresholds.max_volatility))
      (assert (Decision ?A accept "return_and_risk_ok" (score compute_score ?ER ?V)))
      (assert (Decision ?A deprioritize "low_return_or_high_volatility" (score compute_score ?ER ?V))))
)
