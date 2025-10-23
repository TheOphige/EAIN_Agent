;; Example ethical rules expressed in MeTTa-like pseudo-syntax

(rule exclude_by_industry
  (Investor ?INV (excluded_industries ?EX))
  (Asset ?A (sector ?S))
  =>
  (if (contains ?EX ?S)
      (assert (Decision ?A reject "excluded_industry" (evidence sector ?S)))
      (nop))
)
