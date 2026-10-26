import unittest

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


if __name__ == "__main__":
    unittest.main()
