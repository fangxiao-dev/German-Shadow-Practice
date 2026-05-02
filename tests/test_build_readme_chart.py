from datetime import date

from scripts.build_readme_chart import (
    build_svg,
    build_week_grid,
    compute_stats,
    get_color_level,
    load_daily_counts,
)


def test_load_daily_counts_aggregates_by_date(tmp_path):
    yaml_file = tmp_path / "assets.yaml"
    yaml_file.write_text(
        "- {created_at: '2026-04-13'}\n"
        "- {created_at: '2026-04-13'}\n"
        "- {created_at: '2026-04-14'}\n",
        encoding="utf-8",
    )
    counts = load_daily_counts(str(yaml_file))
    assert counts == {date(2026, 4, 13): 2, date(2026, 4, 14): 1}


def test_load_daily_counts_empty_file(tmp_path):
    yaml_file = tmp_path / "assets.yaml"
    yaml_file.write_text("[]", encoding="utf-8")
    assert load_daily_counts(str(yaml_file)) == {}


def test_compute_stats_basic():
    counts = {date(2026, 4, 13): 33, date(2026, 4, 14): 11}
    study_days, total_words, avg = compute_stats(counts)
    assert study_days == 2
    assert total_words == 44
    assert avg == 22.0


def test_compute_stats_rounds_avg():
    counts = {
        date(2026, 4, 13): 10,
        date(2026, 4, 14): 11,
        date(2026, 4, 15): 12,
    }
    _, total, avg = compute_stats(counts)
    assert total == 33
    assert avg == 11.0


def test_compute_stats_empty():
    study_days, total_words, avg = compute_stats({})
    assert study_days == 0
    assert total_words == 0
    assert avg == 0.0


def test_get_color_level_zero_returns_zero():
    assert get_color_level(0, 33) == 0


def test_get_color_level_max_returns_four():
    assert get_color_level(33, 33) == 4


def test_get_color_level_bands():
    assert get_color_level(1, 100) == 1
    assert get_color_level(25, 100) == 1
    assert get_color_level(26, 100) == 2
    assert get_color_level(50, 100) == 2
    assert get_color_level(51, 100) == 3
    assert get_color_level(75, 100) == 3
    assert get_color_level(76, 100) == 4


def test_get_color_level_max_zero_returns_zero():
    assert get_color_level(0, 0) == 0


def test_build_week_grid_returns_12_weeks():
    today = date(2026, 5, 1)
    grid = build_week_grid({}, today)
    assert len(grid) == 12


def test_build_week_grid_each_week_has_7_days():
    today = date(2026, 5, 1)
    grid = build_week_grid({}, today)
    for week in grid:
        assert len(week) == 7


def test_build_week_grid_last_cell_is_today_or_later():
    today = date(2026, 5, 1)
    grid = build_week_grid({}, today)
    last_week = grid[-1]
    assert last_week[4][0] == today


def test_build_week_grid_future_days_are_not_activity_cells():
    today = date(2026, 5, 1)
    grid = build_week_grid({}, today)
    last_week = grid[-1]
    assert last_week[5][1] is None
    assert last_week[6][1] is None


def test_build_week_grid_assigns_levels():
    today = date(2026, 5, 1)
    counts = {date(2026, 4, 29): 16, date(2026, 4, 30): 16}
    grid = build_week_grid(counts, today)
    apr29_week = next(w for w in grid if w[2][0] == date(2026, 4, 29))
    assert apr29_week[2][1] == 4
    assert apr29_week[3][1] == 4


def test_build_week_grid_uses_window_max_not_historical_max():
    today = date(2026, 5, 1)
    counts = {
        date(2025, 12, 1): 1000,
        date(2026, 4, 29): 16,
    }
    grid = build_week_grid(counts, today)
    apr29_week = next(w for w in grid if w[2][0] == date(2026, 4, 29))
    assert apr29_week[2][1] == 4


def _make_grid():
    today = date(2026, 5, 1)
    counts = {
        date(2026, 4, 13): 33,
        date(2026, 4, 14): 11,
        date(2026, 4, 21): 26,
        date(2026, 4, 26): 5,
        date(2026, 4, 29): 16,
        date(2026, 4, 30): 16,
        date(2026, 5, 1): 20,
    }
    return counts, build_week_grid(counts, today)


def test_build_svg_is_valid_xml():
    counts, grid = _make_grid()
    stats = compute_stats(counts)
    svg = build_svg(stats, grid)
    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")


def test_build_svg_contains_stat_values():
    counts, grid = _make_grid()
    stats = compute_stats(counts)
    svg = build_svg(stats, grid)
    assert ">7<" in svg
    assert ">127<" in svg
    assert ">18.1<" in svg


def test_build_svg_contains_only_rendered_day_cells():
    counts, grid = _make_grid()
    stats = compute_stats(counts)
    svg = build_svg(stats, grid)
    assert svg.count('class="day"') == 82


def test_build_svg_contains_orange_cells():
    counts, grid = _make_grid()
    stats = compute_stats(counts)
    svg = build_svg(stats, grid)
    assert "#f0883e" in svg or "#d36820" in svg
