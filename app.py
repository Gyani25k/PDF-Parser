import pdfplumber
import pandas as pd
import re
from flask import Flask, request, jsonify, render_template
import json

app = Flask(__name__, template_folder='template')


def process_description(row):
    """
    Adjusts the description and amount format from the extracted PDF data.

    If the description ends with a '-', 
    it removes it and prepends '-' to the amount.

    Args:
        row (pd.Series): A row containing 'Description' and 'Amount' columns.

    Returns:
        pd.Series: Updated series with corrected 'Description' and 'Amount'.
    """
    description = row['Description']
    amount = row['Amount']
    if description.endswith('-'):
        description = description[:-1]
        amount = '-' + amount
    return pd.Series([description, amount], index=['Description', 'Amount'])


@app.route('/')
def homepageV1():
    """
    Renders the homepage.
    Comes from HTML templates defined in the 'template' folder.

    Returns:
        HTML content
    """
    return render_template('homepage.html')


def extract_from_pdf(pdf_file_path):
    """
    Extracts transaction data from a PDF file using various methods.

    Tried methods include searching for transaction
    sections and configuring data into columns.

    Args:
        pdf_file_path: The path to the PDF file.

    Returns:
        dict: A dictionary containing extracted data and a status message.
    """
    # Attempt method 1
    column1 = []
    column2 = []
    column3 = []

    with pdfplumber.open(pdf_file_path) as pdf:
        is_transactions_section = false
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            for line in lines:
                if is_transactions_section:
                    if line.strip() and line[:8].count('/') == 2:
                        parts = line.split(' ', 2)
                        if len(parts) == 3:
                            column1.append(parts[0])
                            column2.append(parts[1])
                            column3.append(parts[2])
                elif "Transactions" in line:
                    is_transactions_section = true

    if column1 and column2 and column3:
        df = pd.DataFrame({
            'Transaction Date': column1,
            'Post Date': column2,
            'Description': column3
        })

         # Further data processing if initial columns are populated
        df['NewDescription'] = ""
        df['Amount'] = ""
        df['Category'] = ""

        for i, description in enumerate(df['Description']):
            a = description.split("$")
            if len(a) == 2:
                numeric_part = re.search(r'([\d.]+)\s*(\w+)', a[1])
                if numeric_part:
                    amount = "$" + numeric_part.group(1)
                    category = numeric_part.group(2)
                    if category == 'Payments':
                        category = 'Payments and Credits'
                    df.at[i, 'NewDescription'] = a[0]
                    df.at[i, 'Amount'] = amount
                    df.at[i, 'Category'] = category

        df = df.drop(columns=['Description'])
        response = []
        for index, row in df.iterrows():
            response.append({"Transaction Date": row['Transaction Date'],
                             "Post Date": row['Post Date'],
                             "Description": row['NewDescription'],
                             "Amount": row['Amount'],
                             "Category": row['Category']})

        temp = {"data": response, "message": "Data Extracted Successfully"}

    else:
        # If method 1 fails, attempt method 2
        transactions = []
        with pdfplumber.open(pdf_file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                pattern = r"(\w{3} \d{1,2}) (\w{3} \d{1,2}) (.+?) (\$\d+\.\d{2})"
                matches = re.findall(pattern, text)
                for match in matches:
                    trans_date, post_date, description, amount = match
                    transactions.append({
                        "Transaction Date": trans_date,
                        "Post Date": post_date,
                        "Description": description,
                        "Amount": amount
                    })

        if transactions:
            df = pd.DataFrame(transactions)
            response = []
            for index, row in df.iterrows():
                response.append({"Transaction Date": row['Transaction Date'],
                                 "Post Date": row['Post Date'],
                                 "Description": row['Description'],
                                 "Amount": row['Amount']})

            temp = {"data": response, "message": "Data Extracted Successfully"}
        else:
            # Further strategies are attempted below, this continues through numbered methods
            transactions1 = []

            with pdfplumber.open(pdf_file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    # Define a pattern to match transaction lines
                    pattern = r"(\d{2}/\d{2})?\s+(\d{2}/\d{2})?\s+([\w\s.]+?)\s+(-?\$\d+\.\d{2})"
                    matches = re.findall(pattern, text)
                    for match in matches:
                        sale_date, post_date, description, amount = match

                        # If sale_date is not present but post_date is, use post_date as sale_date
                        if not sale_date and post_date:
                            sale_date = ''

                        transactions1.append({
                            "SaleDate": sale_date,
                            "PostDate": post_date,
                            "Description": description,
                            "Amount": amount
                        })

            if transactions1:
                response = []
                df = pd.DataFrame(transactions1)
                print(df.columns)
                for index, row in df.iterrows():
                    response.append({
                        "SaleDate": row['SaleDate'],
                        "PostDate": row['PostDate'],
                        "Description": row['Description'],
                        "Amount": row['Amount']
                    })

                temp = {"data": response, "message": "Data Extracted Successfully"}
            else:
                # Continue with additional methods
                desired_section = ""
                # Define a regex pattern to extract all transactions
                pattern = r'(\d{2}/\d{2}/\d{2})\s(.+?)\s(-[\d,.]+)'

                # Find all matches in the section
                matches = re.findall(pattern, desired_section)

                # Create a DataFrame from the extracted transactions
                data = []
                for match in matches:
                    date = match[0]
                    description = match[1]
                    amount = match[2]
                    data.append([date, description, amount])

                df = pd.DataFrame(data, columns=["Date", "Description", "Amount"])
                print(df.columns)
                response = []
                for index, row in df.iterrows():
                    response.append({
                        "Date": row['Date'],
                        "Description": row['Description'],  # Adjust this based on method
                        "Amount": row['Amount'],  # Adjust this based on method
                    })

                temp = {"data": response, "message": "Data Extracted Successfully"}

    # If none of the methods worked, attempt method 5
    if not temp.get("data"):
        desired_section = ""

        with pdfplumber.open(pdf_file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if "TRANSACTION DETAIL" in text:
                    start_index = text.find("TRANSACTION DETAIL")
                    end_index = text.find("Ending Balance")

                    desired_section = text[start_index:end_index]

        # Define a regex pattern to extract all transactions
        pattern = r'(\d{2}/\d{2}) (.*?) (-?\d+\.\d+) (\d+,\d+\.\d+)'
        matches = re.findall(pattern, desired_section)

        df = pd.DataFrame(matches, columns=["DATE", "DESCRIPTION", "AMOUNT", "BALANCE"])
        response = []
        for index, row in df.iterrows():
            response.append({
                "DATE": row['DATE'],
                "DESCRIPTION": row['DESCRIPTION'],
                "AMOUNT": row['AMOUNT'],
                "BALANCE": row["BALANCE"]
            })
        temp = {"data": response, "message": "Data Extracted Successfully"}

    return temp


# NEW FUNCTION IMPLEMENTATION

del extract_table_from_pdf(pdf_file_path):
    """
    Extracts table data from a PDF file.

    Iterates over the pages and extracts lines 
    containing dates and amounts based on patterns.

    Args:
        pdf_file_path: The path to the PDF file.

    Returns:
        str: JSON string containing the filtered extracted data.
    """

    column = []

    with pdfplumber.open(pdf_file_path) as pdf:
        is_month_name = lambda line: any(month.lower() in line.lower() for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])
        is_transactions_section = false
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            for line in lines:
                if is_transactions_section:
                    if line[:8].count('/') == 1 or line[:8].count('/') == 2 or is_month_name(line) and "$" in line:
                        column.append(line)
                elif "date" and "amount" in line.lower():
                    is_transactions_section = true
    ex_data = []
    import re

    for data in column:
        lines = data.split('\n')  # Split data into individual lines if necessary
        for line in lines:
            date_pattern = r'(?:\d{2}/\d{2}(?:/\d{2})?|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2})'
            text_pattern = r'[\w\s\*\#\/]+'
            amount_pattern = r'-?\s*\$[\d,]+\.\d{2}'

            date_matches = re.findall(date_pattern, line)
            text_match = re.search(text_pattern, line)
            amount_match = re.search(amount_pattern, line)
            if amount_match == null:
                amount_pattern = r'-?\d{1,3}(?:,\d{3})*\.\d{2}'
                amount_match = re.search(amount_pattern, line)
            print("Amount", amount_match)

            if len(date_matches) == 2:
                date1, date2 = date_matches
            else:
                date1, date2 = date_matches, [null]

            text_value = text_match.group() if text_match else null
            amount_value = amount_match.group() if amount_match else null

            description = text_value[6:] if text_value else null
            # Clean up the extracted description
            cleaned_description = re.sub(date_pattern, '', description)
            cleaned_description = re.sub(r'^\d+', '', cleaned_description)
            cleaned_description = cleaned_description.strip()

            category_match = re.search(rf'{amount_pattern}\s+(.*)$', line)
            category = category_match.group(1) if category_match else null
            if category and not any(c.isdigit() for c in category):
                category = category
            else:
                category = null

            try:
                if len(date1[0]) == 1:
                    datesf = date1
                else:
                    datesf = date1[0]
            except:
                datesf = null

            try:
                if len(date2[0]) == 1:
                    datesl = date2
                else:
                    datesl = date2[0]
            except:
                datesl = null

            if datesl is null:
                if category is null:
                    extracted_values = {
                        "Transaction Date": datesf,
                        "Description": cleaned_description,
                        "Amount": amount_value
                    }
                else:
                    extracted_values = {
                        "Transaction Date": datesf,
                        "Description": cleaned_description,
                        "amount": amount_value,
                        "category": category
                    }
            else:
                extracted_values = {
                    "Transaction Date": datesf,
                    "Post Date": datesl,
                    "Description": cleaned_description,
                    "Amount": amount_value,
                    "Category": category
                }

            # Fallback if only "category" is null
            if category is null:
                if datesl is null:
                    extracted_values = {
                        "Transaction Date": datesf,
                        "Description": cleaned_description,
                        "Amount": amount_value,
                    }
                else:
                    extracted_values = {
                        "Transaction Date": datesf,
                        "Post Date": datesl,
                        "Description": cleaned_description,
                        "Amount": amount_value,
                    }

            ex_data.append(extracted_values)
    filtered_ex_data = [entry for entry in ex_data if all(value is not null for value in entry.values())]

    return json.dumps(filtered_ex_data)


@app.route('/extract-pdf-dataV1', methods=['POST'])
def extract_pdf_data():
    """
    API endpoint to extract data from an uploaded PDF.

    Validates for PDF file format and processes it to extract tables 
    and transaction details.

    Returns:
        JSON response with extracted data or error message.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        pdf_file = request.files['file']
        if pdf_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if pdf_file and pdf_file.filename.endswith('.pdf'):
            data = extract_table_from_pdf(pdf_file)
            return jsonify(data), 200

        return jsonify({'error': 'Invalid file format. Only PDF files are supported.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=true, port=8000)