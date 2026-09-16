from __future__ import annotations

import asyncio
import os
import threading
from enum import Enum

from pynput import keyboard

from core.event_bus import EventBus

# Speech
from speech.mic_stream import MicrophoneStream
from speech.wake_word import WakeWordDetector
from speech.voice import VoiceEngine
from speech.stt import FasterWhisperEngine
from speech.tts import WindowsTTSEngine

# Execution
from execution.router import CommandRouter
from execution.confirmation import ConfirmationManager
from execution.application_intent import ApplicationIntentResolver
from tools.registry import ToolRegistry
from execution.system_router import SystemCommandRouter
from execution.normalizer import CommandNormalizer

# Application System
from tools.system.application_registry import ApplicationRegistry
from tools.system.applications import OpenApplicationTool
from tools.system.volume import VolumeControlTool


os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


# =============================================================
# ASSISTANT STATE
# =============================================================


class AssistantState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    EXECUTING = "executing"
    WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"
    SPEAKING = "speaking"
    SHUTTING_DOWN = "shutting_down"


# =============================================================
# ASSISTANT CONTROLLER
# =============================================================


class AssistantController:
    """
    Controls the lifecycle of Vox OS.

    State rules:

        IDLE
            ↓
        LISTENING
            ↓
        PROCESSING
            ↓
        EXECUTING
            ↓
        SPEAKING
            ↓
        IDLE

    For actions requiring confirmation:

        EXECUTING
            ↓
        SPEAKING
            ↓
        WAITING_FOR_CONFIRMATION
            ↓
        LISTENING
            ↓
        PROCESSING
            ↓
        EXECUTING
            ↓
        SPEAKING
            ↓
        IDLE
    """

    def __init__(self) -> None:
        self.state = AssistantState.IDLE
        self._lock = threading.Lock()

    def get_state(self) -> AssistantState:
        with self._lock:
            return self.state

    def set_state(self, state: AssistantState) -> None:
        with self._lock:
            previous = self.state
            self.state = state

        print(
            f"[State] {previous.value.upper()} "
            f"-> {state.value.upper()}"
        )

    def can_wake(self) -> bool:
        """
        Normal wake is allowed only while IDLE.

        Confirmation responses are handled separately.
        """

        with self._lock:
            return self.state == AssistantState.IDLE

    def can_accept_confirmation(self) -> bool:
        """
        Return True when the assistant is waiting for a
        confirmation response.
        """

        with self._lock:
            return (
                self.state
                == AssistantState.WAITING_FOR_CONFIRMATION
            )

    def begin_interaction(self) -> bool:
        """
        Begin a normal assistant interaction.
        """

        with self._lock:
            if self.state != AssistantState.IDLE:
                return False

            self.state = AssistantState.LISTENING

        print("[State] IDLE -> LISTENING")

        return True

    def begin_confirmation_interaction(self) -> bool:
        """
        Begin capturing a confirmation response.
        """

        with self._lock:
            if (
                self.state
                != AssistantState.WAITING_FOR_CONFIRMATION
            ):
                return False

            self.state = AssistantState.LISTENING

        print(
            "[State] WAITING_FOR_CONFIRMATION "
            "-> LISTENING"
        )

        return True

    def shutdown(self) -> None:
        self.set_state(
            AssistantState.SHUTTING_DOWN
        )


# =============================================================
# GLOBAL HOTKEY
# =============================================================


def setup_global_hotkey(
    event_bus: EventBus,
    loop: asyncio.AbstractEventLoop,
    controller: AssistantController,
):
    """
    Register F9 as a manual wake trigger.

    F9 can start:

    1. A normal interaction while IDLE.
    2. A confirmation response while
       WAITING_FOR_CONFIRMATION.
    """

    def on_press(key):
        if key != keyboard.Key.f9:
            return

        state = controller.get_state()

        # -----------------------------------------------------
        # Normal interaction
        # -----------------------------------------------------

        if state == AssistantState.IDLE:
            print(
                "\n[Hotkey] F9 Pressed! "
                "Waking Vox OS manually..."
            )

            asyncio.run_coroutine_threadsafe(
                event_bus.publish(
                    "wake_word_detected",
                    {
                        "wakeword": "keyboard_trigger",
                    },
                ),
                loop,
            )

            return

        # -----------------------------------------------------
        # Confirmation response
        # -----------------------------------------------------

        if state == AssistantState.WAITING_FOR_CONFIRMATION:
            print(
                "\n[Hotkey] F9 Pressed! "
                "Listening for confirmation..."
            )

            asyncio.run_coroutine_threadsafe(
                event_bus.publish(
                    "confirmation_wake",
                    {
                        "wakeword": "keyboard_trigger",
                    },
                ),
                loop,
            )

            return

        # -----------------------------------------------------
        # Busy
        # -----------------------------------------------------

        print(
            "[Hotkey] Ignored because assistant is "
            f"{state.value}."
        )

    listener = keyboard.Listener(
        on_press=on_press
    )

    listener.start()

    return listener


# =============================================================
# MAIN
# =============================================================


async def main():
    print("Initializing Vox OS...")

    bus = EventBus()

    controller = AssistantController()

    loop = asyncio.get_running_loop()

    # =========================================================
    # SPEECH SYSTEM
    # =========================================================

    mic = MicrophoneStream()

    wake_word_engine = WakeWordDetector(
        bus,
        loop,
    )

    voice_engine = VoiceEngine()

    stt_engine = FasterWhisperEngine()

    tts_engine = WindowsTTSEngine()

    print(
        "[TTS] Windows TTS engine initialized."
    )

    # =========================================================
    # APPLICATION DISCOVERY
    # =========================================================

    print(
        "[Applications] "
        "Discovering installed applications..."
    )

    application_registry = ApplicationRegistry()

    application_count = (
        application_registry.discover()
    )

    print(
        "[Applications] Discovered: "
        f"{application_count} applications."
    )

    # =========================================================
    # TOOL REGISTRY
    # =========================================================

    tool_registry = ToolRegistry()
    open_application_tool = OpenApplicationTool(
        application_registry
    )

    volume_control_tool = VolumeControlTool()

    tool_registry.register(
        open_application_tool
    )

    tool_registry.register(
        volume_control_tool
    )

    command_normalizer = CommandNormalizer()

    command_router_resolver = ApplicationIntentResolver(
        application_registry
    )

    # =========================================================
    # COMMAND ROUTER
    # =========================================================

    command_router = CommandRouter(
        registry=tool_registry,
        application_resolver=command_router_resolver,
    )

    # =========================================================
    # SYSTEM COMMAND ROUTER
    # =========================================================

    system_router = SystemCommandRouter(
        tool_registry
    )

    print(
        "[System Router] Deterministic system command router initialized."
    )

    # =========================================================
    # CONFIRMATION MANAGER
    # =========================================================

    confirmation_manager = ConfirmationManager(
        tool_registry
    )

    print(
        "[Confirmation] Confirmation manager initialized."
    )

    # =========================================================
    # GLOBAL HOTKEY
    # =========================================================

    hotkey_listener = setup_global_hotkey(
        bus,
        loop,
        controller,
    )

    # =========================================================
    # HELPER: RESUME WAKE WORD MODE
    # =========================================================

    def resume_wake_mode() -> None:
        """
        Resume the always-on wake-word microphone.

        This function is intentionally synchronous because
        it is called from the asyncio event loop after the
        voice/TTS operations have completed.
        """

        if (
            controller.get_state()
            == AssistantState.SHUTTING_DOWN
        ):
            return

        wake_word_engine.resume_listening()

        mic.start(
            callback=(
                wake_word_engine.process_audio_chunk
            )
        )

        print(
            "[System] Wake-word mode resumed."
        )

    # =========================================================
    # WAKE WORD
    # =========================================================

    async def handle_wake_word(payload):
        """
        Start a normal voice interaction.
        """

        if not controller.begin_interaction():
            print(
                "[Wake] Ignored because assistant is "
                f"{controller.get_state().value}."
            )
            return

        print(
            "[Wake] Triggered by: "
            f"{payload.get('wakeword', 'unknown')}"
        )

        # -----------------------------------------------------
        # Stop always-on wake-word microphone.
        # -----------------------------------------------------

        mic.stop()

        # -----------------------------------------------------
        # Capture + STT in background thread.
        # -----------------------------------------------------

        def capture_and_transcribe():
            try:
                # -------------------------------------------------
                # Capture
                # -------------------------------------------------

                voice_engine.start()

                print(
                    "[Voice] Listening for command..."
                )

                command = voice_engine.listen()

                if not command:
                    print(
                        "[Voice] No command captured."
                    )

                    asyncio.run_coroutine_threadsafe(
                        bus.publish(
                            "interaction_failed",
                            {},
                        ),
                        loop,
                    )

                    return

                # -------------------------------------------------
                # Processing
                # -------------------------------------------------

                controller.set_state(
                    AssistantState.PROCESSING
                )

                print(
                    "[STT] Transcribing..."
                )

                text = stt_engine.transcribe(
                    command
                )

                if not text:
                    print(
                        "[STT] No speech recognized."
                    )

                    asyncio.run_coroutine_threadsafe(
                        bus.publish(
                            "interaction_failed",
                            {},
                        ),
                        loop,
                    )

                    return

                print(
                    f"[STT] Recognized: {text}"
                )

                # -------------------------------------------------
                # Send command to execution pipeline.
                # -------------------------------------------------

                asyncio.run_coroutine_threadsafe(
                    bus.publish(
                        "command_recognized",
                        {
                            "text": text,
                        },
                    ),
                    loop,
                )

            except Exception as exc:
                print(
                    "[System Error] "
                    "Audio capture/transcription "
                    f"failed: {exc}"
                )

                asyncio.run_coroutine_threadsafe(
                    bus.publish(
                        "interaction_failed",
                        {},
                    ),
                    loop,
                )

            finally:
                voice_engine.stop()

        threading.Thread(
            target=capture_and_transcribe,
            daemon=True,
            name="voice-capture",
        ).start()

    bus.subscribe(
        "wake_word_detected",
        handle_wake_word,
    )

    # =============================================================
    # CONFIRMATION WAKE
    # =============================================================

    async def handle_confirmation_wake(payload):
        """
        Start recording a response to a pending confirmation.
        """

        if not controller.begin_confirmation_interaction():
            print(
                "[Confirmation Wake] Ignored because assistant "
                "is not waiting for confirmation."
            )

            return

        print(
            "[Confirmation Wake] Triggered by: "
            f"{payload.get('wakeword', 'unknown')}"
        )

        # ---------------------------------------------------------
        # Stop any wake-word microphone.
        # ---------------------------------------------------------

        mic.stop()

        # ---------------------------------------------------------
        # Capture confirmation response.
        # ---------------------------------------------------------

        def capture_confirmation():
            try:
                voice_engine.start()

                print(
                    "[Voice] Listening for confirmation..."
                )

                command = voice_engine.listen()

                if not command:
                    print(
                        "[Confirmation] "
                        "No response captured."
                    )

                    asyncio.run_coroutine_threadsafe(
                        bus.publish(
                            "interaction_failed",
                            {},
                        ),
                        loop,
                    )

                    return

                # -------------------------------------------------
                # Processing
                # -------------------------------------------------

                controller.set_state(
                    AssistantState.PROCESSING
                )

                print(
                    "[STT] Transcribing confirmation..."
                )

                text = stt_engine.transcribe(
                    command
                )

                if not text:
                    print(
                        "[STT] "
                        "No confirmation recognized."
                    )

                    asyncio.run_coroutine_threadsafe(
                        bus.publish(
                            "interaction_failed",
                            {},
                        ),
                        loop,
                    )

                    return

                print(
                    "[STT] Confirmation recognized: "
                    f"{text}"
                )

                asyncio.run_coroutine_threadsafe(
                    bus.publish(
                        "confirmation_response",
                        {
                            "text": text,
                        },
                    ),
                    loop,
                )

            except Exception as exc:
                print(
                    "[System Error] "
                    "Confirmation capture/transcription "
                    f"failed: {exc}"
                )

                asyncio.run_coroutine_threadsafe(
                    bus.publish(
                        "interaction_failed",
                        {},
                    ),
                    loop,
                )

            finally:
                voice_engine.stop()

        threading.Thread(
            target=capture_confirmation,
            daemon=True,
            name="confirmation-capture",
        ).start()

    bus.subscribe(
        "confirmation_wake",
        handle_confirmation_wake,
    )

    # =========================================================
    # SPEAK RESPONSE
    # =========================================================

    async def speak_response(
        response: str,
        return_to_idle: bool = True,
    ) -> None:
        """
        Speak a response using TTS.

        When return_to_idle=True:
            SPEAKING → IDLE → wake-word mode

        When False:
            SPEAKING → WAITING_FOR_CONFIRMATION
        """

        controller.set_state(
            AssistantState.SPEAKING
        )

        print(
            f"[TTS] Speaking: {response}"
        )

        try:
            await asyncio.to_thread(
                tts_engine.speak,
                response,
            )

        except Exception as exc:
            print(
                "[TTS Error] "
                f"Failed to speak response: {exc}"
            )

        # -----------------------------------------------------
        # Confirmation is waiting.
        # -----------------------------------------------------

        if not return_to_idle:
            if (
                controller.get_state()
                != AssistantState.SHUTTING_DOWN
            ):
                controller.set_state(
                    AssistantState.WAITING_FOR_CONFIRMATION
                )

                print(
                    "[Confirmation] "
                    "Waiting for user confirmation..."
                )

            return

        # -----------------------------------------------------
        # Normal completion.
        # -----------------------------------------------------

        if (
            controller.get_state()
            != AssistantState.SHUTTING_DOWN
        ):
            controller.set_state(
                AssistantState.IDLE
            )

            print(
                "[System] Returning to "
                "wake-word mode..."
            )

            resume_wake_mode()

    # =========================================================
    # COMMAND EXECUTION
    # =========================================================

    async def handle_command_recognized(payload):
        """
        Handle normal commands.

        If a confirmation is pending, this event is treated
        as the confirmation response instead.
        """

        text = payload.get(
            "text",
            "",
        ).strip()

        if not text:
            return

        print(
            f"[Command] {text}"
        )

        # -----------------------------------------------------
        # SECURITY BOUNDARY
        #
        # If a confirmation is pending, NEVER send the text
        # back through the normal command router.
        #
        # It must go exclusively through ConfirmationManager.
        # -----------------------------------------------------

        if confirmation_manager.has_pending:
            await handle_confirmation_response(
                text
            )
            return

        # -----------------------------------------------------
        # Normal command execution
        # -----------------------------------------------------

        controller.set_state(
            AssistantState.EXECUTING
        )

        try:
            # -------------------------------------------------
            # Deterministic system commands first.
            # Simple commands such as volume control bypass
            # the slower application/LLM path.
            # -------------------------------------------------

            normalized_text = command_normalizer.normalize(text)

            print(
                f"[Router] Normalized: {normalized_text}"
            )

            result = await asyncio.to_thread(
                system_router.route,
                normalized_text,
            )

            # -------------------------------------------------
            # Fall back to the existing command router when the
            # system router does not recognize the command.
            # -------------------------------------------------

            if result is None:
                result = await asyncio.to_thread(
                    command_router.route,
                    normalized_text,
                )

        except Exception as exc:
            print(
                "[Execution Error] "
                "Command execution failed: "
                f"{exc}"
            )

            response = (
                "Something went wrong while "
                "executing that command."
            )

            await speak_response(
                response
            )

            return

        # -----------------------------------------------------
        # Execution result
        # -----------------------------------------------------

        if result.success:
            print(
                "[Execution] Success: "
                f"{result.message}"
            )

            await speak_response(
                result.message
            )

            return

        print(
            "[Execution] Failed: "
            f"{result.message}"
        )

        # -----------------------------------------------------
        # CONFIRMATION REQUIRED
        # -----------------------------------------------------

        if (
            result.data
            and result.data.get("type")
            == "confirmation_required"
        ):
            action = result.data.get(
                "action"
            )

            arguments = result.data.get(
                "arguments",
                {},
            )

            # -------------------------------------------------
            # Validate confirmation payload.
            # -------------------------------------------------

            if not action:
                print(
                    "[Confirmation Error] "
                    "Missing action."
                )

                await speak_response(
                    "I couldn't safely prepare that confirmation."
                )

                return

            if not isinstance(
                arguments,
                dict,
            ):
                print(
                    "[Confirmation Error] "
                    "Invalid arguments."
                )

                await speak_response(
                    "I couldn't safely prepare that confirmation."
                )

                return

            # -------------------------------------------------
            # Store pending action.
            # -------------------------------------------------

            confirmation_result = (
                confirmation_manager.request(
                    action=action,
                    arguments=arguments,
                    prompt=result.message,
                )
            )

            # -------------------------------------------------
            # Speak confirmation request.
            #
            # Do NOT return to wake-word mode afterward.
            # -------------------------------------------------

            await speak_response(
                confirmation_result.message,
                return_to_idle=False,
            )

            return

        # -----------------------------------------------------
        # Normal failure.
        # -----------------------------------------------------

        await speak_response(
            result.message
        )

    bus.subscribe(
        "command_recognized",
        handle_command_recognized,
    )

    # =========================================================
    # CONFIRMATION RESPONSE
    # =========================================================

    async def handle_confirmation_response(
        text: str,
    ) -> None:
        """
        Process a response to the currently pending action.
        """

        if not confirmation_manager.has_pending:
            print(
                "[Confirmation] "
                "No pending confirmation."
            )

            await speak_response(
                "There is nothing waiting for confirmation."
            )

            return

        print(
            "[Confirmation] Response: "
            f"{text}"
        )

        controller.set_state(
            AssistantState.EXECUTING
        )

        try:
            result = await asyncio.to_thread(
                confirmation_manager.handle_response,
                text,
            )

        except Exception as exc:
            print(
                "[Confirmation Error] "
                f"Failed to process confirmation: {exc}"
            )

            await speak_response(
                "Something went wrong while processing "
                "the confirmation."
            )

            return

        # -----------------------------------------------------
        # Result
        # -----------------------------------------------------

        if result.success:
            print(
                "[Confirmation] Approved and executed: "
                f"{result.message}"
            )

        else:
            print(
                "[Confirmation] "
                f"{result.message}"
            )

        # -----------------------------------------------------
        # Speak result and return to normal mode.
        # -----------------------------------------------------

        await speak_response(
            result.message
        )

    bus.subscribe(
        "confirmation_response",
        lambda payload: handle_confirmation_response(
            payload.get("text", "").strip()
        ),
    )

    # =========================================================
    # FAILED INTERACTION
    # =========================================================

    async def handle_interaction_failed(payload):
        """
        Recover safely when voice capture or STT fails.

        If confirmation was pending, it remains pending so the
        user can try again rather than accidentally cancelling
        the requested action.
        """

        if (
            controller.get_state()
            == AssistantState.SHUTTING_DOWN
        ):
            return

        # -----------------------------------------------------
        # If confirmation is still pending, return to the
        # waiting state instead of clearing it.
        # -----------------------------------------------------

        if confirmation_manager.has_pending:
            controller.set_state(
                AssistantState.WAITING_FOR_CONFIRMATION
            )

            print(
                "[System] Confirmation response failed."
            )

            print(
                "[System] Still waiting for confirmation..."
            )

            return

        # -----------------------------------------------------
        # Normal interaction failure.
        # -----------------------------------------------------

        controller.set_state(
            AssistantState.IDLE
        )

        print(
            "[System] Interaction failed. "
            "Returning to wake-word mode..."
        )

        resume_wake_mode()

    bus.subscribe(
        "interaction_failed",
        handle_interaction_failed,
    )

    # =========================================================
    # START
    # =========================================================

    print(
        "[System] Starting wake-word listener..."
    )

    mic.start(
        callback=(
            wake_word_engine.process_audio_chunk
        )
    )

    # =========================================================
    # MAIN LOOP
    # =========================================================

    try:
        while True:
            await asyncio.sleep(1)

    except asyncio.CancelledError:
        pass

    except KeyboardInterrupt:
        print(
            "\n[System] Shutdown requested..."
        )

    finally:
        controller.shutdown()

        print(
            "[System] Cleaning up..."
        )

        try:
            mic.stop()

        except Exception as exc:
            print(
                f"[Cleanup] Microphone: {exc}"
            )

        try:
            voice_engine.stop()

        except Exception as exc:
            print(
                f"[Cleanup] Voice engine: {exc}"
            )

        try:
            tts_engine.stop()

        except Exception as exc:
            print(
                f"[Cleanup] TTS: {exc}"
            )

        try:
            hotkey_listener.stop()

        except Exception as exc:
            print(
                f"[Cleanup] Hotkey: {exc}"
            )

        print(
            "[System] Vox OS stopped."
        )


# =============================================================
# ENTRY POINT
# =============================================================


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass