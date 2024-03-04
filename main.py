import sys
import os
import csv
import tiktoken
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QGridLayout,
    QWidget,
    QFileDialog,
    QLineEdit,
    QLabel,
)


class FolderSelector(QWidget):
    def __init__(self, on_folder_selected):
        """
        A widget for selecting a folder and starting the tokenization process.

        Args:
            on_folder_selected (function): A callback function to be called when a folder is selected.
        """
        super().__init__()
        self.on_folder_selected = on_folder_selected
        self.initUI()


    def initUI(self):
        """
        Initialize the user interface of the widget.
        """
        self.setWindowTitle("Logseq Tokenizer")

        layout = QGridLayout()

        self.fileNameLabel = QLabel("Enter Output CSV File Name:", self)
        layout.addWidget(self.fileNameLabel, 0, 0)

        self.fileNameEdit = QLineEdit(self)
        self.fileNameEdit.setText("output")
        layout.addWidget(self.fileNameEdit, 0, 1)

        self.btn = QPushButton("Select Folder to Tokenize", self)
        self.btn.clicked.connect(self.openFolderDialog)
        layout.addWidget(self.btn, 1, 0)

        self.tokenize_button = QPushButton("Start", self)
        self.tokenize_button.clicked.connect(self.start)
        layout.addWidget(self.tokenize_button, 1, 1)

        self.setLayout(layout)


    def start(self):
        """
        Start the tokenization process by calling the callback function with the selected folder path and file name.
        """
        self.on_folder_selected(self.folder_path, self.file_name)


    def openFolderDialog(self):
        """
        Open a folder dialog to select a folder for tokenization.
        """
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            # Get the file name from the QLineEdit
            file_name = self.fileNameEdit.text()
            if not file_name.endswith(".csv"):
                file_name += ".csv"
            # Pass the selected folder path and file name to the processing function
            self.folder_path = folder_path
            self.file_name = file_name


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """
    Returns the number of tokens in a text string.

    Args:
        string (str): The text string to count tokens from.
        encoding_name (str): The name of the encoding to use for tokenization.

    Returns:
        int: The number of tokens in the text string.
    """
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def tokenize_md_file(file_path):
    """
    Tokenize a Markdown file and return the character count and token count.

    Args:
        file_path (str): The path to the Markdown file.

    Returns:
        tuple: A tuple containing the character count and token count.
    """
    # Read the contents of the Markdown file
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    tokens = num_tokens_from_string(content, "cl100k_base")

    # Character count
    character_count = len(content)

    return character_count, tokens


def calculate_estimated_price(token_count, model_name):
    """
    Calculate the estimated price for a given token count and model name.

    Args:
        token_count (int): The number of tokens.
        model_name (str): The name of the model.

    Returns:
        str: The estimated price as a string.
    """

    # Pricing as of March 2024
    # Prices are in USD per 1,000 tokens
    # Source: https://openai.com/pricing

    pricing = {
        # Embedding models
        "text-embedding-3-small": 0.00002,
        "text-embedding-3-large": 0.00013,
        "text-embedding-ada-002": 0.00010,
    }

    # Calculate the cost per 1,000 tokens and round up to the nearest thousand
    tokens_per_thousand = token_count / 1000
    if model_name in pricing:
        cost_per_thousand = pricing[model_name]
    else:
        cost_per_thousand = 0.01  # Default pricing if model is not in the list

    # Total estimated price
    estimated_price = tokens_per_thousand * cost_per_thousand

    price_str = "{:.6f}".format(
        estimated_price
    )  # Return price as a string with 6 decimal places
    return price_str.ljust(10, "0")


def process_md_files_in_folder(folder_path, csv_file_path):
    """
    Process all .md files in the specified folder and write the results to a CSV file.

    Args:
        folder_path (str): The path to the folder containing the .md files.
        csv_file_path (str): The path to the CSV file to write the results to.

    Returns:
        None
    """
    charTotalCount = 0
    total_tokens = 0

    te_smallTotalPrice = 0.000000
    te_largeTotalPrice = 0.000000
    ada_002TotalPrice = 0.000000

    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        # Write the headers
        writer.writerow(
            [
                "Filename",
                "Character Count",
                "Tokens",
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002",
            ]
        )

        # Iterate over all .md files in the specified folder
        for filename in os.listdir(folder_path):
            if filename.endswith(".md"):
                file_path = os.path.join(folder_path, filename)
                char_count, tokens = tokenize_md_file(file_path)

                charTotalCount += char_count
                total_tokens += tokens

                # Calculate the estimated price
                te_smallEstimatedPrice = calculate_estimated_price(
                    tokens, "text-embedding-3-small"
                )
                te_largeEstimatedPrice = calculate_estimated_price(
                    tokens, "text-embedding-3-large"
                )
                ada_002EstimatedPrice = calculate_estimated_price(
                    tokens, "text-embedding-ada-002"
                )

                # Add to total price
                te_smallTotalPrice += float(te_smallEstimatedPrice)
                te_largeTotalPrice += float(te_largeEstimatedPrice)
                ada_002TotalPrice += float(ada_002EstimatedPrice)

                # Write the data to the CSV file
                writer.writerow(
                    [
                        filename,
                        char_count,
                        tokens,
                        te_smallEstimatedPrice,
                        te_largeEstimatedPrice,
                        ada_002EstimatedPrice,
                    ]
                )

        # Write the totals data to the CSV file
        writer.writerow(
            [
                folder_path,
                charTotalCount,
                total_tokens,
                "{:.6f}".format(te_smallTotalPrice),
                "{:.6f}".format(te_largeTotalPrice),
                "{:.6f}".format(ada_002TotalPrice),
            ]
        )


def start_processing(folder_path, file_name):
    """
    Start the processing of Markdown files in a folder and write the results to a CSV file.

    Args:
        folder_path (str): The path to the folder containing the Markdown files.
        file_name (str): The name of the output CSV file.

    Returns:
        None
    """
    process_md_files_in_folder(folder_path, file_name)
    print(f"CSV file '{file_name}' has been created and data has been written.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = FolderSelector(start_processing)
    ex.show()
    sys.exit(app.exec())
