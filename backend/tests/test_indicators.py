from app.data import indicators as ind


def test_sma_and_rsi():
    vals = list(range(1, 31))
    assert ind.sma(vals, 5)[-1] == 28
    assert ind.rsi(vals) == 100.0
    assert ind.rsi(list(reversed(vals))) < 1


def test_drawdown_and_summary():
    assert ind.max_drawdown([100, 120, 60, 90]) == -0.5
    s = ind.summarize([float(i) for i in range(1, 300)])
    assert s["trend"] == "uptrend" and s["sma200"] is not None


def test_news_scoring():
    from app.data.news import score_text

    assert score_text("Shares surge after record profit") > 0
    assert score_text("Stock plunges on lawsuit and downgrade") < 0
    assert score_text("Company holds meeting") == 0
