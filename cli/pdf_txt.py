import fitz
from openai import AzureOpenAI
import os
import base64
import json

import libs.config as config

from cli.blob import upload_file
from cli.common import load_project_env, load_graphrag_config, project_path
from cli.logger import get_logger

import concurrent.futures
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

logger = get_logger('pdf_txt')


def get_setting_file(file_path: str, default_prompt: str = ""):
    if not os.path.exists(file_path):
        return default_prompt

    with open(file_path, "r") as f:
        prompt = f.read()
        return prompt


def image_to_base64(image_path: str):
    with open(image_path, "rb") as image_file:
        base64_encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return base64_encoded

class PageTask:

    def __init__(self, doc, pdf_path, project_name, pdf_vision_option, page_num):
        self.doc = doc
        self.pdf_name = os.path.basename(pdf_path)
        self.project_name = project_name
        self.pdf_vision_option = pdf_vision_option
        self.pdf_vision_option_format = pdf_vision_option.replace(" ", "")
        self.base_name = f"{project_path(project_name)}/pdf_cache"
        self.img_path = f"{self.base_name}/{self.pdf_name}_page_{page_num + 1}.png"
        self.txt_path = f"{self.base_name}/{self.pdf_name}_page_{page_num + 1}.png.txt"
        self.cache_path = f"{self.base_name}/{self.pdf_name}_page_{page_num + 1}.cache.json"
        self.ai_txt_path = f"{self.base_name}/{self.pdf_name}_page_{page_num + 1}.png.{self.pdf_vision_option_format}.txt"
        self.page_num = page_num
        self.graphrag_config = load_graphrag_config(project_name)
        self.client = AzureOpenAI(
            api_version=self.graphrag_config.llm.api_version,
            azure_endpoint=self.graphrag_config.llm.api_base,
            azure_deployment=self.graphrag_config.llm.deployment_name,
            api_key=self.graphrag_config.llm.api_key,
        )

    def page_to_image(self):
        page = self.doc.load_page(self.page_num)
        pix = page.get_pixmap(dpi=150)
        pix.save(self.img_path)
        upload_file(self.project_name, self.img_path)

    def page_to_txt(self):
        page_txt = self.doc[self.page_num].get_text("text")
        # with open(self.txt_path, "w") as txt_file:
        #     txt_file.write(page_txt)
        #     st.write(f"[{self.page_num}/{self.doc.page_count}] {self.txt_path}")
        return page_txt

    def get_ai_txt(self):
        # use cache if exists
        if os.path.exists(self.ai_txt_path):
            with open(self.ai_txt_path, "r") as f:
                return "", f.read()

        self.page_to_image()

        prompt, ai_txt = "", ""

        try:
            if self.pdf_vision_option == config.generate_data_vision:
                prompt, ai_txt = self.gpt_vision_txt()

            if self.pdf_vision_option == config.generate_data_vision_txt:
                prompt, ai_txt = self.gpt_vision_txt_by_txt()

            if self.pdf_vision_option == config.generate_data_vision_image:
                prompt, ai_txt = self.gpt_vision_txt_by_image()

            if self.pdf_vision_option == config.generate_data_vision_azure:
                prompt, ai_txt = self.gpt_vision_txt_azure()

            if self.pdf_vision_option == config.generate_data_vision_di:
                ai_txt = di_analyze_read(self.img_path, self.project_name)

            # set cache
            with open(self.ai_txt_path, "w") as txt_file:
                txt_file.write(ai_txt)
                logger.info(f"[{self.page_num}/{self.doc.page_count}] {self.ai_txt_path}")
        except Exception as e:
            logger.warning(
                f"[{self.page_num}/{self.doc.page_count}] `{self.pdf_name}` generated an exception: {e}"
            )

        return prompt, ai_txt

    def gpt_vision_txt_azure(self):
        base64_string = image_to_base64(self.img_path)

        prompt = config.pdf_gpt_vision_prompt_azure.format(page_txt=self.page_to_txt())

        completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_string}",
                            },
                        },
                    ],
                }
            ],
            model=self.graphrag_config.llm.model,
        )
        ai_txt = completion.choices[0].message.content
        self.write_cache(completion.to_json())
        return prompt, ai_txt

    def gpt_vision_txt(self):
        base64_string = image_to_base64(self.img_path)
        settings_file = (
            f"{project_path(self.project_name)}/prompts/pdf_gpt_vision_prompt.txt"
        )
        prompt = get_setting_file(settings_file, config.pdf_gpt_vision_prompt).format(
            page_txt=self.page_to_txt()
        )

        completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_string}",
                            },
                        },
                    ],
                }
            ],
            model=self.graphrag_config.llm.model,
        )
        ai_txt = completion.choices[0].message.content
        self.write_cache(completion.to_json())
        return prompt, ai_txt

    def write_cache(self, data):
        with open(self.cache_path, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)


    def gpt_vision_txt_by_txt(self):
        base64_string = image_to_base64(self.img_path)
        settings_file = f"{project_path(self.project_name)}/prompts/pdf_gpt_vision_prompt_by_text.txt"
        prompt = get_setting_file(
            settings_file, config.pdf_gpt_vision_prompt_by_text
        ).format(page_txt=self.page_to_txt())

        completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_string}",
                            },
                        },
                    ],
                }
            ],
            model=self.graphrag_config.llm.model,
        )
        ai_txt = completion.choices[0].message.content
        self.write_cache(completion.to_json())
        return prompt, ai_txt

    def gpt_vision_txt_by_image(self):
        base64_string = image_to_base64(self.img_path)

        settings_file = f"{project_path(self.project_name)}/prompts/pdf_gpt_vision_prompt_by_image.txt"
        prompt = get_setting_file(
            settings_file, config.pdf_gpt_vision_prompt_by_image
        ).format(page_txt=self.page_to_txt())

        completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_string}",
                            },
                        },
                    ],
                }
            ],
            model=self.graphrag_config.llm.model,
        )
        ai_txt = completion.choices[0].message.content
        self.write_cache(completion.to_json())
        return prompt, ai_txt


def save_pdf_pages_as_images(pdf_path: str, project_name: str, pdf_vision_option: str):
    pdf_file_name = os.path.basename(pdf_path)
    pdf_ai_txt_path = f"{pdf_path}.{pdf_vision_option.replace(" ", "")}.txt"
    base_dir = f"{project_path(project_name)}/pdf_cache"
    os.makedirs(base_dir, exist_ok=True)

    doc = fitz.open(pdf_path)

    upload_file(project_name, pdf_path)

    def process_page(page_num):
        pt = PageTask(doc, pdf_path, project_name, pdf_vision_option, page_num)
        return pt.get_ai_txt()

    # get txt by parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_page = {
            executor.submit(process_page, page_num): page_num
            for page_num in range(doc.page_count)
        }
        for future in concurrent.futures.as_completed(future_to_page):
            page_num = future_to_page[future]
            try:
                future.result()
                logger.info(f"[{page_num}/{doc.page_count}] `{pdf_file_name}` done")
            except Exception as exc:
                logger.warning(
                    f"[{page_num}/{doc.page_count}] `{pdf_file_name}` generated an exception: {exc}"
                )

    # write full txt by order
    with open(pdf_ai_txt_path, "w") as f:
        f.write("\n")

    for page_num in range(doc.page_count):
        pt = PageTask(doc, pdf_path, project_name, pdf_vision_option, page_num)
        with open(pdf_ai_txt_path, "a") as f:
            f.write("\n\n")
            prompt, ai_txt = pt.get_ai_txt()
            if ai_txt:
                f.write(ai_txt)


def format_bounding_box(bounding_box):
    if not bounding_box:
        return "N/A"
    return ", ".join(["[{}, {}]".format(p.x, p.y) for p in bounding_box])


def di_analyze_read(img_path: str, project_name: str):
    load_project_env(project_name)
    endpoint = os.getenv("DOCUMENT_INTELLIGENCE_URL", "")
    key = os.getenv("DOCUMENT_INTELLIGENCE_KEY", "")

    if not endpoint or not key:
        logger.error(
            "Your need to set DOCUMENT_INTELLIGENCE_URL and DOCUMENT_INTELLIGENCE_KEY in .env file."
        )
        return ""

    # open the file
    with open(img_path, "rb") as file:
        file_data = file.read()

        # print(file_data)

        document_analysis_client = DocumentAnalysisClient(
            endpoint=endpoint, credential=AzureKeyCredential(key)
        )

        poller = document_analysis_client.begin_analyze_document(
            "prebuilt-read", document=file_data
        )
        result = poller.result()

        for idx, style in enumerate(result.styles):
            print(
                "Document contains {} content".format(
                    "handwritten" if style.is_handwritten else "no handwritten"
                )
            )

        for page in result.pages:
            print("----Analyzing Read from page #{}----".format(page.page_number))
            print(
                "Page has width: {} and height: {}, measured with unit: {}".format(
                    page.width, page.height, page.unit
                )
            )

            for line_idx, line in enumerate(page.lines):
                print(
                    "...Line # {} has text content '{}' within bounding box '{}'".format(
                        line_idx,
                        line.content,
                        format_bounding_box(line.polygon),
                    )
                )

            for word in page.words:
                print(
                    "...Word '{}' has a confidence of {}".format(
                        word.content, word.confidence
                    )
                )

        print("====================================")
        return result.content
