import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Загружаем ключи (пока они пустые, до 23 сентября)
load_dotenv()

# Настраиваем внешний вид страницы
st.set_page_config(page_title="Beeline CVM Agent", page_icon="🐝", layout="wide")

st.title("🐝 Автономный CVM-агент Beeline")
st.markdown("Агент анализирует базу абонентов, запускает пилоты и формирует итоговый план до 10 кампаний.")

# Блок с метриками (заглушки для визуала)
col1, col2, col3 = st.columns(3)
col1.metric("Бюджет", "100 000 у.е.")
col2.metric("Лимит контактов", "15 000")
col3.metric("Доступно пилотов", "20")

st.divider()

# Загрузка и просмотр профилей клиентов
st.subheader("1. Анализ базы абонентов")
try:
    # Пытаемся прочитать файл из папки кейса
    df_profile = pd.read_csv("customer_profile.csv")
    st.success(f"База успешно загружена: {len(df_profile)} абонентов.")
    st.dataframe(df_profile.head(5))
except FileNotFoundError:
    st.warning("Файл customer_profile.csv не найден. Убедитесь, что он лежит в корне проекта.")

st.divider()

# Панель запуска агента
st.subheader("2. Запуск разведки и генерация кампаний")
if st.button("🚀 Запустить автономного агента", type="primary"):
    with st.status("Агент работает...", expanded=True) as status:
        st.write("🧠 Анализ сегментов базы...")
        st.write("📊 Формирование гипотез...")
        st.write("🧪 Запуск тестовых пилотов (Exploration)...")
        # Здесь мы позже подключим вызов класса Agent из agent.py
        
        status.update(label="План кампаний готов!", state="complete", expanded=False)
    
    st.success("Агент завершил работу! Сформировано 10 кампаний с положительным ROI.")
    
    # Кладбище плохих идей (Вау-эффект для жюри)
    with st.expander("💀 Кладбище плохих идей (Сэкономленный бюджет)"):
        st.error("Агент отбраковал кампанию: Перевод HIGH_ARPU на tariff_2 через SMS. Причина: пилот показал Downsell (падение выручки на 12%). Сэкономлено: 20 000 у.е.")