import time
import requests

import pandas as pd
import os
import re
import zipfile
from cli.common import run_command, project_path
from theodoretools.url import url_to_name
import cli.pdf_txt as pdf_txt

from cli.logger import get_logger

logger = get_logger('generate_data_cli')


def generate_data(project_name, pdf_vision_option):
    logger.info(f"generate data for project: {project_name}")

    project_dir = project_path(project_name)

    # 1. clear input directory
    run_command(f"rm -rf {project_dir}/input/*")

    # 2. clear pdf_cache directory
    run_command(f"rm -rf {project_dir}/pdf_cache/*")

    # 3. copy original files to input
    for root, dirs, files in os.walk(
        f"{project_dir}/original"
    ):
        for file in files:
            file_path = os.path.join(root, file)
            prepare_file(file_path, file, project_name)

    # 4. convert files to txt
    for root, dirs, files in os.walk(f"{project_dir}/input"):
        for file in files:
            file_path = os.path.join(root, file)
            convert_file(file_path, file,
                     project_name, pdf_vision_option)

    #  5. make file permissions to another user can write
    for root, dirs, files in os.walk(f"{project_dir}/input"):
        for file in files:
            file_path = os.path.join(root, file)
            os.chmod(file_path, 0o666)

def create_zip(directory, output_path):
    with zipfile.ZipFile(output_path, "w") as zipf:
        for foldername, subfolders, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(".txt"):
                    filepath = os.path.join(foldername, filename)
                    zipf.write(filepath, os.path.relpath(filepath, directory))



def convert_file(file_path, file, project_name, pdf_vision_option):

    if file.endswith(".xlsx") or file.endswith(".csv"):
        logger.info(f"converting `{file}`")
        excel_to_txt(file_path, project_name)

    if file.endswith(".pdf"):
        logger.info(f"converting `{file}`")
        pdf_txt.save_pdf_pages_as_images(
            file_path, project_name, pdf_vision_option)


def excel_to_txt(file_path, project_name):
    file_name = os.path.basename(file_path)

    if file_path.endswith(".xlsx"):
        excel_data = pd.ExcelFile(file_path, engine='openpyxl')
        with open(
            f"{project_path(project_name)}/input/{file_name}.txt", "w", encoding="utf-8"
        ) as f:
            for sheet_name in excel_data.sheet_names:
                f.write(f"{sheet_name}\n\n")
                df = excel_data.parse(sheet_name)
                for index, row in df.iterrows():
                    for column in df.columns:
                        if pd.notna(row[column]):
                            f.write(f"【{column}】: {row[column]} ")
                    f.write(f"\n\n")
    elif file_path.endswith(".csv"):

        df = pd.read_csv(file_path, encoding='utf-8')
        with open(
            f"{project_path(project_name)}/input/{file_name}.txt", "w", encoding="utf-8"
        ) as f:
            for column in df.columns:
                f.write(f"{column}\n\n")
            for index, row in df.iterrows():
                for column in df.columns:
                    if pd.notna(row[column]):
                        f.write(f"【{column}】: {row[column]} ")
                f.write(f"\n\n")
    else:

        try:
            excel_data = pd.ExcelFile(file_path, engine='openpyxl')
            with open(
                f"{project_path(project_name)}/input/{file_name}.txt", "w", encoding="utf-8"
            ) as f:
                for sheet_name in excel_data.sheet_names:
                    f.write(f"{sheet_name}\n\n")
                    df = excel_data.parse(sheet_name)
                    for index, row in df.iterrows():
                        for column in df.columns:
                            if pd.notna(row[column]):
                                f.write(f"【{column}】: {row[column]} ")
                        f.write(f"\n\n")
        except Exception as e:
            logger.error(f"无法处理文件 {file_name}: {str(e)}")


def prepare_file(file_path, file, project_name):
    if file.endswith(".xlsx") or file.endswith(".csv"):
        if has_download_files(file_path):
            download_files_from_xlsx_csv(file_path, file, project_name)
        else:
            run_command(
                f"cp -r '{file_path}' {project_path(project_name)}/input/")
            logger.info(f"copied {file} to input")
    if file.endswith(".txt"):
        run_command(f"cp -r '{file_path}' {project_path(project_name)}/input/")
        logger.info(f"copied {file} to input")

    if file.endswith(".md"):
        run_command(
            f"cp -r '{file_path}' {project_path(project_name)}/input/{file}.txt"
        )
        logger.info(f"converted {file} to {file}.txt")

    if file.endswith(".pdf"):
        run_command(f"cp -r '{file_path}' {project_path(project_name)}/input/")

    # if file.endswith('.zip'):
    #     deal_zip(file_path, project_name)


def has_download_files(file_path: str):
    if not file_path.endswith(".xlsx") and not file_path.endswith(".csv"):
        return False


    if file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path, engine='openpyxl')
    elif file_path.endswith(".csv"):

        df = pd.read_csv(file_path, encoding='utf-8')
    else:

        df = pd.read_excel(file_path, engine='openpyxl')
    

    if 'doc_url' in df.columns:
        return True
    

    for index, row in df.iterrows():
        if "doc_url" in row:
            return True
    
    return False


def download_files_from_xlsx_csv(file_path, file, project_name):
    if not file_path.endswith(".xlsx") and not file_path.endswith(".csv"):
        return

 
    if file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path, engine='openpyxl')
    elif file_path.endswith(".csv"):
  
        df = pd.read_csv(file_path, encoding='utf-8')
    else:

        df = pd.read_excel(file_path, engine='openpyxl')
    
    logger.info(df)
    df_count = len(df) - 1
    for index, row in df.iterrows():
        if "doc_url" in row:
            doc_url = row["doc_url"]
            download_file(doc_url, index, df_count, project_name)


def download_file(doc_url, index, df_count, project_name):
    file_name = url_to_name(doc_url)
    os.makedirs(f"{project_path(project_name)}/input", exist_ok=True)
    file_path = os.path.join(f"{project_path(project_name)}/input", file_name)

    if os.path.exists(file_path):
        logger.info(f"[{index}/{df_count}] File already exists: {file_path}")
        return

    logger.info(f"[{index}/{df_count}] Downloading {doc_url}")

    try:
        response = requests.get(doc_url, stream=True)
        response.raise_for_status()

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logger.info(f"[{index}/{df_count}] Downloaded: {file_path}")
    except requests.RequestException as e:
        logger.info(f"[{index}/{df_count}] Downloaded Error: {e}")


def replace_image_tag(match):
    image_path = match.group(1)
    file_path = f"{image_path}.desc"

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            content = file.read()
            return f"此处是文本插图：{content}"

    return match.group(1)


def replace_classify(markdown_text: str):
    markdown_pattern = r"!\[.*?\]\((.*?)\)"
    html_pattern = r'<img .*?src="(.*?)".*?>'
    markdown_text = re.sub(markdown_pattern, replace_image_tag, markdown_text)
    markdown_text = re.sub(html_pattern, replace_image_tag, markdown_text)
    return markdown_text


def download_image(image_url, output_dir, image_index):
    image_extension = image_url.split(".")[-1].split("?")[0]

    image_extension = image_extension.replace(",", "")
    image_extension = image_extension.replace("&", "")
    image_extension = image_extension.replace("=", "")
    image_extension = image_extension.replace(".", "")

    image_filename = f"image_{image_index}.{image_extension}"
    image_path = os.path.join(output_dir, image_filename)

    try:
        response = requests.get(image_url)
        response.raise_for_status()
        with open(image_path, "wb") as image_file:
            image_file.write(response.content)
        return image_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {image_url}: {e}")
        return None


def read_pdf(file_path):
    import PyPDF2

    text = ""
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text
