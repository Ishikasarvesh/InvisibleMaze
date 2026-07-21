import math
import random

import pygame

from game.settings import (
    BATTERY_GLOW,
    EXIT_COLOR,
    GREEN_LIGHT,
    PARTICLE_COUNT,
    PLAYER_COLOR,
    YELLOW,
)


class Particle:
    """
    Represents one animated particle.
    """

    def __init__(
        self,
        x,
        y,
        velocity_x,
        velocity_y,
        lifetime,
        radius,
        color,
        gravity=0,
        fade=True,
    ):
        self.x = float(x)
        self.y = float(y)

        self.velocity_x = float(
            velocity_x
        )

        self.velocity_y = float(
            velocity_y
        )

        self.lifetime = lifetime
        self.maximum_lifetime = lifetime

        self.radius = radius
        self.color = color

        self.gravity = gravity
        self.fade = fade

        self.alive = True

    def update(self, delta_time):
        """
        Updates particle position and lifetime.
        """

        if not self.alive:
            return

        self.lifetime -= delta_time

        if self.lifetime <= 0:
            self.alive = False
            return

        self.velocity_y += (
            self.gravity * delta_time
        )

        self.x += (
            self.velocity_x * delta_time
        )

        self.y += (
            self.velocity_y * delta_time
        )

    def draw(self, surface):
        """
        Draws the particle using transparency.
        """

        if not self.alive:
            return

        if self.fade:
            life_ratio = (
                self.lifetime
                / self.maximum_lifetime
            )
        else:
            life_ratio = 1

        current_radius = max(
            1,
            int(self.radius * life_ratio),
        )

        alpha = int(
            255 * life_ratio
        )

        particle_surface = pygame.Surface(
            (
                current_radius * 4,
                current_radius * 4,
            ),
            pygame.SRCALPHA,
        )

        pygame.draw.circle(
            particle_surface,
            (
                self.color[0],
                self.color[1],
                self.color[2],
                alpha,
            ),
            (
                current_radius * 2,
                current_radius * 2,
            ),
            current_radius,
        )

        surface.blit(
            particle_surface,
            (
                int(self.x)
                - current_radius * 2,
                int(self.y)
                - current_radius * 2,
            ),
        )


class Firefly:
    """
    Decorative floating firefly used in menus
    and dark backgrounds.
    """

    def __init__(
        self,
        screen_width,
        screen_height,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.reset(
            random_position=True
        )

    def reset(
        self,
        random_position=False,
    ):
        if random_position:
            self.x = random.uniform(
                0,
                self.screen_width,
            )

            self.y = random.uniform(
                0,
                self.screen_height,
            )
        else:
            self.x = random.choice(
                [
                    -20,
                    self.screen_width + 20,
                ]
            )

            self.y = random.uniform(
                0,
                self.screen_height,
            )

        self.speed = random.uniform(
            8,
            24,
        )

        self.direction = random.uniform(
            0,
            math.tau,
        )

        self.radius = random.randint(
            1,
            3,
        )

        self.phase = random.uniform(
            0,
            math.tau,
        )

        self.time = 0

    def update(self, delta_time):
        self.time += delta_time

        self.direction += (
            math.sin(self.time + self.phase)
            * 0.01
        )

        self.x += (
            math.cos(self.direction)
            * self.speed
            * delta_time
        )

        self.y += (
            math.sin(self.direction)
            * self.speed
            * delta_time
        )

        outside_screen = (
            self.x < -50
            or self.x > self.screen_width + 50
            or self.y < -50
            or self.y > self.screen_height + 50
        )

        if outside_screen:
            self.reset()

    def draw(self, surface):
        glow_alpha = int(
            70
            + (
                math.sin(
                    self.time * 3
                    + self.phase
                )
                + 1
            ) * 45
        )

        glow_radius = self.radius * 5

        glow_surface = pygame.Surface(
            surface.get_size(),
            pygame.SRCALPHA,
        )

        pygame.draw.circle(
            glow_surface,
            (
                YELLOW[0],
                YELLOW[1],
                YELLOW[2],
                glow_alpha // 3,
            ),
            (
                int(self.x),
                int(self.y),
            ),
            glow_radius,
        )

        pygame.draw.circle(
            glow_surface,
            (
                YELLOW[0],
                YELLOW[1],
                YELLOW[2],
                glow_alpha,
            ),
            (
                int(self.x),
                int(self.y),
            ),
            self.radius,
        )

        surface.blit(
            glow_surface,
            (0, 0),
        )


class ParticleManager:
    """
    Controls all temporary and decorative particles.
    """

    def __init__(
        self,
        screen_width,
        screen_height,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.particles = []

        self.fireflies = [
            Firefly(
                screen_width,
                screen_height,
            )
            for _ in range(PARTICLE_COUNT)
        ]

        self.trail_timer = 0

    # =====================================================
    # UPDATE AND DRAW
    # =====================================================

    def update(
        self,
        delta_time,
        update_fireflies=True,
    ):
        if update_fireflies:
            for firefly in self.fireflies:
                firefly.update(delta_time)

        for particle in self.particles:
            particle.update(delta_time)

        self.particles = [
            particle
            for particle in self.particles
            if particle.alive
        ]

        self.trail_timer = max(
            0,
            self.trail_timer - delta_time,
        )

    def draw_fireflies(self, surface):
        for firefly in self.fireflies:
            firefly.draw(surface)

    def draw_particles(self, surface):
        for particle in self.particles:
            particle.draw(surface)

    # =====================================================
    # BATTERY COLLECTION PARTICLES
    # =====================================================

    def create_battery_burst(
        self,
        x,
        y,
        amount=18,
    ):
        """
        Creates a glowing burst when collecting a battery.
        """

        for _ in range(amount):
            angle = random.uniform(
                0,
                math.tau,
            )

            speed = random.uniform(
                45,
                130,
            )

            velocity_x = (
                math.cos(angle) * speed
            )

            velocity_y = (
                math.sin(angle) * speed
            )

            particle = Particle(
                x=x,
                y=y,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                lifetime=random.uniform(
                    0.35,
                    0.8,
                ),
                radius=random.uniform(
                    2,
                    5,
                ),
                color=random.choice(
                    [
                        BATTERY_GLOW,
                        YELLOW,
                        (255, 245, 170),
                    ]
                ),
                gravity=45,
            )

            self.particles.append(
                particle
            )

    # =====================================================
    # PLAYER TRAIL
    # =====================================================

    def create_player_trail(
        self,
        x,
        y,
    ):
        """
        Creates a soft glowing trail behind the player.
        """

        if self.trail_timer > 0:
            return

        self.trail_timer = 0.035

        particle = Particle(
            x=x + random.uniform(-3, 3),
            y=y + random.uniform(-3, 3),
            velocity_x=random.uniform(
                -6,
                6,
            ),
            velocity_y=random.uniform(
                -6,
                6,
            ),
            lifetime=random.uniform(
                0.2,
                0.45,
            ),
            radius=random.uniform(
                2,
                4,
            ),
            color=PLAYER_COLOR,
            gravity=0,
        )

        self.particles.append(
            particle
        )

    # =====================================================
    # EXIT PORTAL PARTICLES
    # =====================================================

    def create_exit_particle(
        self,
        x,
        y,
        radius,
    ):
        """
        Creates one particle moving around the exit portal.
        """

        angle = random.uniform(
            0,
            math.tau,
        )

        particle_x = (
            x + math.cos(angle) * radius
        )

        particle_y = (
            y + math.sin(angle) * radius
        )

        speed = random.uniform(
            15,
            35,
        )

        velocity_x = (
            -math.cos(angle) * speed
        )

        velocity_y = (
            -math.sin(angle) * speed
        )

        particle = Particle(
            x=particle_x,
            y=particle_y,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            lifetime=random.uniform(
                0.5,
                1.1,
            ),
            radius=random.uniform(
                1.5,
                3.5,
            ),
            color=random.choice(
                [
                    EXIT_COLOR,
                    GREEN_LIGHT,
                    (200, 255, 230),
                ]
            ),
            gravity=0,
        )

        self.particles.append(
            particle
        )

    # =====================================================
    # WALL HIT PARTICLES
    # =====================================================

    def create_wall_hit_sparks(
        self,
        x,
        y,
        direction,
    ):
        """
        Creates small sparks when the player hits a wall.
        """

        row_direction, col_direction = (
            direction
        )

        base_x = -col_direction
        base_y = -row_direction

        for _ in range(7):
            spread_x = random.uniform(
                -0.8,
                0.8,
            )

            spread_y = random.uniform(
                -0.8,
                0.8,
            )

            velocity_x = (
                base_x * random.uniform(30, 75)
                + spread_x * 35
            )

            velocity_y = (
                base_y * random.uniform(30, 75)
                + spread_y * 35
            )

            particle = Particle(
                x=x,
                y=y,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                lifetime=random.uniform(
                    0.15,
                    0.35,
                ),
                radius=random.uniform(
                    1,
                    2.5,
                ),
                color=random.choice(
                    [
                        (180, 190, 215),
                        (120, 135, 170),
                        (230, 230, 240),
                    ]
                ),
                gravity=80,
            )

            self.particles.append(
                particle
            )

    # =====================================================
    # WIN CELEBRATION
    # =====================================================

    def create_win_burst(
        self,
        x,
        y,
        amount=45,
    ):
        """
        Creates a large celebration burst.
        """

        colors = [
            EXIT_COLOR,
            GREEN_LIGHT,
            YELLOW,
            PLAYER_COLOR,
            (255, 255, 255),
        ]

        for _ in range(amount):
            angle = random.uniform(
                0,
                math.tau,
            )

            speed = random.uniform(
                70,
                220,
            )

            particle = Particle(
                x=x,
                y=y,
                velocity_x=(
                    math.cos(angle) * speed
                ),
                velocity_y=(
                    math.sin(angle) * speed
                ),
                lifetime=random.uniform(
                    0.7,
                    1.5,
                ),
                radius=random.uniform(
                    2,
                    6,
                ),
                color=random.choice(
                    colors
                ),
                gravity=80,
            )

            self.particles.append(
                particle
            )

    def clear(self):
        """
        Removes all temporary particles.
        """

        self.particles.clear()

    def create_sparkle(
        self,
        x,
        y,
    ):
        """
        Creates a small golden sparkle floating upwards.
        """
        particle = Particle(
            x=x + random.uniform(-12, 12),
            y=y + random.uniform(-12, 12),
            velocity_x=random.uniform(-15, 15),
            velocity_y=random.uniform(-30, -10),
            lifetime=random.uniform(0.4, 0.8),
            radius=random.uniform(1.2, 2.8),
            color=random.choice([
                (255, 215, 0), # Gold
                (255, 223, 0), # Golden yellow
                (255, 245, 180), # Soft light gold
            ]),
            gravity=-12,
        )
        self.particles.append(particle)

    def create_powerup_burst(
        self,
        x,
        y,
        amount=30,
    ):
        """
        Creates a star-explosion gold burst of particles.
        """
        colors = [
            (255, 215, 0), # Gold
            (255, 223, 0), # Golden yellow
            (255, 245, 180),
            (255, 255, 255), # White star sparkle
        ]
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(50, 180)
            particle = Particle(
                x=x,
                y=y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                lifetime=random.uniform(0.45, 1.1),
                radius=random.uniform(2, 5),
                color=random.choice(colors),
                gravity=40,
            )
            self.particles.append(particle)

    def create_red_sparks(
        self,
        x,
        y,
        amount=15,
    ):
        """
        Creates small red sparks when a Spike trap is triggered.
        """
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(30, 110)
            particle = Particle(
                x=x,
                y=y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                lifetime=random.uniform(0.3, 0.7),
                radius=random.uniform(1.5, 3.2),
                color=random.choice([
                    (230, 30, 40), # red
                    (180, 20, 30), # dark red
                    (255, 80, 80), # light red
                ]),
                gravity=45,
            )
            self.particles.append(particle)

    def create_smoke_ring(
        self,
        x,
        y,
        amount=12,
    ):
        """
        Creates expanding dark smoke particles for a Darkness trap.
        """
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(15, 45)
            particle = Particle(
                x=x,
                y=y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                lifetime=random.uniform(0.5, 1.0),
                radius=random.uniform(2.5, 5.0),
                color=random.choice([
                    (15, 15, 20), # black
                    (30, 30, 35), # dark grey
                ]),
                gravity=0,
            )
            self.particles.append(particle)

    def create_teleport_burst(
        self,
        x,
        y,
        amount=20,
    ):
        """
        Creates purple particles for teleport triggers.
        """
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(40, 140)
            particle = Particle(
                x=x,
                y=y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                lifetime=random.uniform(0.4, 0.9),
                radius=random.uniform(2.0, 4.5),
                color=random.choice([
                    (160, 32, 240), # purple
                    (110, 20, 160), # dark purple
                    (220, 160, 255), # light purple
                ]),
                gravity=20,
            )
            self.particles.append(particle)

    def create_battery_sparks(
        self,
        x,
        y,
        amount=12,
    ):
        """
        Creates small electrical yellow sparks.
        """
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(35, 120)
            particle = Particle(
                x=x,
                y=y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                lifetime=random.uniform(0.25, 0.6),
                radius=random.uniform(1.2, 2.5),
                color=random.choice([
                    (255, 221, 105), # electrical yellow
                    (255, 207, 70), # dark yellow
                    (255, 255, 255), # white spark
                ]),
                gravity=50,
            )
            self.particles.append(particle)

    def create_key_burst(self, x, y, color, amount=20):
        """
        Creates matching color sparkles when a key is picked up.
        """
        rgb = (255, 255, 255)
        if color == "Red": rgb = (245, 82, 95)
        elif color == "Blue": rgb = (89, 145, 255)
        elif color == "Green": rgb = (69, 230, 154)
        elif color == "Gold": rgb = (255, 215, 0)
        
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(40, 120)
            particle = Particle(
                x=x,
                y=y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                lifetime=random.uniform(0.35, 0.8),
                radius=random.uniform(1.5, 3.5),
                color=random.choice([rgb, (255, 255, 255)]),
                gravity=30,
            )
            self.particles.append(particle)

    def create_unlock_shards(self, x, y, color, amount=15):
        """
        Spawns glowing cracking shards and smoke when a door is unlocked.
        """
        rgb = (255, 255, 255)
        if color == "Red": rgb = (245, 82, 95)
        elif color == "Blue": rgb = (89, 145, 255)
        elif color == "Green": rgb = (69, 230, 154)
        elif color == "Gold": rgb = (255, 215, 0)
        
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(20, 90)
            particle = Particle(
                x=x + random.uniform(-10, 10),
                y=y + random.uniform(-10, 10),
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                lifetime=random.uniform(0.4, 0.9),
                radius=random.uniform(2.0, 4.0),
                color=random.choice([rgb, (30, 30, 35)]),
                gravity=15,
            )
            self.particles.append(particle)

    def create_exit_explosion(self, x, y, amount=45):
        """
        Spawns a large green/neon explosion when all doors are unlocked.
        """
        colors = [
            (71, 235, 171), # EXIT_COLOR
            (174, 255, 219), # GREEN_LIGHT
            (255, 255, 255)
        ]
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(60, 220)
            particle = Particle(
                x=x,
                y=y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                lifetime=random.uniform(0.6, 1.3),
                radius=random.uniform(2.5, 6.0),
                color=random.choice(colors),
                gravity=25,
            )
            self.particles.append(particle)