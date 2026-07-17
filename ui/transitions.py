import pygame

from game.animations import clamp
from game.settings import (
    BACKGROUND,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


class FadeTransition:
    """
    Controls a fade-out and fade-in screen transition.

    Transition sequence:

    1. The screen fades to black.
    2. A callback changes the game state.
    3. The screen fades back to normal.
    """

    def __init__(
        self,
        duration=0.45,
        color=BACKGROUND,
    ):
        self.duration = max(
            0.01,
            duration,
        )

        self.color = color

        self.alpha = 0

        self.active = False
        self.direction = 1

        self.callback = None
        self.callback_called = False

    # =====================================================
    # START TRANSITION
    # =====================================================

    def start(self, callback=None):
        """
        Starts a complete fade-out and fade-in transition.

        The callback runs when the screen becomes fully dark.
        """

        if self.active:
            return

        self.active = True
        self.direction = 1

        self.alpha = 0

        self.callback = callback
        self.callback_called = False

    # =====================================================
    # UPDATE
    # =====================================================

    def update(self, delta_time):
        """
        Updates the transition opacity.
        """

        if not self.active:
            return

        change_amount = (
            255
            / self.duration
            * delta_time
        )

        self.alpha += (
            change_amount
            * self.direction
        )

        if (
            self.direction == 1
            and self.alpha >= 255
        ):
            self.alpha = 255

            if (
                self.callback is not None
                and not self.callback_called
            ):
                self.callback()
                self.callback_called = True

            self.direction = -1

        elif (
            self.direction == -1
            and self.alpha <= 0
        ):
            self.alpha = 0
            self.active = False
            self.callback = None
            self.callback_called = False

        self.alpha = clamp(
            self.alpha,
            0,
            255,
        )

    # =====================================================
    # DRAW
    # =====================================================

    def draw(self, surface):
        """
        Draws the fade overlay.
        """

        if not self.active:
            return

        overlay = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        overlay.fill(
            (
                self.color[0],
                self.color[1],
                self.color[2],
                int(self.alpha),
            )
        )

        surface.blit(
            overlay,
            (0, 0),
        )

    # =====================================================
    # INFORMATION
    # =====================================================

    def is_active(self):
        """
        Returns True while a transition is running.
        """

        return self.active

    def is_fully_covered(self):
        """
        Returns True when the screen is fully dark.
        """

        return self.alpha >= 255


class CircleTransition:
    """
    Creates a circular reveal or closing transition.

    This transition is optional. It can be used when
    entering a maze or returning to the menu.
    """

    def __init__(
        self,
        duration=0.6,
        color=BACKGROUND,
    ):
        self.duration = max(
            0.01,
            duration,
        )

        self.color = color

        self.active = False

        self.progress = 0
        self.direction = 1

        self.center = (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )

        self.callback = None
        self.callback_called = False

        self.maximum_radius = int(
            (
                SCREEN_WIDTH ** 2
                + SCREEN_HEIGHT ** 2
            ) ** 0.5
        )

    # =====================================================
    # START
    # =====================================================

    def start(
        self,
        callback=None,
        center=None,
    ):
        """
        Starts the circular transition.
        """

        if self.active:
            return

        self.active = True

        self.progress = 0
        self.direction = 1

        self.callback = callback
        self.callback_called = False

        if center is not None:
            self.center = center
        else:
            self.center = (
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
            )

    # =====================================================
    # UPDATE
    # =====================================================

    def update(self, delta_time):
        """
        Updates circular closing and opening.
        """

        if not self.active:
            return

        self.progress += (
            delta_time
            / self.duration
            * self.direction
        )

        if (
            self.direction == 1
            and self.progress >= 1
        ):
            self.progress = 1

            if (
                self.callback is not None
                and not self.callback_called
            ):
                self.callback()
                self.callback_called = True

            self.direction = -1

        elif (
            self.direction == -1
            and self.progress <= 0
        ):
            self.progress = 0

            self.active = False
            self.callback = None
            self.callback_called = False

        self.progress = clamp(
            self.progress,
            0,
            1,
        )

    # =====================================================
    # DRAW
    # =====================================================

    def draw(self, surface):
        """
        Draws an overlay with a circular visible region.
        """

        if not self.active:
            return

        transition_surface = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        transition_surface.fill(
            (
                self.color[0],
                self.color[1],
                self.color[2],
                255,
            )
        )

        visible_radius = int(
            self.maximum_radius
            * (
                1
                - self.progress
            )
        )

        pygame.draw.circle(
            transition_surface,
            (
                0,
                0,
                0,
                0,
            ),
            self.center,
            max(
                0,
                visible_radius,
            ),
        )

        surface.blit(
            transition_surface,
            (0, 0),
        )

    # =====================================================
    # INFORMATION
    # =====================================================

    def is_active(self):
        """
        Returns True while the transition is active.
        """

        return self.active


class TransitionManager:
    """
    Provides one shared transition controller
    for the complete game.
    """

    def __init__(self):
        self.fade = FadeTransition()
        self.circle = CircleTransition()

        self.current_transition = None

    def start_fade(self, callback=None):
        """
        Starts the standard fade transition.
        """

        if self.is_active():
            return

        self.current_transition = self.fade

        self.fade.start(callback)

    def start_circle(
        self,
        callback=None,
        center=None,
    ):
        """
        Starts the circular transition.
        """

        if self.is_active():
            return

        self.current_transition = self.circle

        self.circle.start(
            callback=callback,
            center=center,
        )

    def update(self, delta_time):
        """
        Updates the currently active transition.
        """

        if self.current_transition is None:
            return

        self.current_transition.update(
            delta_time
        )

        if not self.current_transition.is_active():
            self.current_transition = None

    def draw(self, surface):
        """
        Draws the currently active transition.
        """

        if self.current_transition is None:
            return

        self.current_transition.draw(surface)

    def is_active(self):
        """
        Returns True when any transition is running.
        """

        return (
            self.current_transition is not None
            and self.current_transition.is_active()
        )