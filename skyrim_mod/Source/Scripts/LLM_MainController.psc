Scriptname LLM_MainController extends Quest

; Свойства для настройки в Creation Kit
Int Property PushToTalkKey = 47 Auto ; Клавиша 'V' по умолчанию
Actor Property PlayerRef Auto

; Пути для обмена данными.
; ВНИМАНИЕ: JContainers пишет пути относительно корня игры (где SkyrimSE.exe), поэтому жестко задаем Data/
String Property REQUEST_PATH = "Data/Interface/llm_bridge/request.json" Auto
String Property RESPONSE_PATH = "Data/Interface/llm_bridge/response.json" Auto
String Property START_FLAG = "Data/Interface/llm_bridge/recording_start.flag" Auto
String Property STOP_FLAG = "Data/Interface/llm_bridge/recording_stop.flag" Auto
String Property AUDIO_PATH = "Data/Sound/Voice/llm_mod/" Auto

bool bIsRecording = false
bool bIsWaitingForResponse = false
Actor CurrentTalkTarget = None

Event OnInit()
    RegisterForKey(PushToTalkKey)
    Debug.Notification("LLM Voice Mod инициализирован. Нажмите V для общения.")
EndEvent

Event OnKeyDown(Int KeyCode)
    If KeyCode == PushToTalkKey && !bIsRecording && !bIsWaitingForResponse
        ; Используем функцию SKSE для получения цели в прицеле
        CurrentTalkTarget = Game.GetCurrentCrosshairRef() as Actor

        If CurrentTalkTarget != None && !CurrentTalkTarget.IsDead() && CurrentTalkTarget.GetRace().HasKeyword(Keyword.GetKeyword("ActorTypeNPC"))
            StartRecording(CurrentTalkTarget)
        Else
            Debug.Notification("LLM: Нет подходящей цели для разговора.")
        EndIf
    EndIf
EndEvent

Event OnKeyUp(Int KeyCode, Float TimePressed)
    If KeyCode == PushToTalkKey && bIsRecording
        StopRecording()
    EndIf
EndEvent

Function StartRecording(Actor Target)
    bIsRecording = true
    Debug.Notification("LLM: Запись началась...")

    ; 1. Сбор контекста (Имя, Локация, Отношения, Инвентарь)
    String npcName = Target.GetBaseObject().GetName()

    String locationName = "Скайрим (Дикая местность)"
    Location curLoc = PlayerRef.GetCurrentLocation()
    If curLoc != None
        locationName = curLoc.GetName()
    EndIf

    int relationInt = Target.GetRelationshipRank(PlayerRef)
    String relationStr = "Нейтральное"
    If relationInt >= 3
        relationStr = "Союзник"
    ElseIf relationInt > 0
        relationStr = "Дружелюбное"
    ElseIf relationInt < 0
        relationStr = "Враждебное"
    EndIf

    ; Получение базового инвентаря игрока (оружие в руках как контекст)
    String rightHand = "Ничего"
    If PlayerRef.GetEquippedWeapon(false) != None
        rightHand = PlayerRef.GetEquippedWeapon(false).GetName()
    EndIf

    ; Получение активного квеста (Если установлен PapyrusUtil или через массив) - для простоты берем базовую инфу
    String currentAction = "Исследует мир"
    If PlayerRef.IsSneaking()
        currentAction = "Крадется"
    ElseIf PlayerRef.IsWeaponDrawn()
        currentAction = "Оружие наготове, готов к бою"
    EndIf

    ; Создаем JSON объект через JContainers
    int contextObj = JMap.object()

    JMap.setStr(contextObj, "npc_name", npcName)
    JMap.setStr(contextObj, "location", locationName)
    JMap.setStr(contextObj, "player_name", PlayerRef.GetBaseObject().GetName())
    JMap.setStr(contextObj, "relationship", relationStr)
    JMap.setStr(contextObj, "player_right_hand", rightHand)
    JMap.setStr(contextObj, "player_action", currentAction)

    ; Сохраняем в файл request.json
    JValue.writeToFile(contextObj, REQUEST_PATH)

    ; 2. Создаем файл-флаг для сервера (Для этого можно записать пустой JSON)
    int emptyObj = JMap.object()
    JValue.writeToFile(emptyObj, START_FLAG)

    ; Очистка памяти JContainers
    JValue.release(contextObj)
    JValue.release(emptyObj)
EndFunction

Function StopRecording()
    bIsRecording = false
    bIsWaitingForResponse = true
    Debug.Notification("LLM: Обработка...")

    ; Создаем флаг остановки
    int emptyObj = JMap.object()
    JValue.writeToFile(emptyObj, STOP_FLAG)
    JValue.release(emptyObj)

    ; Начинаем поллинг (ожидание ответа)
    RegisterForSingleUpdate(0.5)
EndFunction

Event OnUpdate()
    If bIsWaitingForResponse
        ; Проверяем, существует ли response.json. В JContainers если файл есть и он валидный JSON, он загрузится.
        int responseObj = JValue.readFromFile(RESPONSE_PATH)

        If responseObj != 0
            ; Файл найден! Читаем данные
            String responseText = JMap.getStr(responseObj, "text")
            String audioFile = JMap.getStr(responseObj, "audio_file")

            ; Проверка на пустой ответ (защита от чтения пустого JSON)
            If responseText != ""
                ; Воспроизводим в игре
                PlayLLMResponse(responseText, audioFile)

                ; Важно: очищаем response.json, чтобы цикл не зациклился на старом ответе
                ; Мы не используем JMap.object() для пустого файла, чтобы не засорять память,
                ; просто удалим данные внутри объекта и запишем его, либо просто создадим новый,
                ; но сервер и так его удалит в начале следующей записи. Для подстраховки:
                int emptyObj = JMap.object()
                JValue.writeToFile(emptyObj, RESPONSE_PATH)
                ; В JContainers не нужно делать release для вновь созданного объекта, если мы не вызывали retain.
            EndIf

            JValue.release(responseObj)
            bIsWaitingForResponse = false
        Else
            ; Файл еще не готов, ждем дальше (Таймаут можно добавить позже)
            RegisterForSingleUpdate(0.5)
        EndIf
    EndIf
EndEvent

Function PlayLLMResponse(String text, String audioFile)
    ; Показ субтитров
    Debug.Notification(CurrentTalkTarget.GetBaseObject().GetName() + ": " + text)

    ; Примечание по воспроизведению аудио:
    ; Движок Skyrim кэширует .wav файлы. Использование одного и того же файла response.wav
    ; приведет к тому, что всегда будет проигрываться первая сгенерированная фраза.
    ; Для полноценного локального проигрывания динамического аудио (с уникальными именами)
    ; требуется использование плагинов типа Fuz Ro D-oh или написание кастомного SKSE-плагина.

    Debug.Trace("LLM_MOD: Сгенерирован ответ '" + text + "'. Аудиофайл: " + audioFile)
    Debug.Trace("LLM_MOD: Для проигрывания звука требуется дополнительный SKSE плагин, поддерживающий динамические пути.")

    CurrentTalkTarget = None
EndFunction
