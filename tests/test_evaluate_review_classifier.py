from models.evaluate_review_classifier import build_error_rows


def test_build_error_rows_separates_false_positive_and_false_negative():
    class FakeSeries:
        def __init__(self, values):
            self._values = values

        def tolist(self):
            return list(self._values)

    import pandas as pd

    metadata = pd.DataFrame(
        [
            {"publication_id": "pub1", "critic_name": "Critic 1", "headline": "A", "rt_quote": "Q1", "review_url": "u1"},
            {"publication_id": "pub2", "critic_name": "Critic 2", "headline": "B", "rt_quote": "Q2", "review_url": "u2"},
        ]
    )

    errors = build_error_rows(
        X_test=None,
        y_test=FakeSeries([0, 1]),
        probs=[0.9, 0.1],
        preds=FakeSeries([1, 0]),
        metadata_test=metadata,
    )

    assert len(errors) == 2
    assert errors[0]["error_type"] == "false_positive"
    assert errors[1]["error_type"] == "false_negative"
