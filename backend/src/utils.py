"""
通用工具函数
包含确定性的工具逻辑，不需要LLM参与
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from rich.console import Console
from pdf2image import convert_from_path
from PIL import Image

load_dotenv()
console = Console()


def prepare_input(file_path: str) -> List[str]:
    """
    步骤1: 准备输入文件

    接受PDF或图片文件,统一转换为标准化的图片列表

    Args:
        file_path: 输入文件路径 (PDF或图片文件)

    Returns:
        List[str]: 标准化后的图片路径列表

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 不支持的文件格式
    """
    # 验证文件存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 获取输出目录
    pages_dir = os.getenv("PAGES_DIR", "output/pages")
    os.makedirs(pages_dir, exist_ok=True)

    # 获取文件扩展名
    file_ext = Path(file_path).suffix.lower()
    file_stem = Path(file_path).stem

    # 支持的图片格式
    image_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}

    image_paths = []

    console.print(f"[cyan]正在处理文件: {file_path}[/cyan]")

    if file_ext == '.pdf':
        # PDF转图片
        console.print("[yellow]检测到PDF文件,正在转换为图片...[/yellow]")

        try:
            # 转换PDF为图片列表
            images = convert_from_path(file_path, dpi=300)

            console.print(f"[green]成功转换,共{len(images)}页[/green]")

            # 保存每一页
            for i, image in enumerate(images, start=1):
                output_path = os.path.join(pages_dir, f"{file_stem}_page_{i:03d}.png")
                image.save(output_path, 'PNG')
                image_paths.append(output_path)
                console.print(f"[green]  ✓ 保存第{i}页: {output_path}[/green]")

        except Exception as e:
            console.print(f"[red]PDF转换失败: {e}[/red]")
            raise

    elif file_ext in image_formats:
        # 已经是图片,复制到标准位置
        console.print("[yellow]检测到图片文件,正在标准化...[/yellow]")

        try:
            # 打开并重新保存为PNG格式(标准化)
            image = Image.open(file_path)
            output_path = os.path.join(pages_dir, f"{file_stem}.png")
            image.save(output_path, 'PNG')
            image_paths.append(output_path)
            console.print(f"[green]  ✓ 标准化完成: {output_path}[/green]")

        except Exception as e:
            console.print(f"[red]图片处理失败: {e}[/red]")
            raise

    else:
        raise ValueError(
            f"不支持的文件格式: {file_ext}\n"
            f"支持的格式: PDF (.pdf) 或图片 ({', '.join(image_formats)})"
        )

    console.print(f"[bold green]✓ 输入准备完成,共{len(image_paths)}张图片[/bold green]")

    return image_paths


def export_wrongbook(questions: List[Dict[str, Any]], selected_ids: List[str], output_path: str = None) -> str:
    """
    步骤5: 导出错题本

    将用户选择的题目导出为Markdown格式的错题本

    Args:
        questions: 题目列表
        selected_ids: 用户选择的题目ID列表
        output_path: 输出Markdown文件路径（可选）

    Returns:
        str: 导出的Markdown文件路径
    """
    if output_path is None:
        results_dir = os.getenv("RESULTS_DIR", "results")
        os.makedirs(results_dir, exist_ok=True)
        output_path = os.path.join(results_dir, "wrongbook.md")

    # 过滤选中的题目
    selected_questions = [q for q in questions if q.get('question_id') in selected_ids]

    # 构建Markdown内容
    md_content = "# 错题本\n\n"
    md_content += f"> 共收录 {len(selected_questions)} 道题目\n\n"
    md_content += "---\n\n"

    for i, q in enumerate(selected_questions, start=1):
        md_content += f"## {i}. 题目 {q.get('question_id', '')} ({q.get('question_type', '未知')})\n\n"

        # 获取图片引用列表，用于填充空的 image block
        image_refs = q.get('image_refs', [])
        image_ref_index = 0

        # 添加内容块（只有 text 和 image，公式以 LaTeX 标记嵌入 text 中）
        for block in q.get('content_blocks', []):
            if block['block_type'] == 'text':
                md_content += f"{block['content']}\n\n"
            elif block['block_type'] == 'image':
                # 优先使用 block 的 content
                image_path = block.get('content', '').strip()

                # 如果为空，尝试从 image_refs 获取
                if not image_path and image_ref_index < len(image_refs):
                    image_path = image_refs[image_ref_index]
                    image_ref_index += 1

                # 将 Flask 路由路径转为 Markdown 相对路径
                if image_path.startswith("/images/"):
                    struct_dir = os.getenv("STRUCT_DIR", "output/struct")
                    image_path = f"../{struct_dir}/imgs/{image_path[len('/images/'):]}"

                md_content += f"![图片]({image_path})\n\n"

        # 添加选项
        if q.get('options'):
            for option in q['options']:
                md_content += f"{option}\n\n"

        md_content += "### 我的答案\n\n"
        md_content += "_（请在此处填写你的答案）_\n\n"

        md_content += "### 正确答案\n\n"
        md_content += "_（请在此处填写正确答案）_\n\n"

        md_content += "### 解析\n\n"
        md_content += "_（请在此处填写解题思路和知识点）_\n\n"

        md_content += "---\n\n"

    # 保存Markdown
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    console.print(f"[green]✓ 错题本已导出: {output_path}[/green]")

    return output_path
