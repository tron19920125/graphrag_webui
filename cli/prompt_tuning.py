
from cli.common import project_path
import graphrag.api as api
from graphrag.config.load_config import load_config
from pathlib import Path
import asyncio
import re

from cli.logger import get_logger

logger = get_logger('prompt_tuning_cli')

async def prompt_tuning(project_name: str):
    base_path = f"{project_path(project_name)}"
    
    logger.info("This operation will overwrite your following files, please proceed with caution: \n\n - prompts/entity_extraction.txt \n\n - prompts/summarize_descriptions.txt \n\n - prompts/community_report.txt")
    
    logger.info(f'Start Tuning {project_name}')
    
    # Generate prompts
    (
        entity_extraction_prompt,
        entity_summarization_prompt,
        community_summarization_prompt,
    ) = await api.generate_indexing_prompts(
            config=load_config(root_dir=Path(base_path)),
            root=base_path)
    
    # Define file paths
    entity_extraction_prompt_path = f"{base_path}/prompts/entity_extraction.txt"
    entity_summarization_prompt_path = f"{base_path}/prompts/summarize_descriptions.txt" 
    community_summarization_prompt_path = f"{base_path}/prompts/community_report.txt"

    # fix wrong prompt
    entity_extraction_prompt = fix_wrong_prompt(entity_extraction_prompt)

    # Write files concurrently
    await asyncio.gather(
        write_prompt_file(entity_extraction_prompt_path, entity_extraction_prompt),
        write_prompt_file(entity_summarization_prompt_path, entity_summarization_prompt),
        write_prompt_file(community_summarization_prompt_path, community_summarization_prompt)
    )
    
    return True # Add return value to avoid coroutine warning



async def write_prompt_file(path: str, content: str):
    """Write prompt content to file asynchronously"""
    with open(path, "wb") as file:
        file.write(content.encode(encoding="utf-8", errors="strict"))
    return True


def sanitize_line(line: str):
    if line.strip() == '':
        return ''
    if line.strip().startswith('(') and not line.strip().endswith(')'):
        # 替换最后一个字符
        line = line.strip()[:-1] + ')'
    return line.strip()
  
def replace_func(match: re.Match):
    group = match.group(1)
    results = []
    lines = group.split('\n')
    results = []
    for line in lines:
        results.append(sanitize_line(line))
    result = "\n".join(results)
    return f"output: {result}#############################" 

def fix_wrong_prompt(content: str):
    """fix wrong prompt"""
    # 正则匹配 output 和 #### 之间的内容, 支持多行, 可能出现多个output, 保持其余内容不变
    pattern = r".*output:([\s\S]*?)#############################"
    result = re.sub(pattern, replace_func, content)
    return result