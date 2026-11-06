from django.test import SimpleTestCase

from . import knn


class NormalizeTests(SimpleTestCase):
    def test_scales_each_column_to_0_1(self):
        out = knn.normalize([[0, 50], [10, 100], [5, 75]])
        self.assertEqual(out, [[0.0, 0.0], [1.0, 1.0], [0.5, 0.5]])

    def test_constant_column_becomes_zero(self):
        self.assertEqual(knn.normalize([[7, 1], [7, 2]]), [[0.0, 0.0], [0.0, 1.0]])


class DistanceTests(SimpleTestCase):
    def test_identical_vectors(self):
        self.assertEqual(knn.distance([1, 1, 1, 1], [1, 1, 1, 1]), 0.0)

    def test_weighted_euclidean(self):
        # first column weight 2: sqrt(2*1^2) = 1.4142...
        self.assertAlmostEqual(knn.distance([1, 0, 0, 0], [0, 0, 0, 0]), 2 ** 0.5)
        self.assertAlmostEqual(knn.distance([0, 1, 0, 0], [0, 0, 0, 0]), 1.0)


class NearestTests(SimpleTestCase):
    def setUp(self):
        v = knn.to_vector
        self.target = v(85000, 1.5, "good", 86)
        self.cands = [
            (v(85000, 1.5, "good", 86), "same"),
            (v(85000, 1.5, "good", 70), "battery differs"),
            (v(32000, 4.0, "poor", 60), "very different"),
            (v(85000, 0.5, "excellent", 95), "newer"),
        ]

    def test_exact_twin_is_first_with_zero_distance(self):
        d, payload = knn.nearest(self.target, self.cands, 1)[0]
        self.assertEqual(payload, "same")
        self.assertAlmostEqual(d, 0.0)

    def test_order_is_closest_first_and_far_phone_last(self):
        names = [p for _, p in knn.nearest(self.target, self.cands, 4)]
        self.assertEqual(names[0], "same")
        self.assertEqual(names[-1], "very different")

    def test_k_limits_results(self):
        self.assertEqual(len(knn.nearest(self.target, self.cands, 2)), 2)

    def test_empty_candidates(self):
        self.assertEqual(knn.nearest(self.target, [], 3), [])


class MarketCheckTests(SimpleTestCase):
    def phones(self, prices):
        return [(knn.to_vector(85000, 1.5, "good", 86), p) for p in prices]

    def test_average_of_k_nearest_rounded_to_100(self):
        check = knn.market_check(knn.to_vector(85000, 1.5, "good", 86),
                                 self.phones([60000, 62000, 65100]), price_of=lambda p: p)
        self.assertEqual(check.price, 62400)  # mean 62366.7 -> nearest 100
        self.assertEqual(len(check.neighbors), 3)

    def test_not_enough_data_returns_none(self):
        self.assertIsNone(knn.market_check(knn.to_vector(85000, 1.5, "good", 86),
                                           self.phones([60000, 62000]), price_of=lambda p: p))

    def test_age_buckets_match_formula_brackets(self):
        self.assertEqual([knn.age_bucket(a) for a in (0, 1, 2, 3, 6)], [0.5, 1.5, 2.5, 4.0, 4.0])
