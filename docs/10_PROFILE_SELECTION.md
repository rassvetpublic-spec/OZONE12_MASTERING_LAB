# 10. Profile Selection

Universal Core не имеет единственного жанрового default. Профиль выбирается по аудио и творческой задаче.

| Профиль | Когда применять |
|---|---|
| `generic_streaming_safe` | жанр/приоритет неясен |
| `drum_forward_commercial` | groove и живые ударные должны тащить мастер |
| `wide_wow_streaming_safe` | нужен headphone wow при обязательной mono stability |
| `codec_safe_dark` | верх/кодек опасны, но нельзя автоматически затемнять vocal |
| `open_modern_pop` | нужен air/clarity/controlled width |
| `aggressive_loud_probe` | только loudness boundary probe |
| `dark_gothic_streaming_safe` | стиль явно dark/gothic/industrial |

Профиль задаёт направление и проверки, а не фиксированные track settings. Любой профиль уступает current winner, слуху пользователя и hard reject checks.
