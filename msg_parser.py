import json
import pandas as pd
from extract_msg import Message
import os

class MsgParser:
    def __init__(self, msg_file_path):
        """
        Инициализация парсера.
        :param msg_file_path: Путь к .msg файлу.
        """
        self.msg_file_path = msg_file_path
        self.msg = None
        self.msg_dict = {}

    def parse_excel_to_string(self, file_path, format='markdown'):
        """
        Чтение Excel-файла и преобразование в строку.
        :param file_path: Путь к Excel-файлу.
        :param format: Формат вывода ('markdown' или 'csv').
        :return: Строка с данными таблицы.
        """
        df = pd.read_excel(file_path)
        if format == 'markdown':
            return df.to_markdown(index=False)
        elif format == 'csv':
            return df.to_csv(index=False)
        else:
            raise ValueError("Неподдерживаемый формат. Используйте 'markdown' или 'csv'.")

    def parse_msg(self):
        """
        Парсинг .msg файла и обработка вложений.
        """
        # Открываем и парсим .msg файл
        self.msg = Message(self.msg_file_path)

        # Собираем основные данные
        self.msg_dict = {
            "sender": self.msg.sender,
            "to": self.msg.to,
            "subject": self.msg.subject,
            "date": str(self.msg.date),  # Преобразуем datetime в строку
            "body": self.msg.body,
            "attachments": []
        }

        # Обрабатываем вложения
        for attachment in self.msg.attachments:
            attachment_info = {
                "filename": attachment.longFilename,
                "data": None
            }

            # Если вложение — это Excel-файл, парсим его
            if attachment.longFilename.endswith(('.xlsx', '.xls')):
                # Сохраняем временный файл
                temp_file_path = attachment.longFilename
                with open(temp_file_path, 'wb') as f:
                    f.write(attachment.data)

                # Парсим Excel и преобразуем в строку
                try:
                    excel_data = self.parse_excel_to_string(temp_file_path, format='markdown')
                    attachment_info["data"] = excel_data
                except Exception as e:
                    attachment_info["error"] = f"Ошибка при чтении Excel: {str(e)}"
                finally:
                    # Удаляем временный файл
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)

            self.msg_dict["attachments"].append(attachment_info)

    def to_json(self):
        """
        Преобразование данных в JSON-строку.
        :return: JSON-строка с данными из .msg файла.
        """
        if not self.msg_dict:
            raise ValueError("Данные не были распарсены. Вызовите метод parse_msg().")
        return json.dumps(self.msg_dict, ensure_ascii=False, indent=4)

    def close(self):
        """
        Закрытие .msg файла.
        """
        if self.msg:
            self.msg.close()

    def __enter__(self):
        """
        Поддержка контекстного менеджера (with).
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Закрытие файла при выходе из контекстного менеджера.
        """
        self.close()

