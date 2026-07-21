import pygame

from game.animations import clamp
import game.settings
from game.settings import (
    BACKGROUND,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


class BaseTransition:
    """
    Base class for all screen transitions.
    Defines the unified interface and standard lifecycle methods.
    """

    def __init__(
        self,
        duration=0.5,
        color=None,
    ):
        self.duration = max(
            0.01,
            duration,
        )
        self.color = color if color is not None else getattr(game.settings, "BACKGROUND", BACKGROUND)

        self.active = False

        self.callback = None
        self.callback_called = False

    def start(
        self,
        callback=None,
        *args,
        **kwargs,
    ):
        """
        Starts the transition.
        """
        if self.active:
            return

        self.active = True
        self.callback = callback
        self.callback_called = False

    def update(self, delta_time):
        """
        Updates the transition progress over time.
        """
        pass

    def draw(self, surface):
        """
        Renders the transition overlay onto the target surface.
        """
        pass

    def reset(self):
        """
        Resets the transition to its initial state.
        """
        self.active = False
        self.callback = None
        self.callback_called = False

    def is_active(self):
        """
        Returns True while the transition is active.
        """
        return self.active


class FadeTransition(BaseTransition):
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
        color=None,
    ):
        super().__init__(
            duration=duration,
            color=color,
        )

        self.alpha = 0
        self.direction = 1

    def start(
        self,
        callback=None,
        *args,
        **kwargs,
    ):
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

    def draw(self, surface):
        """
        Draws the fade overlay.
        """
        if not self.active:
            return

        effective_color = self.color if self.color is not None else getattr(game.settings, "BACKGROUND", BACKGROUND)

        overlay = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        overlay.fill(
            (
                effective_color[0],
                effective_color[1],
                effective_color[2],
                int(self.alpha),
            )
        )

        surface.blit(
            overlay,
            (0, 0),
        )

    def reset(self):
        """
        Resets the fade transition state.
        """
        super().reset()
        self.alpha = 0
        self.direction = 1

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


class CircleTransition(BaseTransition):
    """
    Creates a circular reveal or closing transition.

    This transition is optional. It can be used when
    entering a maze or returning to the menu.
    """

    def __init__(
        self,
        duration=0.6,
        color=None,
    ):
        super().__init__(
            duration=duration,
            color=color,
        )

        self.progress = 0
        self.direction = 1

        self.center = (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )

        self.maximum_radius = int(
            (
                SCREEN_WIDTH ** 2
                + SCREEN_HEIGHT ** 2
            ) ** 0.5
        )

    def start(
        self,
        callback=None,
        center=None,
        *args,
        **kwargs,
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

    def draw(self, surface):
        """
        Draws an overlay with a circular visible region.
        """
        if not self.active:
            return

        effective_color = self.color if self.color is not None else getattr(game.settings, "BACKGROUND", BACKGROUND)

        transition_surface = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        transition_surface.fill(
            (
                effective_color[0],
                effective_color[1],
                effective_color[2],
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

    def reset(self):
        """
        Resets the circle transition state.
        """
        super().reset()
        self.progress = 0
        self.direction = 1
        self.center = (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )

    def is_active(self):
        """
        Returns True while the transition is active.
        """
        return self.active


class ThemeTransition(BaseTransition):
    """
    Renders themed sweeps (ink wipes, green petals, frost, scanning glitch grids)
    across the screen based on the active world.
    """

    def __init__(
        self,
        duration=0.6,
        color=None,
    ):
        super().__init__(
            duration=duration,
            color=color,
        )

        self.progress = 0.0
        self.direction = 1
        self.theme_name = "Ninja World"

    def start(
        self,
        callback=None,
        theme_name="Ninja World",
        *args,
        **kwargs,
    ):
        """
        Starts the themed transition.
        """
        if self.active:
            return

        self.active = True
        self.direction = 1
        self.progress = 0.0

        self.callback = callback
        self.callback_called = False

        if theme_name:
            self.theme_name = theme_name

    def update(self, delta_time):
        """
        Updates the sweep progress.
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
            and self.progress >= 1.0
        ):
            self.progress = 1.0

            if (
                self.callback is not None
                and not self.callback_called
            ):
                self.callback()
                self.callback_called = True

            self.direction = -1

        elif (
            self.direction == -1
            and self.progress <= 0.0
        ):
            self.progress = 0.0

            self.active = False
            self.callback = None
            self.callback_called = False

        self.progress = clamp(
            self.progress,
            0.0,
            1.0,
        )

    def draw(self, surface):
        """
        Renders the theme sweep transition.
        """
        if not self.active:
            return

        import random

        width = int(SCREEN_WIDTH * self.progress)

        if self.theme_name == "Ninja World":
            pygame.draw.rect(surface, (15, 12, 18), (0, 0, width, SCREEN_HEIGHT))
            pygame.draw.rect(surface, (245, 82, 95), (max(0, width - 15), 0, 15, SCREEN_HEIGHT))
        elif self.theme_name == "Spring World":
            pygame.draw.rect(surface, (22, 45, 28), (0, 0, width, SCREEN_HEIGHT))
            pygame.draw.rect(surface, (255, 182, 193), (max(0, width - 15), 0, 15, SCREEN_HEIGHT))
        elif self.theme_name == "Frozen World":
            pygame.draw.rect(surface, (15, 26, 40), (0, 0, width, SCREEN_HEIGHT))
            pygame.draw.rect(surface, (140, 210, 255), (max(0, width - 15), 0, 15, SCREEN_HEIGHT))
        elif self.theme_name == "Haunted World":
            pygame.draw.rect(surface, (20, 15, 26), (0, 0, width, SCREEN_HEIGHT))
            pygame.draw.rect(surface, (160, 120, 210), (max(0, width - 15), 0, 15, SCREEN_HEIGHT))
        elif self.theme_name == "Cyber World":
            pygame.draw.rect(surface, (12, 10, 22), (0, 0, width, SCREEN_HEIGHT))
            pygame.draw.rect(surface, (0, 245, 255), (max(0, width - 15), 0, 15, SCREEN_HEIGHT))
            for _ in range(5):
                qy = random.randint(0, max(0, SCREEN_HEIGHT - 30))
                qw = random.randint(10, 40)
                pygame.draw.rect(surface, (50, 255, 120), (max(0, width - qw), qy, qw, qw))
        elif self.theme_name == "Desert Temple World":
            pygame.draw.rect(surface, (48, 35, 18), (0, 0, width, SCREEN_HEIGHT))
            pygame.draw.rect(surface, (255, 210, 100), (max(0, width - 15), 0, 15, SCREEN_HEIGHT))
        else:
            effective_color = self.color if self.color is not None else getattr(game.settings, "BACKGROUND", BACKGROUND)
            pygame.draw.rect(surface, effective_color, (0, 0, width, SCREEN_HEIGHT))

    def reset(self):
        """
        Resets the themed transition state.
        """
        super().reset()
        self.progress = 0.0
        self.direction = 1

    def is_active(self):
        """
        Returns True while the transition is active.
        """
        return self.active


class LoadingTransition(BaseTransition):
    """
    Transition with loading indicator/overlay for level loading operations.
    """

    def __init__(
        self,
        duration=0.6,
        color=None,
    ):
        super().__init__(
            duration=duration,
            color=color,
        )

        self.progress = 0.0
        self.direction = 1

    def start(
        self,
        callback=None,
        *args,
        **kwargs,
    ):
        """
        Starts the loading transition.
        """
        if self.active:
            return

        self.active = True
        self.direction = 1
        self.progress = 0.0

        self.callback = callback
        self.callback_called = False

    def update(self, delta_time):
        """
        Updates the loading transition.
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
            and self.progress >= 1.0
        ):
            self.progress = 1.0

            if (
                self.callback is not None
                and not self.callback_called
            ):
                self.callback()
                self.callback_called = True

            self.direction = -1

        elif (
            self.direction == -1
            and self.progress <= 0.0
        ):
            self.progress = 0.0

            self.active = False
            self.callback = None
            self.callback_called = False

        self.progress = clamp(
            self.progress,
            0.0,
            1.0,
        )

    def draw(self, surface):
        """
        Renders the loading transition overlay.
        """
        if not self.active:
            return

        effective_color = self.color if self.color is not None else getattr(game.settings, "BACKGROUND", BACKGROUND)

        overlay = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        alpha = int(255 * self.progress)
        overlay.fill(
            (
                effective_color[0],
                effective_color[1],
                effective_color[2],
                alpha,
            )
        )

        surface.blit(
            overlay,
            (0, 0),
        )

    def reset(self):
        """
        Resets the loading transition state.
        """
        super().reset()
        self.progress = 0.0
        self.direction = 1

    def is_active(self):
        """
        Returns True while the transition is active.
        """
        return self.active


class WorldTransition(BaseTransition):
    """
    Transition between different game worlds.
    """

    def __init__(
        self,
        duration=0.6,
        color=None,
    ):
        super().__init__(
            duration=duration,
            color=color,
        )

        self.progress = 0.0
        self.direction = 1

    def start(
        self,
        callback=None,
        *args,
        **kwargs,
    ):
        """
        Starts the world transition.
        """
        if self.active:
            return

        self.active = True
        self.direction = 1
        self.progress = 0.0

        self.callback = callback
        self.callback_called = False

    def update(self, delta_time):
        """
        Updates the world transition.
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
            and self.progress >= 1.0
        ):
            self.progress = 1.0

            if (
                self.callback is not None
                and not self.callback_called
            ):
                self.callback()
                self.callback_called = True

            self.direction = -1

        elif (
            self.direction == -1
            and self.progress <= 0.0
        ):
            self.progress = 0.0

            self.active = False
            self.callback = None
            self.callback_called = False

        self.progress = clamp(
            self.progress,
            0.0,
            1.0,
        )

    def draw(self, surface):
        """
        Renders the world transition overlay.
        """
        if not self.active:
            return

        effective_color = self.color if self.color is not None else getattr(game.settings, "BACKGROUND", BACKGROUND)

        overlay = pygame.Surface(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        alpha = int(255 * self.progress)
        overlay.fill(
            (
                effective_color[0],
                effective_color[1],
                effective_color[2],
                alpha,
            )
        )

        surface.blit(
            overlay,
            (0, 0),
        )

    def reset(self):
        """
        Resets the world transition state.
        """
        super().reset()
        self.progress = 0.0
        self.direction = 1

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
        self.theme_trans = ThemeTransition()
        self.loading = LoadingTransition()
        self.world_trans = WorldTransition()

        self.current_transition = None

    @property
    def active(self):
        """
        Convenience property returning True when any transition is active.
        """
        return self.is_active()

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

    def start_theme(
        self,
        callback=None,
        theme_name="Ninja World",
    ):
        """
        Starts the themed sweep transition.
        """
        if self.is_active():
            return

        self.current_transition = self.theme_trans
        self.theme_trans.start(
            callback=callback,
            theme_name=theme_name,
        )

    def start_loading(self, callback=None):
        """
        Starts the loading transition.
        """
        if self.is_active():
            return

        self.current_transition = self.loading
        self.loading.start(callback=callback)

    def start_world(self, callback=None):
        """
        Starts the world transition.
        """
        if self.is_active():
            return

        self.current_transition = self.world_trans
        self.world_trans.start(callback=callback)

    def start(
        self,
        transition_obj,
        callback=None,
        *args,
        **kwargs,
    ):
        """
        Starts any transition instance that implements the BaseTransition interface.
        """
        if self.is_active():
            return

        self.current_transition = transition_obj
        self.current_transition.start(
            callback=callback,
            *args,
            **kwargs,
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

    def reset(self):
        """
        Resets the current transition and clears active state.
        """
        if self.current_transition is not None:
            self.current_transition.reset()
            self.current_transition = None

    def is_active(self):
        """
        Returns True when any transition is running.
        """
        return (
            self.current_transition is not None
            and self.current_transition.is_active()
        )