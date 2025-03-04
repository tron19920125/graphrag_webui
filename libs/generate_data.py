import time
import requests

import pandas as pd
import streamlit as st
import os
import re
import zipfile
from libs import config
from libs.common import run_command
from libs.config import (
    generate_data_vision,
    generate_data_vision_txt,
    generate_data_vision_image,
    generate_data_vision_di,
    generate_data_vision_azure,
)
from theodoretools.url import url_to_name
import libs.pdf_txt as pdf_txt
from theodoretools.fs import get_directory_size

from libs.save_settings import input_files


def create_zip(directory, output_path):
    with zipfile.ZipFile(output_path, "w") as zipf:
        for foldername, subfolders, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(".txt"):
                    filepath = os.path.join(foldername, filename)
                    zipf.write(filepath, os.path.relpath(filepath, directory))


def generate_data(project_name: str):
    st.markdown(f"### Attention")
    st.markdown(f"- Do not process `txt` files")
    st.markdown(f"- `pdf` will be converted to `txt`")
    st.markdown(f"- `xlsx/csv` will be converted to `txt`")
    st.markdown(f"- `md` will be converted to `txt`")
    st.markdown(
        f"- If `xlsx/csv` contains a `doc_url` column, the relevant files will be automatically downloaded, and `xlsx/csv` itself will be excluded"
    )

    st.markdown(f"--------------")
    options = [
        generate_data_vision,
        generate_data_vision_txt,
        generate_data_vision_image,
        generate_data_vision_di,
        generate_data_vision_azure,
    ]
    pdf_vision_option = st.radio(
        "Please select a method to process the PDF:",
        key=f"db_{project_name}",
        options=options,
    )

    if st.button("Start Generate", key=f"generate_btn_{project_name}", icon="🚀"):
        with st.container(
            border=True, key=f"generate_container_{project_name}", height=400
        ):
            with st.spinner(f"Processing ..."):

                # 1. copy original files to input
                for root, dirs, files in os.walk(
                    f"/app/projects/{project_name}/original"
                ):
                    for file in files:
                        file_path = os.path.join(root, file)
                        prepare_file(file_path, file, project_name)

                # 2. convert files to txt
                for root, dirs, files in os.walk(f"/app/projects/{project_name}/input"):
                    for file in files:
                        file_path = os.path.join(root, file)
                        convert_file(file_path, file,
                                     project_name, pdf_vision_option)

                #  3. make file permissions to another user can write
                for root, dirs, files in os.walk(f"/app/projects/{project_name}/input"):
                    for file in files:
                        file_path = os.path.join(root, file)
                        os.chmod(file_path, 0o666)

                st.success("Data generated successfully.")

    input_cache_size_mb = get_directory_size(
        f"/app/projects/{project_name}/input")
    if st.button(
        f"Download generated files",
        key=f"downloads_input_files_{project_name}",
        icon="💾",
    ):
        directory_to_zip = f"/app/projects/{project_name}/input"
        output_zip_path = f"/tmp/{project_name}.zip"
        create_zip(directory_to_zip, output_zip_path)
        with open(output_zip_path, "rb") as f:
            st.download_button(
                label="Download",
                data=f,
                file_name=f"{project_name}.zip",
                mime="application/zip",
            )
    if input_cache_size_mb > 0:
        if st.button(
            f"Clear generated files ({input_cache_size_mb} MB)",
            key=f"delete_all_input_files_{project_name}",
            icon="🗑️",
        ):
            run_command(f"rm -rf /app/projects/{project_name}/input/*")
            time.sleep(3)
            st.success("All files deleted.")

    pdf_cache_size_mb = get_directory_size(
        f"/app/projects/{project_name}/pdf_cache")
    if pdf_cache_size_mb > 0:
        if st.button(
            f"Clear PDF cached files ({pdf_cache_size_mb} MB)",
            key=f"delete_all_cached_files_{project_name}",
            icon="🗑️",
        ):
            run_command(f"rm -rf /app/projects/{project_name}/pdf_cache/*")
            time.sleep(3)
            st.success("All files deleted.")

    st.markdown(f"--------------")
    input_files(project_name)


def convert_file(file_path, file, project_name, pdf_vision_option):

    if file.endswith(".xlsx") or file.endswith(".csv"):
        st.write(f"converting `{file}`")
        excel_to_txt(file_path, project_name)

    if file.endswith(".pdf"):
        st.write(f"converting `{file}`")
        pdf_txt.save_pdf_pages_as_images(
            file_path, project_name, pdf_vision_option)


def excel_to_txt(file_path, project_name):
    file_name = os.path.basename(file_path)
    # 根据文件扩展名选择适当的引擎
    if file_path.endswith(".xlsx"):
        excel_data = pd.ExcelFile(file_path, engine='openpyxl')
        with open(
            f"/app/projects/{project_name}/input/{file_name}.txt", "w", encoding="utf-8"
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
        # 对于CSV文件，直接读取为DataFrame
        df = pd.read_csv(file_path, encoding='utf-8')
        with open(
            f"/app/projects/{project_name}/input/{file_name}.txt", "w", encoding="utf-8"
        ) as f:
            for column in df.columns:
                f.write(f"{column}\n\n")
            for index, row in df.iterrows():
                for column in df.columns:
                    if pd.notna(row[column]):
                        f.write(f"【{column}】: {row[column]} ")
                f.write(f"\n\n")
    else:
        # 如果是其他格式，尝试使用openpyxl
        try:
            excel_data = pd.ExcelFile(file_path, engine='openpyxl')
            with open(
                f"/app/projects/{project_name}/input/{file_name}.txt", "w", encoding="utf-8"
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
            st.error(f"无法处理文件 {file_name}: {str(e)}")


def prepare_file(file_path, file, project_name):
    if file.endswith(".xlsx") or file.endswith(".csv"):
        if has_download_files(file_path):
            download_files_from_xlsx_csv(file_path, file, project_name)
        else:
            run_command(
                f"cp -r '{file_path}' /app/projects/{project_name}/input/")
            st.write(f"copied {file} to input")
    if file.endswith(".txt"):
        run_command(f"cp -r '{file_path}' /app/projects/{project_name}/input/")
        st.write(f"copied {file} to input")

    if file.endswith(".md"):
        run_command(
            f"cp -r '{file_path}' /app/projects/{project_name}/input/{file}.txt"
        )
        st.write(f"converted {file} to {file}.txt")

    if file.endswith(".pdf"):
        run_command(f"cp -r '{file_path}' /app/projects/{project_name}/input/")

    # if file.endswith('.zip'):
    #     deal_zip(file_path, project_name)


def has_download_files(file_path: str):
    if not file_path.endswith(".xlsx") and not file_path.endswith(".csv"):
        return False

    # 根据文件扩展名选择适当的引擎
    if file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path, engine='openpyxl')
    elif file_path.endswith(".csv"):
        # 对于CSV文件，应该使用pd.read_csv而不是pd.read_excel
        df = pd.read_csv(file_path, encoding='utf-8')
    else:
        # 如果无法确定，尝试使用openpyxl
        df = pd.read_excel(file_path, engine='openpyxl')
    
    # 检查是否有doc_url列
    if 'doc_url' in df.columns:
        return True
    
    # 检查每一行是否有doc_url键
    for index, row in df.iterrows():
        if "doc_url" in row:
            return True
    
    return False


def download_files_from_xlsx_csv(file_path, file, project_name):
    if not file_path.endswith(".xlsx") and not file_path.endswith(".csv"):
        return

    # 根据文件扩展名选择适当的引擎
    if file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path, engine='openpyxl')
    elif file_path.endswith(".csv"):
        # 对于CSV文件，使用pd.read_csv
        df = pd.read_csv(file_path, encoding='utf-8')
    else:
        # 如果无法确定，尝试使用openpyxl
        df = pd.read_excel(file_path, engine='openpyxl')
    
    st.write(df)
    df_count = len(df) - 1
    with st.spinner(f"Processing ..."):
        for index, row in df.iterrows():
            if "doc_url" in row:
                doc_url = row["doc_url"]
                download_file(doc_url, index, df_count, project_name)


def download_file(doc_url, index, df_count, project_name):
    file_name = url_to_name(doc_url)
    os.makedirs(f"/app/projects/{project_name}/input", exist_ok=True)
    file_path = os.path.join(f"/app/projects/{project_name}/input", file_name)

    if os.path.exists(file_path):
        st.write(f"[{index}/{df_count}] File already exists: {file_path}")
        return

    st.write(f"[{index}/{df_count}] Downloading {doc_url}")

    try:
        response = requests.get(doc_url, stream=True)
        response.raise_for_status()

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        st.write(f"[{index}/{df_count}] Downloaded: {file_path}")
    except requests.RequestException as e:
        st.write(f"[{index}/{df_count}] Downloaded Error: {e}")


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
