# 11. Prompt Usage Rules

Начинать с `prompts/START_NEW_CHAT_UNIVERSAL.md` и фиксировать:

```text
главный источник = Universal Core v1.3
source WAV и optional reference/codec files
current base/winner XML
PluginVer/Build and decoded ElementChain
musical priority: drums/vocal/width/tone/loudness
active module and changed-only scope
```

Каждый ответ о stage должен назвать active module, базу, provenance, что изменено/не изменено, probe или candidate, render names и критерии проверки.

Если safe settings почти не слышны, не делать вид, что stage завершён: предложить one-module boundary probe. Если mono/codec/transient guard провален — прямо назвать reject и следующий минимальный repair.

При ошибке признать причину, отменить ошибочную базу и строить fixed stage от последнего принятого winner.
