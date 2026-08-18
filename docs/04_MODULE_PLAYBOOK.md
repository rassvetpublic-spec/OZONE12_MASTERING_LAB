# 04. Module Playbook

## Master Rebalance — optional pre-stage

Роль: ограниченная коррекция stem balance уже готового stereo mix. Использовать только когда проблема действительно относится к drums/bass/vocal/other balance. Не маскировать им тональную, фазовую или limiter-проблему. Amount и SourceType — `TRACK_DECISION`, не default.

## Equalizer

Роль: общий тон, низ, муть, presence, air. Не поднимать верх механически: в AI/SUNO/codec material часто уже есть glass. В drum-forward T/S сохранять kick/snare attack, а долгий low-mid/upper buildup корректировать прежде всего в Sustain.

## Impact

Роль: punch и micro/macro dynamics. Если safe candidate почти не слышен, допустим один extreme boundary probe; winner выбирается после retreat. Риск: click, pumping, hollow sustain и fake attack. `Aux: Envelope` не доказывает Sustain branch.

## Clarity

Роль: separation и polish. T/S подтверждён. Для drum-forward материала Transient обычно осторожнее Sustain. Риск: glossy/sterile верх или потеря тела.

## Stabilizer

Роль: adaptive spectral balance. Сильнее Sustain допустимо, если сохраняется attack. Риск: съесть air/character и сделать groove плоским. Confirmed base point относится к GUI schema, а не к музыкальному winner.

## Stereo Imager

Роль: ширина. Wow строить через upper Sustain при стабильном low/center/transient image. Исчезновение важного инструмента в mono — hard reject. `Prevent Antiphase` не отменяет correlation/mono/sample-aligned checks.

## Dynamic EQ

Роль: de-ess, anti-glass и codec-safe контроль после widening. Целиться в конкретную harshness, чаще Sustain. Broad high cut делает vocal matte; low bands могут съесть kick/bass и в drum-forward profile запрещены без причины.

## Maximizer

Роль: финальная громкость/True Peak. Делать последним. Actual drive = `Gain`; target display не заменяет Gain. IRC4 Transient для подтверждённого build, True Peak On, Soft Clip/Low Level Boost Off на первом кандидате. Остановиться раньше, если loudness-match показывает потерю drum attack.
