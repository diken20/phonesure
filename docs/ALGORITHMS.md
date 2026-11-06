# PhoneSure algorithms (for the System Design chapter)

| # | Algorithm | File | Where the user meets it |
|---|-----------|------|--------------------------|
| 1 | Weighted-depreciation valuation | backend/valuation/engine.py | Calculator page; "Fair range" in My Phones and on every listing |
| 2 | Rule-based trust score | backend/phones/trust.py | "Trust x/100" badge on cards, trust breakdown on the phone page |
| 3 | KMP string search (Knuth, Morris, Pratt, 1977) | backend/marketplace/kmp.py | Search box in the marketplace |
| 4 | K-Nearest Neighbors (Cover and Hart, 1967) | backend/valuation/knn.py | "Market check" in the calculator and on a phone page; "Similar phones you may like" |

## 1. Weighted-depreciation valuation
    Estimate = Base x AgeFactor x ConditionFactor x BatteryFactor + AccessoriesBonus
    Range    = Estimate -7% .. +7%   (rounded to Rs. 100)
    Age:  <1y 1.00 | 1-2y 0.85 | 2-3y 0.72 | 3y+ 0.60      Condition: 1.00 / 0.90 / 0.75 / 0.55
    Battery: >=90 1.00 | 80-89 0.95 | 70-79 0.88 | <70 0.78     Bonus: box 500, charger 500, bill 1000
Complexity O(1). Each factor's effect is stored as a step so the user can see why the price changed.

## 2. Trust score (out of 100)
    bill 20 + warranty left 15 + battery > 80% 20 + no repairs 20 + box 5 + charger 5 + photo 15
Complexity O(1). Every rule is returned with earned / not earned.

## 3. KMP search
    build failure table F for pattern P            // F[i] = longest proper prefix of P[0..i] that is also a suffix
    matched <- 0
    for each character c of text T:
        while matched > 0 and c != P[matched]: matched <- F[matched - 1]
        if c == P[matched]: matched <- matched + 1
        if matched == |P|: return index of the match
    return not found
Complexity O(n + m) time, O(m) space. The text searched is "brand model storage condition" of each LISTED phone.
Each word typed by the buyer must be found (AND), so "128gb iphone" finds "Apple iPhone 13 128GB".

## 4. K-Nearest Neighbors (K = 3)
    vector(phone) = [model base price, age bracket, condition score 1..4, battery %]
    1. put the target and all listed phones in one table; min-max scale every column to 0..1
    2. d(a, b) = sqrt( sum_i w_i * (a_i - b_i)^2 )      with weights (2, 1, 1, 1): the model counts double
    3. sort candidates by d and keep the K smallest
    4. market price = average asking price of those K phones (rounded to Rs. 100)
    5. fewer than K listed phones -> no market check, the app shows only the formula range
Complexity O(N log N) for N listed phones. No library is used. Weakness to discuss: needs enough listings
(the demo data has 8); prices are asking prices, not final sale prices.
