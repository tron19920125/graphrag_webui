#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import sys
import time
import glob
from collections import defaultdict
from datetime import datetime

def analyze_tokens():
    """分析cache文件夹下所有文件的token消耗情况"""
    # 定义cache文件夹路径
    cache_dir = "/mnt/efs/graphrag_webui/projects/admin_2025030422/cache"
    
    # 存储各部分token消耗的字典
    token_stats = defaultdict(lambda: defaultdict(int))
    model_token_stats = defaultdict(lambda: defaultdict(int))
    file_token_stats = {}
    
    # 遍历cache文件夹下的所有子文件夹
    for subdir in os.listdir(cache_dir):
        subdir_path = os.path.join(cache_dir, subdir)
        if os.path.isdir(subdir_path):
            print(f"处理 {subdir} 文件夹...")
            # 确保输出被刷新
            sys.stdout.flush()
            
            # 遍历子文件夹中的所有文件
            for filename in os.listdir(subdir_path):
                file_path = os.path.join(subdir_path, filename)
                
                # 获取文件的修改时间
                file_mtime = os.path.getmtime(file_path)
                file_mtime_str = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                # 根据文件名确定文件类型
                file_type = get_file_type(filename, subdir)
                
                try:
                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 解析JSON内容
                    try:
                        data = json.loads(content)
                        
                        # 提取token使用情况
                        if "usage" in data.get("result", {}):
                            usage = data["result"]["usage"]
                            
                            # 提取模型名称
                            model_name = "unknown"
                            if "model" in data.get("result", {}):
                                model_name = data["result"]["model"]
                            
                            # 更新token统计信息
                            completion_tokens = usage.get("completion_tokens", 0)
                            prompt_tokens = usage.get("prompt_tokens", 0)
                            total_tokens = usage.get("total_tokens", 0)
                            
                            token_stats[file_type]["completion_tokens"] += completion_tokens
                            token_stats[file_type]["prompt_tokens"] += prompt_tokens
                            token_stats[file_type]["total_tokens"] += total_tokens
                            
                            # 更新模型统计信息
                            model_token_stats[model_name]["completion_tokens"] += completion_tokens
                            model_token_stats[model_name]["prompt_tokens"] += prompt_tokens
                            model_token_stats[model_name]["total_tokens"] += total_tokens
                            
                            # 保存单个文件的token信息，包含时间信息
                            file_token_stats[file_path] = {
                                "type": file_type,
                                "model": model_name,
                                "completion_tokens": completion_tokens,
                                "prompt_tokens": prompt_tokens,
                                "total_tokens": total_tokens,
                                "mtime": file_mtime,
                                "mtime_str": file_mtime_str
                            }
                            
                            # 尝试通过内容匹配确定文件的具体用途
                            content_type = get_content_type(data)
                            if content_type:
                                token_stats[f"{file_type}_{content_type}"]["completion_tokens"] += usage.get("completion_tokens", 0)
                                token_stats[f"{file_type}_{content_type}"]["prompt_tokens"] += usage.get("prompt_tokens", 0)
                                token_stats[f"{file_type}_{content_type}"]["total_tokens"] += usage.get("total_tokens", 0)
                                
                                # 更新文件的内容类型
                                file_token_stats[file_path]["content_type"] = content_type
                        else:
                            print(f"警告: 文件 {file_path} 中未找到token使用信息")
                    except json.JSONDecodeError:
                        print(f"警告: 文件 {file_path} 不是有效的JSON格式")
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {str(e)}")
    
    # 打印token统计结果
    print("\n===== Token消耗统计 =====")
    print("\n按文件类型统计:")
    
    # 计算每种主要类型的token使用情况
    main_type_stats = defaultdict(lambda: defaultdict(int))
    for file_path, stats in file_token_stats.items():
        file_type = stats["type"]
        main_type_stats[file_type]["completion_tokens"] += stats["completion_tokens"]
        main_type_stats[file_type]["prompt_tokens"] += stats["prompt_tokens"]
        main_type_stats[file_type]["total_tokens"] += stats["total_tokens"]
    
    # 打印主要类型的统计信息
    total_all = 0
    for file_type, usage in sorted(main_type_stats.items()):
        total = usage["total_tokens"]
        total_all += total
        print(f"{file_type}:")
        print(f"  完成 tokens: {usage['completion_tokens']}")
        print(f"  提示 tokens: {usage['prompt_tokens']}")
        print(f"  总计 tokens: {total}")
    
    print(f"\n所有类型总计: {total_all} tokens")
    
    print("\n按内容类型的详细统计:")
    for file_type, usage in sorted(token_stats.items()):
        if "_" in file_type:  # 只打印内容子类型
            print(f"{file_type}:")
            print(f"  完成 tokens: {usage['completion_tokens']}")
            print(f"  提示 tokens: {usage['prompt_tokens']}")
            print(f"  总计 tokens: {usage['total_tokens']}")
    
    # 打印按模型分类的统计信息
    print("\n===== 按模型分类的Token消耗统计 =====")
    for model_name, usage in sorted(model_token_stats.items()):
        print(f"{model_name}:")
        print(f"  完成 tokens: {usage['completion_tokens']}")
        print(f"  提示 tokens: {usage['prompt_tokens']}")
        print(f"  总计 tokens: {usage['total_tokens']}")
    
    # 打印文件数量统计
    print(f"\n总文件数: {len(file_token_stats)} 个文件")

def get_file_type(filename, subdir):
    """根据文件名和子文件夹确定文件类型"""
    if subdir == "community_reporting":
        return "community_report"
    elif subdir == "entity_extraction":
        if "extract-continuation" in filename:
            return "entity_extraction_continuation"
        else:
            return "entity_extraction"
    elif subdir == "summarize_descriptions":
        return "summarize"
    elif subdir == "text_embedding":
        return "embedding"
    else:
        return "unknown"

def get_content_type(data):
    """尝试通过内容匹配确定文件的具体用途"""
    # 检查输入消息
    if "input" in data and "messages" in data["input"]:
        for message in data["input"]["messages"]:
            content = message.get("content", "")
            
            # 检查内容中的关键词
            if isinstance(content, str):
                if "community analyst" in content.lower():
                    return "community_analysis"
                elif "entity extraction" in content.lower():
                    return "entity_extraction"
                elif "summarize" in content.lower():
                    return "summarization"
                elif "embedding" in content.lower():
                    return "embedding"
    
    # 检查输出内容
    if "result" in data and "choices" in data["result"]:
        for choice in data["result"]["choices"]:
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
                
                if isinstance(content, str):
                    if "community" in content.lower() and "report" in content.lower():
                        return "community_analysis"
                    elif "entity" in content.lower() and "extraction" in content.lower():
                        return "entity_extraction"
                    elif "summary" in content.lower() or "summarize" in content.lower():
                        return "summarization"
    
    return None

def analyze_pdf_cache_tokens():
    """分析projects/admin_2025030422/pdf_cache目录下所有JSON文件的token消耗情况"""
    # 定义pdf_cache文件夹路径
    pdf_cache_dir = "/mnt/efs/graphrag_webui/projects/admin_2025030422/pdf_cache"
    
    # 检查目录是否存在
    if not os.path.exists(pdf_cache_dir):
        print(f"错误: 目录 {pdf_cache_dir} 不存在")
        return
    
    # 存储token消耗的字典
    token_stats = defaultdict(int)
    model_token_stats = defaultdict(lambda: defaultdict(int))
    file_token_stats = {}
    
    # 获取所有JSON文件
    json_files = glob.glob(os.path.join(pdf_cache_dir, "*.cache.json"))
    
    if not json_files:
        print(f"警告: 在 {pdf_cache_dir} 中未找到JSON文件")
        return
    
    print(f"正在处理 {pdf_cache_dir} 目录中的 {len(json_files)} 个JSON文件...")
    
    # 遍历所有JSON文件
    for file_path in json_files:
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析JSON内容
            try:
                data = json.loads(content)
                data = json.loads(data)
                # data1 = data['choices']
                # print(data1)
                
                # 提取token使用情况 - 检查不同的可能位置
                usage = None
                if "usage" in data:
                    usage = data["usage"]
                
                # 提取模型名称
                model_name = "unknown"
                if "model" in data:
                    model_name = data["model"]
                
                if usage:
                    # 更新token统计信息
                    completion_tokens = usage.get("completion_tokens", 0)
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)
                    
                    token_stats["completion_tokens"] += completion_tokens
                    token_stats["prompt_tokens"] += prompt_tokens
                    token_stats["total_tokens"] += total_tokens
                    
                    # 更新模型统计信息
                    model_token_stats[model_name]["completion_tokens"] += completion_tokens
                    model_token_stats[model_name]["prompt_tokens"] += prompt_tokens
                    model_token_stats[model_name]["total_tokens"] += total_tokens
                    
                    # 保存单个文件的token信息
                    file_token_stats[file_path] = {
                        "model": model_name,
                        "completion_tokens": completion_tokens,
                        "prompt_tokens": prompt_tokens,
                        "total_tokens": total_tokens
                    }
                else:
                    print(f"警告: 文件 {file_path} 中未找到token使用信息")
            except json.JSONDecodeError:
                print(f"警告: 文件 {file_path} 不是有效的JSON格式")
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {str(e)}")
    
    # 打印token统计结果
    print("\n===== PDF Cache Token消耗统计 =====")
    print(f"完成 tokens: {token_stats['completion_tokens']}")
    print(f"提示 tokens: {token_stats['prompt_tokens']}")
    print(f"总计 tokens: {token_stats['total_tokens']}")
    print(f"总文件数: {len(file_token_stats)} 个文件")
    
    # 打印按模型分类的统计信息
    print("\n===== PDF Cache 按模型分类的Token消耗统计 =====")
    for model_name, usage in sorted(model_token_stats.items()):
        print(f"{model_name}:")
        print(f"  完成 tokens: {usage['completion_tokens']}")
        print(f"  提示 tokens: {usage['prompt_tokens']}")
        print(f"  总计 tokens: {usage['total_tokens']}")
    
    # 打印每个文件的token使用情况
    print("\n各文件token使用详情:")
    for file_path, stats in sorted(file_token_stats.items(), key=lambda x: x[1]["total_tokens"], reverse=True):
        file_name = os.path.basename(file_path)
        print(f"{file_name}:")
        print(f"  完成 tokens: {stats['completion_tokens']}")
        print(f"  提示 tokens: {stats['prompt_tokens']}")
        print(f"  总计 tokens: {stats['total_tokens']}")

if __name__ == "__main__":
    analyze_tokens()
    print("\n" + "="*50 + "\n")
    analyze_pdf_cache_tokens()
