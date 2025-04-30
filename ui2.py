import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QFormLayout, 
                            QLineEdit, QPushButton, QFileDialog, QLabel, 
                            QTableWidget, QTableWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt
from comparation import TenderMatcher  # Импортируйте ваш класс из соответствующего модуля

class TenderMatcherUI(QWidget):
    def __init__(self):
        super().__init__()
        self.tender_matcher = TenderMatcher()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Tender Matcher')
        self.setGeometry(100, 100, 800, 600)
        
        # Create widgets
        self.goods_input = QLineEdit()
        self.suppliers_input = QLineEdit()
        
        self.tender_file_btn = QPushButton('Select Tenders File')
        self.tender_file_label = QLabel('No file selected')
        self.procurement_file_btn = QPushButton('Select Procurement File')
        self.procurement_file_label = QLabel('No file selected')
        
        self.find_btn = QPushButton('Find Matches')
        self.results_table = QTableWidget()
        
        # Setup layout
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        form_layout.addRow('Goods/Services (comma-separated):', self.goods_input)
        form_layout.addRow('Possible Suppliers (comma-separated):', self.suppliers_input)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.tender_file_btn)
        layout.addWidget(self.tender_file_label)
        layout.addWidget(self.procurement_file_btn)
        layout.addWidget(self.procurement_file_label)
        layout.addWidget(self.find_btn)
        layout.addWidget(self.results_table)
        
        self.setLayout(layout)
        
        # Connect signals
        self.tender_file_btn.clicked.connect(lambda: self.select_file('tender'))
        self.procurement_file_btn.clicked.connect(lambda: self.select_file('procurement'))
        self.find_btn.clicked.connect(self.process_data)
        
        # Configure table
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            'Event #', 'Commodity', 'Participants', 'Items'
        ])
        self.results_table.setSortingEnabled(True)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        
    def select_file(self, file_type):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f'Select {file_type.capitalize()} File',
            '', 
            'Excel Files (*.xlsx)'
        )
        
        if file_path:
            if file_type == 'tender':
                self.tender_file_label.setText(file_path)
            else:
                self.procurement_file_label.setText(file_path)
                
    def validate_input(self):
        errors = []
        if self.tender_file_label.text() == 'No file selected':
            errors.append('Please select a tender file')
        if self.procurement_file_label.text() == 'No file selected':
            errors.append('Please select a procurement file')
        if not self.goods_input.text().strip():
            errors.append('Please enter goods/services')
            
        if errors:
            QMessageBox.warning(self, 'Input Error', '\n'.join(errors))
            return False
        return True
    
    def process_data(self):
        if not self.validate_input():
            return
            
        try:
            # Prepare user data
            user_data = {
                "Тендер": {
                    "Товары/услуги": [x.strip() for x in self.goods_input.text().split(',')],
                    "Возможные_поставщики": [x.strip() for x in self.suppliers_input.text().split(',') if x.strip()]
                }
            }
            
            # Load data
            tenders_df, procurement_df = self.tender_matcher.load_data(
                self.tender_file_label.text(),
                self.procurement_file_label.text()
            )
            
            # Process user data
            processed_data = self.tender_matcher.process_user_data(user_data)
            
            # Find procurement codes
            procurement_codes = self.tender_matcher.find_procurement_code(processed_data, procurement_df)
            
            # Find similar tenders
            results = self.tender_matcher.find_similar_tenders(processed_data, tenders_df, procurement_codes)
            
            # Display results
            self.show_results(results)
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred:\n{str(e)}')
    
    def show_results(self, results):
        self.results_table.setRowCount(len(results))
        
        for row_idx, result in enumerate(results):
            self.results_table.setItem(row_idx, 0, QTableWidgetItem(str(result['Event #'])))
            self.results_table.setItem(row_idx, 1, QTableWidgetItem(str(result['Commodity'])))
            self.results_table.setItem(row_idx, 2, QTableWidgetItem(str(result['участники'])))
            self.results_table.setItem(row_idx, 3, QTableWidgetItem(str(result['Items_clean'])))
            
        self.results_table.resizeColumnsToContents()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TenderMatcherUI()
    window.show()
    sys.exit(app.exec_())