import os
import re
import streamlit as st
from collections import defaultdict

from libs.blob import get_sas_url
from typing import Dict, Set
from libs.config import settings

#pattern = re.compile(r'\[\^Data:(\w+?)\((\d+(?:,\d+)*)\)\]')

pattern = re.compile(r'\[Data: (\w+?) \(([\d, ]+)\)(?:; (\w+?) \(([\d, ]+)\))?\]')

def parse_file_info(input_string: str):
    match = re.match(r"(.*?\.pdf)_page_(\d+)\.png", input_string)
    if match:
        base_pdf = match.group(1)
        page_number = int(match.group(2))
        screenshot_file = f"{base_pdf}_page_{page_number}.png"
        return base_pdf, screenshot_file, page_number
    else:
        raise ValueError("输入字符串格式不正确，无法解析！")


def get_query_sources(project_name: str, context_data: any):
    
    sources = []
    
    txt_files_path = f"/app/projects/{project_name}/pdf_cache"
    if not os.path.exists(txt_files_path):
        return sources
    
    if not context_data['sources']:
        return sources
    
    if len(context_data['sources']) == 0:
        return sources
    
    source_cache = {}
    screenshot_sas_url_cache = {}
    
    for source in context_data['sources']:
        if source['text'] in source_cache:
            continue
        
        for txt_file in os.listdir(txt_files_path):
            try:
                file_path = os.path.join(txt_files_path, txt_file)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if source['text'] in content:
                        pdf_file, screenshot_file, page_number = parse_file_info(txt_file)
                        if screenshot_file in screenshot_sas_url_cache:
                            continue
                        pdf_sas_url, pdf_sas_url_error = get_sas_url(project_name, pdf_file)
                        screenshot_sas_url, screenshot_sas_url_error = get_sas_url(project_name, screenshot_file)
                        sources.append({
                            "pdf_file": pdf_file,
                            "screenshot_file": screenshot_file,
                            "page_number": page_number,
                            "pdf_sas_url": pdf_sas_url,
                            "pdf_sas_url_error": pdf_sas_url_error,
                            "screenshot_sas_url": screenshot_sas_url,
                            "screenshot_sas_url_error": screenshot_sas_url_error
                        })
                        screenshot_sas_url_cache[screenshot_file] = screenshot_sas_url
            except Exception as e:
                st.error(f"Error parsing file info: {e}")
                
        source_cache[source['text']] = True
                
    return sources

def get_reference(text: str) -> dict:
    data_dict = defaultdict(set)
    for match in pattern.finditer(text):
        key = match.group(1).lower()
        value = match.group(2)

        ids = value.replace(" ", "").split(',')
        data_dict[key].update(ids)

    return dict(data_dict)


def generate_ref_links(data: Dict[str, Set[int]], index_id: str) -> str:
    base_url = f"{settings.website_address}/v1/references"
    lines = []
    lines.append("## Sources \n")
    source_no = 1
    for key, values in data.items():
        for value in values:
            lines.append(f'[Data:{key.capitalize()}({value})]: [{key.capitalize()}: {value}]({base_url}/{index_id}/{key}/{value})')
            # lines.append(f'* [Source {source_no}]({base_url}/{index_id}/{key}/{value})')
            source_no += 1
    return "\n".join(lines)