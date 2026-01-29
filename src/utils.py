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


def build_preview(questions: List[Dict[str, Any]], output_path: str = None) -> str:
    """
    步骤4: 生成HTML预览

    将分割后的题目列表生成HTML预览页面，供用户查看和选择

    Args:
        questions: 题目列表
        output_path: 输出HTML文件路径（可选）

    Returns:
        str: HTML预览文件路径
    """
    if output_path is None:
        results_dir = os.getenv("RESULTS_DIR", "results")
        os.makedirs(results_dir, exist_ok=True)
        output_path = os.path.join(results_dir, "preview.html")

    # 构建HTML内容
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>题目预览</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .question {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .question-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        .question-id {
            font-size: 1.2em;
            font-weight: bold;
            color: #2196F3;
            margin-right: 15px;
        }
        .question-type {
            display: inline-block;
            padding: 4px 12px;
            background-color: #4CAF50;
            color: white;
            border-radius: 4px;
            font-size: 0.85em;
        }
        .question-content {
            line-height: 1.8;
            color: #333;
        }
        .formula {
            display: block;
            margin: 10px 0;
            padding: 10px;
            background-color: #f9f9f9;
            border-left: 3px solid #2196F3;
            font-family: 'Courier New', monospace;
        }
        .option {
            margin: 8px 0;
            padding-left: 10px;
        }
        .image-ref {
            color: #FF9800;
            font-style: italic;
        }
        .select-btn {
            margin-top: 10px;
            padding: 8px 16px;
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .select-btn:hover {
            background-color: #1976D2;
        }
        .select-btn.selected {
            background-color: #4CAF50;
        }
        h1 {
            text-align: center;
            color: #333;
        }
        .export-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            padding: 15px 30px;
            background-color: #FF5722;
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1.1em;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .export-btn:hover {
            background-color: #E64A19;
        }
    </style>
</head>
<body>
    <h1>📝 题目预览与选择</h1>
"""

    # 添加题目
    for q in questions:
        html_content += f"""
    <div class="question" data-id="{q.get('question_id', '')}">
        <div class="question-header">
            <span class="question-id">题目 {q.get('question_id', '')}</span>
            <span class="question-type">{q.get('question_type', '未知')}</span>
        </div>
        <div class="question-content">
"""

        # 添加内容块（只有 text 和 image 两种类型，公式以 LaTeX 标记嵌入 text 中）
        for block in q.get('content_blocks', []):
            if block['block_type'] == 'text':
                html_content += f"            <p>{block['content']}</p>\n"
            elif block['block_type'] == 'image':
                html_content += f"            <p class='image-ref'>📷 图片: {block.get('content', '')}</p>\n"

        # 添加选项（如果是选择题）
        if q.get('options'):
            html_content += "            <div class='options'>\n"
            for option in q['options']:
                html_content += f"                <div class='option'>{option}</div>\n"
            html_content += "            </div>\n"

        html_content += """
            <button class="select-btn" onclick="toggleSelect(this)">选择此题</button>
        </div>
    </div>
"""

    # 添加脚本和底部按钮
    html_content += """
    <button class="export-btn" onclick="exportSelected()">导出选中题目</button>

    <script>
        function toggleSelect(btn) {
            btn.classList.toggle('selected');
            if (btn.classList.contains('selected')) {
                btn.textContent = '✓ 已选择';
            } else {
                btn.textContent = '选择此题';
            }
        }

        function exportSelected() {
            const selected = [];
            document.querySelectorAll('.select-btn.selected').forEach(btn => {
                const questionDiv = btn.closest('.question');
                const questionId = questionDiv.getAttribute('data-id');
                selected.push(questionId);
            });

            if (selected.length === 0) {
                alert('请至少选择一道题目！');
                return;
            }

            alert('已选择 ' + selected.length + ' 道题目\\n题号: ' + selected.join(', ') +
                  '\\n\\n请在命令行中使用这些题号导出错题本。');
        }
    </script>
</body>
</html>
"""

    # 保存HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    console.print(f"[green]✓ HTML预览已生成: {output_path}[/green]")

    return output_path


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

                # 如果还是空的，根据 bbox 生成图片路径
                if not image_path and 'bbox' in block:
                    bbox = block['bbox']
                    struct_dir = os.getenv("STRUCT_DIR", "output/struct")
                    # 使用相对路径，因为 wrongbook.md 在 results/ 目录下
                    image_path = f"../{struct_dir}/imgs/img_in_image_box_{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}.jpg"

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
