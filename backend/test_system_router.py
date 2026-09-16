from execution.system_router import SystemCommandRouter
from tools.registry import ToolRegistry
from tools.system.volume import VolumeControlTool


class FakeAudioController:
    def __init__(self):
        self.volume = 50
        self.muted = False

    def get_volume(self):
        return self.volume

    def set_volume(self, percentage):
        self.volume = percentage
        return self.volume

    def volume_up(self, step=None):
        step = step or 10
        self.volume = min(100, self.volume + step)
        return self.volume

    def volume_down(self, step=None):
        step = step or 10
        self.volume = max(0, self.volume - step)
        return self.volume

    def mute(self):
        self.muted = True

    def unmute(self):
        self.muted = False

    def is_muted(self):
        return self.muted


controller = FakeAudioController()

registry = ToolRegistry()
registry.register(
    VolumeControlTool(controller=controller)
)

router = SystemCommandRouter(registry)


commands = [
    "volume up",
    "increase volume",
    "increase the volume",
    "turn the volume up",
    "volume down",
    "decrease volume",
    "turn the volume down",
    "mute",
    "unmute",
    "set volume to 40",
    "set volume to 55 percent",
    "volume 60",
    "volume 60 percent",
    "increase the volume to 50",
    "increase the volume to 16",
    "decrease the volume to 25",
    "what is the volume",
    "whats the volume",
    "what's the volume",
    "check the volume",
    "current volume",
    "volume",
    "open chrome",
]


for command in commands:
    result = router.route(command)

    print(f"\nCOMMAND: {command}")
    print(f"RESULT : {result}")


print("\nSYSTEM ROUTER TEST COMPLETED")