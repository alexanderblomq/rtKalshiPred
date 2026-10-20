from models.trainer import build_training_frame


def test_build_training_frame_creates_expected_columns():
    rows = [
        {
            "publication_id": "variety",
            "critic_name": "Critic One",
            "headline": "A terrific movie",
            "rt_quote": "Sharp and wonderful.",
            "body_text": "Longer review body.",
            "fresh_label": 1,
            "original_score": "4/5",
        },
        {
            "publication_id": "411mania",
            "critic_name": "Critic Two",
            "headline": "A dull mess",
            "rt_quote": "Weak and disappointing.",
            "body_text": "Another review body.",
            "fresh_label": 0,
            "original_score": None,
        },
    ]
    frame = build_training_frame(rows)
    assert list(frame.columns) == [
        "combined_text",
        "publication_id",
        "critic_name",
        "normalized_score",
        "fresh_label",
    ]
    assert len(frame) == 2
    assert frame.iloc[0]["normalized_score"] == 0.8


def test_build_training_frame_uses_critic_names_when_primary_name_missing():
    rows = [
        {
            "publication_id": "variety",
            "critic_names": ["Critic One", "Critic Alias"],
            "headline": "A terrific movie",
            "fresh_label": 1,
            "original_score": "4/5",
        }
    ]

    frame = build_training_frame(rows)

    assert frame.iloc[0]["critic_name"] == "Critic One"
