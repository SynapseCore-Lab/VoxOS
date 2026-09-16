from __future__ import annotations

from typing import Optional

from pycaw.pycaw import AudioUtilities


class WindowsAudioController:
    """
    Windows master-volume controller using pycaw.

    Controls the default playback device.
    """

    DEFAULT_STEP = 10

    def __init__(self, default_step: int = DEFAULT_STEP) -> None:
        if not 1 <= default_step <= 100:
            raise ValueError("default_step must be between 1 and 100.")

        self.default_step = default_step

    @staticmethod
    def _get_volume_interface():
        """
        Get the EndpointVolume interface for the default
        Windows playback device.
        """

        device = AudioUtilities.GetSpeakers()

        return device.EndpointVolume

    def get_volume(self) -> int:
        """Return master volume as a percentage."""

        volume = self._get_volume_interface()

        current = volume.GetMasterVolumeLevelScalar()

        current = max(0.0, min(1.0, current))

        return round(current * 100)

    def set_volume(self, percentage: int) -> int:
        """Set master volume to 0-100%."""

        if not 0 <= percentage <= 100:
            raise ValueError("Volume must be between 0 and 100.")

        volume = self._get_volume_interface()

        scalar = percentage / 100.0

        volume.SetMasterVolumeLevelScalar(
            scalar,
            None,
        )

        return self.get_volume()

    def volume_up(self, step: Optional[int] = None) -> int:
        """Increase master volume."""

        if step is None:
            step = self.default_step

        if not 1 <= step <= 100:
            raise ValueError(
                "Volume step must be between 1 and 100."
            )

        current = self.get_volume()

        target = min(
            100,
            current + step,
        )

        return self.set_volume(target)

    def volume_down(self, step: Optional[int] = None) -> int:
        """Decrease master volume."""

        if step is None:
            step = self.default_step

        if not 1 <= step <= 100:
            raise ValueError(
                "Volume step must be between 1 and 100."
            )

        current = self.get_volume()

        target = max(
            0,
            current - step,
        )

        return self.set_volume(target)

    def mute(self) -> None:
        """Mute the default playback device."""

        volume = self._get_volume_interface()

        volume.SetMute(
            1,
            None,
        )

    def unmute(self) -> None:
        """Unmute the default playback device."""

        volume = self._get_volume_interface()

        volume.SetMute(
            0,
            None,
        )

    def is_muted(self) -> bool:
        """Return whether the default playback device is muted."""

        volume = self._get_volume_interface()

        return bool(volume.GetMute())