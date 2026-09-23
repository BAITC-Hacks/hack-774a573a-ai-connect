import pandas as pd
import os
import json
from openai import OpenAI

# 1. Мультиагентная архитектура (Fallback)[cite: 10]
api_key_openai = os.environ.get("OPENAI_API_KEY")
client_main = OpenAI(api_key=api_key_openai) if api_key_openai else None

api_key_nvidia = os.environ.get("NVIDIA_API_KEY")
client_nvidia = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key_nvidia
) if api_key_nvidia else None


class Agent:
    def act(self, env):
        """
        Главный метод агента. Требование ТЗ: возвращать list[dict] до 10 кампаний[cite: 2].
        """
        profile = env.customer_profile
        
        # 1. СТАТИСТИКА: Агрегируем сводку для LLM (нельзя передавать все 23 000 строк)[cite: 2, 3]
        cells = (profile.groupby(["current_tariff", "arpu_segment", "data_segment"], observed=True)
                 .agg(n=("ID_NUMBER", "size"), avg_arpu=("predicted_arpu", "mean"))
                 .reset_index()
                 .sort_values("n", ascending=False)
                 .head(10)) # Берем топ-10 самых массовых сегментов
                 
        stats_str = cells.to_string(index=False)

        # 2. ПРОМПТ ДЛЯ ИИ-АНАЛИТИКА[cite: 3]
        system_prompt = f"""
        Ты - Senior CVM Analyst в телеком-компании. Твоя цель - выбрать сегменты для смены тарифа, чтобы максимизировать ARPU[cite: 3].
        Вот топ сегментов нашей базы:
        {stats_str}
        
        Сгенерируй 5 перспективных гипотез для пилотов. Дорогим абонентам предлагай звонки (call) и дорогие тарифы, дешевым - sms/push.
        Верни ТОЛЬКО валидный JSON-массив объектов с ключами: 'current_tariff', 'arpu_segment', 'target_tariff' (от tariff_1 до tariff_21), 'channel' (push, sms, digital_ads, call).
        """

        hypotheses = []

        # 3. ГЕНЕРАЦИЯ ГИПОТЕЗ ЧЕРЕЗ LLM С FALLBACK-ЛОГИКОЙ[cite: 2, 10]
        try:
            if client_main:
                # Пытаемся спросить OpenAI[cite: 10]
                response = client_main.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": system_prompt}]
                )
                raw_json = response.choices[0].message.content
                # Очищаем ответ от маркдауна, если LLM его добавила
                cleaned_json = raw_json.replace("```json", "").replace("```", "").strip()
                hypotheses = json.loads(cleaned_json)
        except Exception as e:
            print(f"OpenAI недоступен или ошибка парсинга: {e}. Переходим к резервной логике.")
            
        # Если LLM не справилась (или ключи пустые до 23 сентября), включаем базовые эвристики, чтобы не получить 0 баллов[cite: 2]
        if not hypotheses:
            for _, cell in cells.head(5).iterrows():
                target = "tariff_15" if cell.arpu_segment == "HIGH" else "tariff_5"
                if target != cell.current_tariff:
                    hypotheses.append({
                        "current_tariff": cell.current_tariff,
                        "arpu_segment": cell.arpu_segment,
                        "target_tariff": target,
                        "channel": "sms" if cell.arpu_segment == "LOW" else "digital_ads"
                    })

        # 4. ПРОВЕДЕНИЕ ПИЛОТОВ (Разведка)[cite: 2]
        observed = []
        for hyp in hypotheses:
            if env.pilots_left <= 0 or env.remaining_budget < 5000:
                break
            try:
                # Тестируем каждую гипотезу на небольшой выборке (150 человек)[cite: 2]
                res = env.run_pilot(
                    target_tariff=hyp["target_tariff"], 
                    channel=hyp["channel"], 
                    n_customers=150,
                    filter_arpu_segment=hyp["arpu_segment"], 
                    filter_current_tariff=hyp["current_tariff"]
                )
                observed.append({
                    "campaign_name": f"Promo_{hyp['current_tariff']}_to_{hyp['target_tariff']}",
                    "filter_arpu_segment": hyp["arpu_segment"],
                    "filter_current_tariff": hyp["current_tariff"],
                    "target_tariff": hyp["target_tariff"],
                    "channel": hyp["channel"],
                    "roi": res["observed_lift_ratio"] # Сохраняем результат пилота[cite: 3]
                })
            except RuntimeError:
                continue

        # 5. ВЫБОР ФИНАЛЬНЫХ КАМПАНИЙ (Эксплуатация)[cite: 3]
        if not observed:
            return []

        # Сортируем пилоты по прибыльности и забираем максимум 10 лучших с положительным ROI[cite: 2]
        best_campaigns = pd.DataFrame(observed).sort_values("roi", ascending=False)
        
        final_plan = []
        for _, row in best_campaigns.head(10).iterrows():
            if row["roi"] > 0: # Жестко отсекаем downsell[cite: 3]
                final_plan.append({
                    "campaign_name": row["campaign_name"],
                    "filter_arpu_segment": row["filter_arpu_segment"],
                    "filter_current_tariff": row["filter_current_tariff"],
                    "target_tariff": row["target_tariff"],
                    "channel": row["channel"]
                })
                
        return final_plan