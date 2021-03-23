from rest_framework import status
from main.tests.full_setup import FullSetUp


class TestMisc(FullSetUp):
    def test_get_position_first_visit_main_world(self):
        """
        API: /api/position/
        Test get position for main world (Campaign world) for the first time.
        """

        res = self.client.get("/api/position/")
        print(res.data)
        # Status check
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Data check

        # First level in Campaign mode.
        data = {
            'world_id': 1,
            'section_id': 1,
            'level_id': 1
        }

        self.assertEqual(res.data, data)
