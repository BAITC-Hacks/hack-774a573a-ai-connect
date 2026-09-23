import pandas as pd
import os
from openai import OpenAI

# Инициализируем клиента. На хакатоне скрипт жюри сам подставит ключ в os.environ
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

class Agent:
    def act(self, env):
        """
        Главный метод агента. Получает среду env и возвращает список до 10 кампаний.
        """
        profile = env.customer_profile
        
        # 1. СТАТИСТИКА: Собираем агрегированную сводку для LLM
        # LLM не съест 23 000 строк, поэтому мы сжимаем данные
        cells = (profile.groupby(["current_tariff", "arpu_segment"], observed=True)
                 .agg(n=("ID_NUMBER", "size"), arpu=("predicted_arpu", "mean"))
                 .reset_index()
                 .sort_values("n", ascending=False))

        # 2. ГЕНЕРАЦИЯ ГИПОТЕЗ (Пока базовая, позже подключим LLM)
        candidates = []
        for _, cell in cells.head(4).iterrows():
            for target in ["tariff_8", "tariff_9"]:
                if target == cell.current_tariff:
                    continue
                candidates.append((cell.current_tariff, cell.arpu_segment, target))

        # 3. ПРОВЕДЕНИЕ ПИЛОТОВ (Разведка)
        observed = []
        for current_tariff, segment, target in candidates:
            if env.pilots_left <= 0 or env.remaining_budget < 5000:
                break
            try:
                # Делаем тестовый заброс на 150 абонентов через дешевые sms
                res = env.run_pilot(
                    target_tariff=target, channel="sms", n_customers=150,
                    filter_arpu_segment=segment, filter_current_tariff=current_tariff,
                )
                observed.append({
                    "current_tariff": current_tariff, "arpu_segment": segment,
                    "target_tariff": target, "ratio": res["observed_lift_ratio"],
                })
            except RuntimeError:
                break

        if not observed:
            return []

        # 4. ВЫБОР ФИНАЛЬНЫХ КАМПАНИЙ (Эксплуатация)
        # Отбираем только то, что принесло прибыль (ratio > 0)
        best = pd.DataFrame(observed).sort_values("ratio", ascending=False)
        campaigns = []
        for _, row in best.head(10).iterrows(): # Максимум 10 кампаний по правилам
            if row["ratio"] <= 0:
                continue
            campaigns.append({
                "campaign_name": f"Promo_{row['current_tariff']}_to_{row['target_tariff']}",
                "filter_arpu_segment": row["arpu_segment"],
                "filter_current_tariff": row["current_tariff"],
                "target_tariff": row["target_tariff"],
                "channel": "sms", # Позже поручим LLM выбирать канал связи
            })
            
        return campaigns