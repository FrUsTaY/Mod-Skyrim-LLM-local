import requests
import json

class LLMClient:
    def __init__(self, base_url="http://127.0.0.1:1234/v1"):
        """
        Инициализирует клиент для LM Studio.
        По умолчанию LM Studio поднимает сервер на 1234 порту с OpenAI-совместимым API.
        """
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}

    def _build_system_prompt(self, context):
        """
        Формирует System Prompt на основе контекста из игры (из файла request.json).
        """
        npc_name = context.get("npc_name", "Неизвестный")
        location = context.get("location", "Скайрим")
        player_name = context.get("player_name", "Драконорожденный")
        relationship = context.get("relationship", "нейтральное")
        player_right_hand = context.get("player_right_hand", "Ничего")
        player_action = context.get("player_action", "Исследует мир")
        quests = context.get("quests", [])

        prompt = (
            f"Ты - персонаж из игры The Elder Scrolls V: Skyrim. Твое имя {npc_name}. "
            f"Ты находишься в локации {location}. Ты разговариваешь с игроком по имени {player_name}. "
            f"Твое отношение к игроку: {relationship}. "
            f"Текущие действия игрока: {player_action}. Оружие в правой руке игрока: {player_right_hand}. "
            "Реагируй на действия игрока (если он крадется или держит оружие - это может быть подозрительно). "
            "Отвечай от лица своего персонажа, соблюдая лор Скайрима. "
            "Твои ответы должны быть короткими (1-3 предложения), так как они будут озвучены. "
            "Не используй эмодзи или действия в звездочках (например *вздыхает*), только текст, который можно произнести. "
            "Отвечай исключительно на русском языке."
        )

        if quests:
            prompt += f" Сейчас ты знаешь о следующих событиях/квестах: {', '.join(quests)}."

        return prompt

    def generate_response(self, user_text, context_data):
        """
        Отправляет запрос в LM Studio и возвращает сгенерированный ответ.
        """
        system_prompt = self._build_system_prompt(context_data)

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.7,
            "max_tokens": 150 # Ограничиваем длину ответа для быстроты генерации и озвучки
        }

        print(f"Отправка запроса в LM Studio для NPC: {context_data.get('npc_name', 'Unknown')}...", flush=True)
        try:
            response = requests.post(f"{self.base_url}/chat/completions", headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            response_data = response.json()

            reply = response_data['choices'][0]['message']['content'].strip()
            print(f"Ответ LLM: {reply}", flush=True)
            return reply
        except Exception as e:
            print(f"Ошибка при обращении к LLM: {e}", flush=True)
            return "Прости, я сейчас не могу говорить."

if __name__ == "__main__":
    # Test script
    client = LLMClient()
    mock_context = {
        "npc_name": "Балгруф Старший",
        "location": "Драконий Предел, Вайтран",
        "player_name": "Довакин",
        "relationship": "уважительное",
        "quests": ["Дракон напал на Хелген"]
    }
    # Это выдаст ошибку таймаута в песочнице, так как LM Studio не запущен
    # client.generate_response("Привет, ярл. Что слышно о драконах?", mock_context)
