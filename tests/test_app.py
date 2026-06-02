"""Tests for WhiskerShelf app. Uses stdlib unittest only."""
import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from pathlib import Path

from app import build_cc_project


class SanityTest(unittest.TestCase):
    def test_truth(self):
        self.assertTrue(True)


class BuildCCProjectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.session = {
            "id": "1234567890",
            "time": 1234567890,
            "papers": [
                {"name": "a.pdf", "title": "Paper A", "abstract": "Abs A",
                 "tags": ["linear-attention"], "notes": ""},
                {"name": "b.pdf", "title": "Paper B", "abstract": "Abs B",
                 "tags": ["snn"], "notes": ""},
            ],
            "user_context": "test context",
            "result": "# Brief\n\n## 1. Common themes\n..."
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_creates_directory(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        self.assertTrue(result_path.exists())
        self.assertTrue(result_path.is_dir())

    def test_writes_brief_md(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        self.assertEqual((result_path / "brief.md").read_text(encoding="utf-8"),
                         self.session["result"])

    def test_writes_selected_papers_json(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        data = json.loads((result_path / "selected-papers.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "a.pdf")

    def test_writes_claude_md_with_skills_section(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        claude_md = (result_path / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("whiskershelf-brief", claude_md)
        self.assertIn("whiskershelf-search", claude_md)
        self.assertIn("whiskershelf-tag", claude_md)

    def test_writes_start_claude_bat(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        bat = (result_path / "start-claude.bat").read_text(encoding="utf-8")
        self.assertIn("claude", bat.lower())

    def test_writes_start_claude_sh(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        sh = (result_path / "start-claude.sh").read_text(encoding="utf-8")
        self.assertIn("claude", sh.lower())

    def test_copies_skill_files(self):
        target = Path(self.tmp) / "brief-1234"
        result_path = build_cc_project(self.session, target)
        skills_dir = result_path / ".claude" / "skills"
        self.assertTrue((skills_dir / "whiskershelf-brief" / "SKILL.md").exists())
        self.assertTrue((skills_dir / "whiskershelf-search" / "SKILL.md").exists())
        self.assertTrue((skills_dir / "whiskershelf-tag" / "SKILL.md").exists())


from app import PaperHandler


class _LiveServer:
    """Context manager that runs PaperHandler on a random port in a thread."""
    def __enter__(self):
        self.server = HTTPServer(("127.0.0.1", 0), PaperHandler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        # Tiny sleep to let the server bind (usually unnecessary but harmless)
        time.sleep(0.05)
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()


class ExportCCProjectEndpointTest(unittest.TestCase):
    def test_missing_session_id_returns_400(self):
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/idea-spark/export-cc-project",
                data=json.dumps({}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req)
            self.assertEqual(ctx.exception.code, 400)

    def test_export_with_valid_session_writes_directory(self):
        # Seed a session directly in the history file
        from app import add_idea_spark_session
        sess = add_idea_spark_session(
            papers_info=[{"name": "a.pdf", "title": "A", "abstract": "x", "tags": [], "notes": ""}],
            user_context="ctx",
            result_content="# brief",
        )
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            target = Path(tempfile.mkdtemp()) / "out"
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/idea-spark/export-cc-project",
                data=json.dumps({"session_id": sess["id"], "target_dir": str(target)}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
            self.assertTrue(data["success"])
            self.assertTrue((target / "brief.md").exists())
            self.assertTrue((target / "CLAUDE.md").exists())
            import shutil
            shutil.rmtree(target.parent, ignore_errors=True)


class ExportCCDefaultPathTest(unittest.TestCase):
    def test_empty_target_dir_uses_default(self):
        from app import add_idea_spark_session
        sess = add_idea_spark_session(
            papers_info=[{"name": "a.pdf", "title": "A", "abstract": "x", "tags": [], "notes": ""}],
            user_context="ctx",
            result_content="# brief",
        )
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/idea-spark/export-cc-project",
                data=json.dumps({"session_id": sess["id"], "target_dir": ""}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
        self.assertTrue(data["success"])
        self.assertIn("whiskershelf-brief-", data["path"])
        import shutil
        shutil.rmtree(data["path"], ignore_errors=True)


class AgentPapersListTest(unittest.TestCase):
    def test_returns_paper_list(self):
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/agent/papers") as r:
                data = json.loads(r.read())
        self.assertIn("papers", data)
        self.assertIsInstance(data["papers"], list)
        # Each paper has at minimum: name, title, abstract_preview
        if data["papers"]:
            p = data["papers"][0]
            self.assertIn("name", p)
            self.assertIn("title", p)
            self.assertIn("abstract_preview", p)


class AgentPaperDetailTest(unittest.TestCase):
    def test_returns_full_paper_detail(self):
        # Pick a real paper name from the live filesystem
        from app import ROOT
        pdfs = [p.name for p in ROOT.iterdir() if p.suffix.lower() == ".pdf"]
        if not pdfs:
            self.skipTest("No PDFs in project root to test against")
        name = pdfs[0]
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            encoded = urllib.parse.quote(name, safe="")
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/agent/papers/{encoded}") as r:
                data = json.loads(r.read())
        self.assertEqual(data["name"], name)
        self.assertIn("title", data)
        self.assertIn("abstract", data)
        self.assertIn("tags", data)
        self.assertIn("notes", data)

    def test_nonexistent_returns_404(self):
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/agent/papers/ghost.pdf")
            self.assertEqual(ctx.exception.code, 404)


class AgentSearchTest(unittest.TestCase):
    def test_search_returns_results(self):
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/agent/search",
                data=json.dumps({"query": "test"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
        # Each result: name, title, abstract_preview
        if data["results"]:
            item = data["results"][0]
            self.assertIn("name", item)
            self.assertIn("title", item)
            self.assertIn("abstract_preview", item)

    def test_empty_query_returns_empty_list(self):
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/agent/search",
                data=json.dumps({"query": ""}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
        self.assertEqual(data["results"], [])


class AgentTagReadTest(unittest.TestCase):
    def test_get_tags(self):
        from app import ROOT
        pdfs = [p.name for p in ROOT.iterdir() if p.suffix.lower() == ".pdf"]
        if not pdfs:
            self.skipTest("No PDFs in project root to test against")
        name = pdfs[0]
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            encoded = urllib.parse.quote(name, safe="")
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/agent/papers/{encoded}/tags") as r:
                data = json.loads(r.read())
        self.assertIn("tags", data)
        self.assertIsInstance(data["tags"], list)

    def test_get_tags_nonexistent_returns_404(self):
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen("http://127.0.0.1:{port}/api/agent/papers/ghost.pdf/tags".format(port=port))
            self.assertEqual(ctx.exception.code, 404)


class AgentTagWriteTest(unittest.TestCase):
    def test_set_tags(self):
        from app import ROOT
        pdfs = [p.name for p in ROOT.iterdir() if p.suffix.lower() == ".pdf"]
        if not pdfs:
            self.skipTest("No PDFs in project root to test against")
        name = pdfs[0]
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            encoded = urllib.parse.quote(name, safe="")
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/agent/papers/{encoded}/tags",
                data=json.dumps({"tags": ["test-tag-x", "test-tag-y"]}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
        self.assertTrue(data["success"])
        self.assertIn("test-tag-x", data["tags"])

    def test_invalid_name_returns_400(self):
        with _LiveServer() as srv:
            port = srv.server.server_address[1]
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/agent/papers//tags",
                data=json.dumps({"tags": ["x"]}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req)
            self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
