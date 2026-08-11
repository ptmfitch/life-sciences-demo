from app.config import Settings


def test_default_demo_speed_is_one_hz():
    settings = Settings(_env_file=None)
    assert settings.demo_speed == 1.0
    assert settings.tick_interval_seconds == 1.0


def test_tick_interval_scales_with_demo_speed():
    settings = Settings(_env_file=None, demo_speed=12.0)
    assert abs(settings.tick_interval_seconds - (1.0 / 12.0)) < 1e-9
