import unittest
from unittest.mock import patch

from cplus_camera import CameraConfig, CPPlusCamera


class CameraConfigTests(unittest.TestCase):
    def test_common_rtsp_url_is_generated(self):
        camera = CPPlusCamera(CameraConfig("192.0.2.50", "viewer", "p@ss word", channel=2, subtype=1))
        self.assertEqual(
            camera.rtsp_url(),
            "rtsp://viewer:p%40ss%20word@192.0.2.50:554/cam/realmonitor?channel=2&subtype=1",
        )

    def test_rejects_host_with_path(self):
        with self.assertRaises(ValueError):
            CameraConfig("http://192.0.2.50/path", "viewer", "password")

    def test_reads_configured_channels(self):
        camera = CPPlusCamera(CameraConfig("192.0.2.50", "viewer", "password"))
        response = (
            b"table.ChannelTitle[0].Name=Front Door\n"
            b"table.ChannelTitle[1].Name=Parking\n"
        )
        with patch.object(camera, "_get", return_value=response):
            channels = camera.channels()
        self.assertEqual([(item.number, item.name) for item in channels], [(1, "Front Door"), (2, "Parking")])


if __name__ == "__main__":
    unittest.main()
