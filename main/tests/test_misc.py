from random import randrange

from rest_framework import status

from main.GameManager import GameManager
from main.models import UserLevelProgressRecord, Level, World
from main.tests.full_setup import FullSetUp


class TestMisc(FullSetUp):
    def test_get_position_first_visit_main_world(self):
        """
        API: /api/position/
        Test get position for main world (Campaign world) for the first time.
        """

        res = self.client.get("/api/position/")
        # Status check
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Data check
        # First level in Campaign mode.
        data = {
            'world_id': 1,
            'section_id': 1,
            'level_id': 1,
            'has_completed': False
        }

        self.assertEqual(res.data, data)

    def test_get_position_main_world(self):
        """
        API: /api/position/
        Test get position for main world (Campaign world) when there is existing progress.
        """

        # Set user progress randomly
        # position_id = randrange(1, self.total_levels+1)
        # level = Level.objects.get(id=position_id)
        # UserLevelProgressRecord.objects.create(
        #     user=self.user,
        #     level=level
        # )

        gm = GameManager(self.user)
        level = gm.get_user_position_in_world()  # Init the first level
        rand_lvl = randrange(0, self.total_levels)  # start from level 2
        for i in range(0, rand_lvl):
            level = gm.complete_level(level)

        res = self.client.get("/api/position/")

        # Status check
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Data check
        data = {
            'world_id': level.section.world_id,
            'section_id': level.section.id,
            'level_id': level.id,
            'has_completed': False
        }

        self.assertEqual(res.data, data)

    def test_get_position_last_level_uncompleted(self):
        """
        API: /api/position/
        Test get position when user reached the last level and level
        uncompleted.
        """

        level = Level.objects.get(id=self.total_levels)
        UserLevelProgressRecord.objects.create(
            user=self.user,
            level=level
        )

        # gm = GameManager(self.user)
        # level = gm.get_user_position_in_world()  # Init the first level
        # rand_lvl = randrange(0, self.total_levels)  # start from level 2
        # for i in range(0, rand_lvl):
        #     level = gm.complete_level(level)

        res = self.client.get("/api/position/")

        # Status check
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Data check
        data = {
            'world_id': level.section.world_id,
            'section_id': level.section.id,
            'level_id': level.id,
            'has_completed': False
        }

        self.assertEqual(res.data, data)

    def test_get_position_last_level_completed(self):
        """
        API: /api/position/
        Test get position when user reached the last level and level
        completed.
        """

        level = Level.objects.get(id=self.total_levels)
        UserLevelProgressRecord.objects.create(
            user=self.user,
            level=level,
            is_completed=True,
        )

        res = self.client.get("/api/position/")

        # Status check
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Data check
        data = {
            'world_id': level.section.world_id,
            'section_id': level.section.id,
            'level_id': level.id,
            'has_completed': True
        }

        self.assertEqual(res.data, data)
