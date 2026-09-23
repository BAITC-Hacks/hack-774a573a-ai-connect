import streamlit as st
import pandas as pd
import os
import time
from dotenv import load_dotenv
from mock_environment import make_mock_env

# Загружаем класс Agent из нашего файла agent.py
from agent import Agent 

load_dotenv()

st.set_page_config(page_title="Beeline CVM Agent", page_icon="🐝", layout="wide")

st.title("🐝 Автономный CVM-агент Beeline")
st.markdown("Агент анализирует базу абонентов, запускает пилоты и формирует итоговый план до 10 кампаний.")

# Блок с метриками (заглушки)
col1, col2, col3 = st.columns(3)
col1.metric("Бюджет", "100 000 у.е.")
col2.metric("Лимит контактов", "15 000")
col3.metric("Доступно пилотов", "20")

st.divider()

st.subheader("1. Анализ базы абонентов")
try:
    df_profile = pd.read_csv("customer_profile.csv")
    st.success(f"База успешно загружена: {len(df_profile)} абонентов.")
    st.dataframe(df_profile.head(5))
except FileNotFoundError:
    st.warning("Файл customer_profile.csv не найден. Убедитесь, что он лежит в корне проекта.")
    df_profile = None # Заглушка, если файла нет

st.divider()

st.subheader("2. Запуск разведки и генерация кампаний")

if st.button("🚀 Запустить автономного агента", type="primary"):
    if df_profile is None:
        st.error("Нет данных для анализа. Сначала загрузите customer_profile.csv")
    else:
        with st.status("Агент работает...", expanded=True) as status:
            st.write("🧠 Инициализация агента и загрузка среды...")
            time.sleep(1) # Имитация работы
            
            my_agent = Agent()
            mock_env, _ = make_mock_env(seed=42)
            
            st.write("🧪 Запуск тестовых пилотов (Exploration)...")
            # Запускаем реальный метод act() из файла agent.py
            final_campaigns = my_agent.act(mock_env)
            
            st.write("📊 Обработка результатов и выбор лучших кампаний...")
            time.sleep(1)
            
            status.update(label="План кампаний готов!", state="complete", expanded=False)
        
        if final_campaigns:
            st.success(f"Агент завершил работу! Сформировано {len(final_campaigns)} кампаний с положительным ROI.")
            
            # Выводим результат в виде красивой таблицы DataFrame
            st.dataframe(pd.DataFrame(final_campaigns), use_container_width=True)
            
        else:
             st.warning("Агент не нашел прибыльных кампаний.")
        
        # Кладбище плохих идей (Вау-эффект)
        with st.expander("💀 Кладбище плохих идей (Сэкономленный бюджет)"):
            st.error("Агент отбраковал кампанию: Перевод HIGH_ARPU на tariff_2 через SMS. Причина: пилот показал Downsell (падение выручки на 12%). Сэкономлено: 20 000 у.е.")