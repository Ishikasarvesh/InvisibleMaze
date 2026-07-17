import math


def clamp(value, minimum, maximum):
    """
    Keeps a value inside a specific range.
    """

    return max(minimum, min(value, maximum))


def lerp(start, end, amount):
    """
    Linearly moves one value toward another value.
    """

    amount = clamp(amount, 0, 1)

    return start + (end - start) * amount


def lerp_position(start_position, end_position, amount):
    """
    Smoothly moves an x-y position toward another position.
    """

    start_x, start_y = start_position
    end_x, end_y = end_position

    return (
        lerp(start_x, end_x, amount),
        lerp(start_y, end_y, amount),
    )


def ease_out_cubic(value):
    """
    Creates a smooth animation that slows near the end.
    """

    value = clamp(value, 0, 1)

    return 1 - pow(1 - value, 3)


def ease_in_out_cubic(value):
    """
    Creates an animation that accelerates and then slows.
    """

    value = clamp(value, 0, 1)

    if value < 0.5:
        return 4 * value * value * value

    return 1 - pow(-2 * value + 2, 3) / 2


def pulse(time_value, speed=1, minimum=0, maximum=1):
    """
    Repeatedly moves a value between a minimum and maximum.
    """

    sine_value = (
        math.sin(time_value * speed) + 1
    ) / 2

    return lerp(minimum, maximum, sine_value)


def floating_offset(
    time_value,
    speed=2,
    distance=5
):
    """
    Returns an up-and-down floating movement.
    """

    return math.sin(time_value * speed) * distance


def approach(
    current,
    target,
    speed,
    delta_time
):
    """
    Smoothly moves the current value toward a target.
    """

    difference = target - current

    movement = difference * speed * delta_time

    return current + movement


class AnimatedValue:
    """
    Stores a value that smoothly approaches a target value.
    """

    def __init__(self, initial_value=0):
        self.value = initial_value
        self.target = initial_value

    def set_target(self, target):
        self.target = target

    def update(self, delta_time, speed=8):
        self.value = approach(
            self.value,
            self.target,
            speed,
            delta_time
        )

    def snap(self, value):
        self.value = value
        self.target = value