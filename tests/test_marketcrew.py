import math
import tempfile
import unittest
from pathlib import Path

from marketcrew import agents, pipeline
from marketcrew.llm import MockLLM


class Maths(unittest.TestCase):
    def test_cagr(self):
        self.assertAlmostEqual(agents.cagr(100, 200, 1), 1.0)
        self.assertAlmostEqual(agents.cagr(100, 121, 2), 0.10)
        with self.assertRaises(ValueError):
            agents.cagr(0, 10, 3)


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.p = agents.plan("Which fast charging players grow fastest?")
        self.ev = agents.collect(pipeline.DATA, self.p)
        self.f = agents.analyse(self.ev)

    def test_numbers_match_source_data(self):
        x = self.f.facts
        self.assertEqual(x["total"][2025], 520 + 320 + 90 + 310)
        self.assertAlmostEqual(sum(x["shares"].values()), 1.0)
        self.assertEqual((x["leader"], x["fastest"], x["slowest"]), ("VoltGrid", "AmpWorks", "PlugLoop"))
        self.assertAlmostEqual(x["growth"]["AmpWorks"], (310 / 60) ** 0.25 - 1)

    def test_hhi_bounds(self):
        self.assertTrue(1000 < self.f.facts["hhi"] < 10000)

    def test_keyword_relevance_ordering(self):
        self.assertIn("fast", self.ev.snippets[0][1].lower())

    def test_swot_cites_valid_sources(self):
        import re
        cited = {m for bullets in self.f.swot.values() for b in bullets for m in re.findall(r"\[(S\d+)\]", b)}
        self.assertTrue(cited and cited <= set(self.f.sources))

    def test_report_offline_and_with_llm(self):
        rep = pipeline.run("Which fast charging players grow fastest?", llm=MockLLM())
        for part in ("## Executive summary", "## Competition", "### Threats", "## Sources", "VoltGrid"):
            self.assertIn(part, rep)
        llm = MockLLM(lambda s, p: "LLM SUMMARY [S0]")
        rep2 = pipeline.run("q", llm=llm)
        self.assertIn("LLM SUMMARY", rep2)
        self.assertIn("ONLY these facts", llm.calls[0][1])

    def test_trace_has_four_agents(self):
        trace = []
        pipeline.run("q", trace=trace, llm=MockLLM())
        self.assertEqual([a for a, _ in trace], ["planner", "collector", "analyst", "writer"])

    def test_custom_dataset(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "notes").mkdir()
            (Path(d) / "market.csv").write_text("company,year,revenue_musd,segment\nA,2020,10,x\nA,2022,40,x\nB,2020,10,y\nB,2022,10,y\n")
            f = agents.analyse(agents.collect(d, agents.plan("anything here")))
            self.assertAlmostEqual(f.facts["growth"]["A"], 1.0)
            self.assertEqual(f.facts["fastest"], "A")


if __name__ == "__main__":
    unittest.main()
