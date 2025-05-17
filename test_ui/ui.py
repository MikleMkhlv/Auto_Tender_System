import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

from services.extraction import extraction

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

# ----------------------------
# Конфигурация
# ----------------------------
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'  # Модель для русского языка
WEIGHTS = {
    'items_text': 0.8,
    'suppliers': 0.2
}
TOP_N = 3

# ----------------------------
# Загрузка данных
# ----------------------------
def load_data(tender_path, procurement_path):
    tenders_df = pd.read_excel(tender_path, engine='openpyxl')
    procurement_df = pd.read_excel(procurement_path, engine='openpyxl')
    
    # Предобработка первой таблицы
    tenders_df['Items_clean'] = tenders_df['Items'].apply(lambda x: re.sub(r'\s+', ' ', str(x)))  # Удаляем лишние пробелы
    
    return tenders_df, procurement_df

# ----------------------------
# Обработка извлеченных сущностей
# ----------------------------
def process_user_data(user_data):
    # Текст товаров
    items_text = ' '.join(user_data['Тендер']['Товары/услуги']) if user_data.get("Тендер").get('Товары/услуги') else ''
        
    # Поставщики
    suppliers = set(user_data.get("Тендер").get('Возможные_поставщики', []))
    
    return {
        'items_text': items_text,
        'suppliers': suppliers
    }

# ----------------------------
# Поиск кода закупки
# ----------------------------
def find_procurement_code(user_data, procurement_df):
    model = SentenceTransformer(MODEL_NAME)
    
    # Векторизация описаний и ключевых слов
    descriptions = procurement_df['Description'].tolist()
    keywords = procurement_df['Key-words'].tolist()
    all_texts = [user_data['items_text']] + descriptions + keywords
    all_texts = [str(x) for x in all_texts if str(x) != 'nan']
    
    text_embeddings = model.encode(all_texts, show_progress_bar=True)
    user_text_vec = text_embeddings[0].reshape(1, -1)
    db_text_vecs = text_embeddings[1:]
    
    # Косинусная схожесть
    similarities = cosine_similarity(user_text_vec, db_text_vecs)[0]
    
    # Находим индексы, соответствующие описаниям и ключевым словам
    description_similarities = similarities[1:len(descriptions)+1]
    keyword_similarities = similarities[len(descriptions)+1:]
    
    # Находим максимальные значения схожести
    procurement_codes = set()

    # Находим максимальную схожесть по описаниям
    max_description_index = np.argmax(description_similarities)
    max_description_value = description_similarities[max_description_index]

    # Находим максимальную схожесть по ключевым словам
    max_keyword_index = np.argmax(keyword_similarities)
    max_keyword_value = keyword_similarities[max_keyword_index]

    # Сравниваем максимальные значения и добавляем соответствующий код
    if max_description_value > 0.5:
        procurement_codes.add(procurement_df.iloc[max_description_index]['NEW HACAT Code'])
    if max_keyword_value > 0.5:
        procurement_codes.add(procurement_df.iloc[max_keyword_index]['NEW HACAT Code'])
    
    return procurement_codes  # Возвращаем уникальные коды закупок

# ----------------------------
# Поиск похожих тендеров
# ----------------------------
def find_similar_tenders(user_data, tenders_df, procurement_codes):
    # Фильтруем тендеры по кодам закупки
    filtered_tenders = tenders_df[tenders_df['Commodity'].isin(procurement_codes)]
    
    if filtered_tenders.empty:
        filtered_tenders = tenders_df # Если нет подходящих кодов закупок, используем всю таблицу
    
    # Инициализация модели SBERT
    model = SentenceTransformer(MODEL_NAME)
    
    # 1. Текстовая схожесть (SBERT)
    db_texts = filtered_tenders['Items_clean'].tolist()
    all_texts = [user_data['items_text']] + db_texts
    
    # Векторизация
    text_embeddings = model.encode(all_texts, show_progress_bar=False)
    user_text_vec = text_embeddings[0].reshape(1, -1)
    db_text_vecs = text_embeddings[1:]
    
    # Косинусная схожесть
    text_sim = cosine_similarity(user_text_vec, db_text_vecs)[0]
    
    # 3. Схожесть поставщиков (Жаккард)
    supplier_sim = []
    for db_suppliers in filtered_tenders['участники'].apply(lambda x: set(str(x).split('; '))):
        intersection = len(user_data['suppliers'] & db_suppliers)
        union = len(user_data['suppliers'] | db_suppliers)
        supplier_sim.append(intersection / union if union != 0 else 0)
    
    # 4. Комбинированная схожесть
    combined_sim = (
        WEIGHTS['items_text'] * text_sim +
        WEIGHTS['suppliers'] * np.array(supplier_sim)
    )
    
    # Топ-N результатов
    top_indices = np.argsort(combined_sim)[-TOP_N:][::-1]
    results = filtered_tenders.iloc[top_indices][['Event #', 'Commodity', 'участники', 'Items_clean']]
    
    return results.to_dict('records')

class ProcurementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Procurement Assistant")
        self.root.geometry("800x600")

        # Переменные для путей к файлам
        self.tender_path = tk.StringVar()
        self.procurement_path = tk.StringVar()
        self.msg_path = tk.StringVar()

        # Создание элементов интерфейса
        self.create_widgets()
        
    def create_widgets(self):
        # Фрейм для загрузки файлов
        file_frame = ttk.LabelFrame(self.root, text="Загрузка файлов")
        file_frame.pack(pady=10, padx=10, fill="x")

        # Поле для файла тендеров
        ttk.Label(file_frame, text="Файл тендеров:").grid(row=0, column=0, sticky="w")
        ttk.Entry(file_frame, textvariable=self.tender_path, width=50).grid(row=0, column=1)
        ttk.Button(file_frame, text="Обзор", command=lambda: self.select_file(self.tender_path)).grid(row=0, column=2)

        # Поле для файла закупок
        ttk.Label(file_frame, text="Файл закупок:").grid(row=1, column=0, sticky="w")
        ttk.Entry(file_frame, textvariable=self.procurement_path, width=50).grid(row=1, column=1)
        ttk.Button(file_frame, text="Обзор", command=lambda: self.select_file(self.procurement_path)).grid(row=1, column=2)

        # Поле для файла сообщения
        ttk.Label(file_frame, text="Файл сообщения:").grid(row=2, column=0, sticky="w")
        ttk.Entry(file_frame, textvariable=self.msg_path, width=50).grid(row=2, column=1)
        ttk.Button(file_frame, text="Обзор", command=lambda: self.select_file(self.msg_path, [("MSG files", "*.msg")])).grid(row=2, column=2)

        # Кнопка запуска
        ttk.Button(self.root, text="Начать анализ", command=self.start_processing).pack(pady=10)

        # Результаты
        result_frame = ttk.LabelFrame(self.root, text="Результаты")
        result_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Коды закупок
        ttk.Label(result_frame, text="Найденные коды закупок:").pack(anchor="w")
        self.codes_label = ttk.Label(result_frame, text="")
        self.codes_label.pack(anchor="w")

        # Таблица результатов
        columns = ("tender_id", "participants", "items", "commodity")
        self.results_tree = ttk.Treeview(
            result_frame, 
            columns=columns, 
            show="headings",
            height=5
        )
        
        self.results_tree.heading("tender_id", text="Номер закупки")
        self.results_tree.heading("participants", text="Участники")
        self.results_tree.heading("items", text="Описание")
        self.results_tree.heading("commodity", text="Commodity")
        
        self.results_tree.column("tender_id", width=100)
        self.results_tree.column("participants", width=200)
        self.results_tree.column("items", width=200)
        self.results_tree.column("commodity", width=150)
        
        self.results_tree.pack(fill="both", expand=True)

        # Статус бар
        self.status_label = ttk.Label(self.root, text="Готово", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def select_file(self, target_var, filetypes=[("All files", "*.*")]):
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            target_var.set(filename)

    def start_processing(self):
        # Проверка заполнения полей
        if not all([self.tender_path.get(), self.procurement_path.get(), self.msg_path.get()]):
            messagebox.showerror("Ошибка", "Пожалуйста, выберите все необходимые файлы")
            return

        # Очистка предыдущих результатов
        self.codes_label.config(text="")
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Запуск обработки в отдельном потоке
        def process():
            try:
                self.status_label = ttk.Label(self.root, text="Обработка", relief=tk.SUNKEN, font=("Helvetica", 16))  # Увеличиваем шрифт
                self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=10)  # Добавляем отступы
                
                # Загрузка данных
                tenders_df, procurement_df = load_data(
                    self.tender_path.get(),
                    self.procurement_path.get()
                )
                
                # Извлечение данных пользователя
                user_data = extraction(self.msg_path.get())
                processed_user_data = process_user_data(user_data)
                
                # Поиск кодов закупок
                procurement_codes = find_procurement_code(processed_user_data, procurement_df)
                
                # Поиск похожих тендеров
                similar_tenders = find_similar_tenders(processed_user_data, tenders_df, procurement_codes)
                
                # Обновление интерфейса
                self.root.after(0, self.update_results, procurement_codes, similar_tenders)
                self.root.after(0, lambda: self.status_label.config(text="Готово"))
                
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text="Ошибка"))

        threading.Thread(target=process, daemon=True).start()

    def update_results(self, procurement_codes, similar_tenders):
        # Обновление кодов закупок
        codes_text = ", ".join(procurement_codes) if procurement_codes else "Коды не найдены"
        self.codes_label.config(text=codes_text)

        # Заполнение таблицы результатов
        for tender in similar_tenders:
            self.results_tree.insert("", "end", values=(
                tender['Event #'],
                tender['участники'],
                tender['Items_clean'],
                tender['Commodity']
            ))

if __name__ == "__main__":
    root = tk.Tk()
    app = ProcurementApp(root)
    root.mainloop()