import runpy
import unittest
from pathlib import Path

ROUTER = Path(__file__).resolve().parents[1] / ".local/bin/zoom-link-router"
router = runpy.run_path(str(ROUTER))
command = router["brave_command"]
BRAVE = ["/usr/bin/brave-browser-stable", "--password-store=basic"]
APP = BRAVE + ["--profile-directory=Profile 1"]


class ZoomLinkRouterTests(unittest.TestCase):
    def test_https_invite_keeps_original_query(self):
        query = "pwd=abc%2Bdef%3D&tk=registration%2Ftoken"
        for host in ("zoom.us", "school.zoom.us", "us02web.zoom.us", "zoom.com"):
            with self.subTest(host=host):
                self.assertEqual(
                    command(f"https://{host}/j/12345678901?{query}"),
                    APP + [f"--app=https://app.zoom.us/wc/join/12345678901?{query}"],
                )

    def test_personal_room_and_existing_join_urls(self):
        for path, expected in (
            ("/my/my.room/", "/wc/my/my.room"),
            ("/wc/my/my.room", "/wc/my/my.room"),
            ("/wc/123456789/join", "/wc/join/123456789"),
            ("/wc/join/123456789", "/wc/join/123456789"),
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    command(f"https://zoom.us{path}"),
                    APP + [f"--app=https://app.zoom.us{expected}"],
                )

    def test_native_launch_keeps_meeting_id_and_password(self):
        for scheme in ("zoommtg", "zoomus"):
            with self.subTest(scheme=scheme):
                self.assertEqual(
                    command(f"{scheme}://zoom.us/join?action=join&confno=12345678901&pwd=example%2Btoken"),
                    APP + ["--app=https://app.zoom.us/wc/join/12345678901?pwd=example%2Btoken"],
                )

    def test_native_launch_without_meeting_opens_zoom_home(self):
        for link in ("zoommtg://zoom.us", "zoomus://zoom.us/join?confno=invalid"):
            with self.subTest(link=link):
                self.assertEqual(command(link), APP + ["--app=https://app.zoom.us/wc/home?source=pwa"])

    def test_unrelated_urls_pass_unchanged_to_brave(self):
        for link in (
            "https://example.org/?a=one%20two&b=three#top",
            "http://localhost:8080/",
            "https://zoom.us.example.org/j/12345678901",
            "https://example.org@zoom.us/j/12345678901",
            "https://zoom.us/webinar/register/12345678901",
            "https://zoom.us/my/..",
            "https://zoom.us/j/not-a-meeting",
        ):
            with self.subTest(link=link):
                self.assertEqual(command(link), BRAVE + ["--", link])
        self.assertEqual(command(None), BRAVE)


if __name__ == "__main__":
    unittest.main()
