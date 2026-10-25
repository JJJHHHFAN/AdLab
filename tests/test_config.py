from adlab.config import EXPERIMENTS, get_experiment


def test_navigation_contains_all_planned_sections_in_order():
    assert [experiment.slug for experiment in EXPERIMENTS] == [
        "home",
        "auction",
        "ctr",
        "budget",
        "ab_test",
        "bandit",
        "records",
        "docs",
    ]


def test_experiment_identifiers_are_unique_and_lookup_is_stable():
    slugs = [experiment.slug for experiment in EXPERIMENTS]
    assert len(slugs) == len(set(slugs))
    for experiment in EXPERIMENTS:
        assert get_experiment(experiment.slug) is experiment


def test_future_experiments_are_not_marked_complete():
    assert all(experiment.status == "planned" for experiment in EXPERIMENTS[1:])
