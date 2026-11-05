import asyncio


async def _wait_done(client, job_id, timeout=30):
    for _ in range(int(timeout / 0.25)):
        j = (await client.get(f"/api/research/{job_id}")).json()
        if j["status"] in ("completed", "failed"):
            return j
        await asyncio.sleep(0.25)
    raise AssertionError("job did not finish")


async def test_health_and_config(client):
    assert (await client.get("/api/health")).json() == {"status": "ok"}
    cfg = (await client.get("/api/config")).json()
    assert cfg["llm"]["enabled"] is False


async def test_full_research_flow(client):
    r = await client.post("/api/research", json={"query": "Compare Apple and Microsoft outlook", "depth": "deep"})
    assert r.status_code == 202
    job = await _wait_done(client, r.json()["id"])
    assert job["status"] == "completed", job.get("error")
    rep = job["report"]
    assert {i["symbol"] for i in rep["instruments"]} == {"AAPL", "MSFT"}
    assert rep["recommendation"]["stance"] in ("Bullish", "Neutral", "Bearish")
    assert rep["data_quality"] == "synthetic" and rep["review_notes"]
    assert "## Executive Summary" in rep["markdown"]
    events = (await client.get(f"/api/research/{job['id']}/events")).json()
    assert {"planner", "collector", "analyst", "writer", "reviewer"} <= {e["agent"] for e in events}
    md = await client.get(f"/api/research/{job['id']}/export?format=md")
    assert md.status_code == 200 and md.text.startswith("# ")
    page = (await client.get("/api/research?q=apple")).json()
    assert page["total"] >= 1
    stats = (await client.get("/api/dashboard/stats")).json()
    assert stats["completed"] >= 1
    assert (await client.delete(f"/api/research/{job['id']}")).status_code == 204
    assert (await client.get(f"/api/research/{job['id']}")).status_code == 404


async def test_validation(client):
    assert (await client.post("/api/research", json={"query": "x"})).status_code == 422


async def test_watchlist_and_market(client):
    assert (await client.post("/api/watchlist", json={"symbol": "nvda"})).status_code == 201
    assert (await client.post("/api/watchlist", json={"symbol": "NVDA"})).status_code == 409
    items = (await client.get("/api/watchlist/quotes")).json()
    assert items[0]["symbol"] == "NVDA" and items[0]["quote"]["price"] > 0
    assert (await client.delete("/api/watchlist/NVDA")).status_code == 204
    h = (await client.get("/api/market/history/TSLA?range=3mo")).json()
    assert len(h["series"]) > 40 and h["indicators"]["rsi14"] is not None
    assert len((await client.get("/api/market/overview")).json()) == 6
    assert (await client.get("/api/market/search?q=micro")).json()[0]["symbol"] == "MSFT"


async def test_sse_stream(client):
    r = await client.post("/api/research", json={"query": "Tesla quick look", "depth": "quick"})
    jid = r.json()["id"]
    async with client.stream("GET", f"/api/research/{jid}/stream") as resp:
        text = ""
        async for chunk in resp.aiter_text():
            text += chunk
    assert "event: done" in text and "event: end" in text
