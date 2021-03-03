from main.models import UserLevelProgressRecord, UserWorldProgressRecord, World, Level, LevelPath, Section


class GameManager:
    def __init__(self, user):
        self.user = user

    def get_user_position_in_map(self):
        position = UserWorldProgressRecord.objects.filter(user=self.user, is_completed=False)

        # Instantiate the user position to the first world
        if not position:
            world = World.objects.all.order_by("index")[0]
            position = UserWorldProgressRecord.objects.create(
                user=self.user,
                world=world,
            )
        else:
            position = position[0]

        return position.world

    def get_user_position_in_world(self, world_id):
        position = UserLevelProgressRecord.objects.filter(user=self.user, is_completed=False)

        # Instantiate the user position to the first level
        if not position:
            level = Level.objects.all.order_by("index")[0]
            position = UserLevelProgressRecord.objects.create(
                user=self.user,
                level=level,
            )
        else:
            position = position[0]

        return position.level

    def check_access_to_level(self, level_id):
        world_position = self.get_user_position_in_map()
        position = self.get_user_position_in_world(world_position)
        next_level = Level.objects.filter(section=position.section, index__gt=position.index).order_by("index")[0]

        if level_id == next_level.id:
            return True
        else:
            return False
