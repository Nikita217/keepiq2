from utils.settings import Settings


def test_cors_allowed_origins_are_normalized() -> None:
    settings = Settings(
        MINI_APP_PUBLIC_URL="https://keepiq2.pages.dev/",
        MINI_APP_DEV_URL="http://localhost:5173/",
    )

    assert settings.cors_allowed_origins == [
        "http://localhost:5173",
        "https://keepiq2.pages.dev",
    ]
