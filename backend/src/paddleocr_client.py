"""
PaddleOCR 文档解析客户端
用于调用 PaddleOCR-VL API 进行文档结构化解析
"""

import os
import json
import base64
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
import aiohttp
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# 加载环境变量
load_dotenv()

console = Console()


class PaddleOCRClient:
    """PaddleOCR API 客户端"""

    def __init__(self):
        """初始化客户端，从环境变量读取配置"""
        self.api_url = os.getenv("PADDLEOCR_API_URL")
        self.token = os.getenv("PADDLEOCR_API_TOKEN")
        self.use_doc_orientation = os.getenv("PADDLEOCR_USE_DOC_ORIENTATION", "false").lower() == "true"
        self.use_doc_unwarping = os.getenv("PADDLEOCR_USE_DOC_UNWARPING", "false").lower() == "true"
        self.use_chart_recognition = os.getenv("PADDLEOCR_USE_CHART_RECOGNITION", "false").lower() == "true"
        # 验证必需的配置
        if not self.api_url or not self.token:
            raise ValueError(
                "缺少必需的环境变量。请确保 .env 文件中配置了：\n"
                "- PADDLEOCR_API_URL\n"
                "- PADDLEOCR_API_TOKEN"
            )

    def parse_image(
        self,
        image_path: str,
        save_output: bool = True,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """解析图片并返回结构化结果

        Args:
            image_path: 图片文件路径
            save_output: 是否保存输出结果
            output_dir: 输出目录（默认从环境变量 STRUCT_DIR 读取）

        Returns:
            Dict: PaddleOCR API 返回的结构化结果
        """
        if output_dir is None:
            from .utils import RUNTIME_ROOT
            output_dir = os.getenv("STRUCT_DIR", os.path.join(RUNTIME_ROOT, "struct"))

        console.print(f"[cyan]正在解析图片: {image_path}[/cyan]")

        # 读取图片并转为 base64
        with open(image_path, "rb") as file:
            file_bytes = file.read()
            file_data = base64.b64encode(file_bytes).decode("ascii")

        # 准备请求
        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }

        payload = {
            "file": file_data,
            "fileType": 1,  # 1 表示图片
            "useDocOrientationClassify": self.use_doc_orientation,
            "useDocUnwarping": self.use_doc_unwarping,
            "useChartRecognition": self.use_chart_recognition,
        }

        # 调用 API
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在调用 PaddleOCR API...", total=None)

            response = requests.post(self.api_url, json=payload, headers=headers)
            progress.update(task, completed=True)

        if response.status_code != 200:
            console.print(f"[red]API 调用失败: HTTP {response.status_code}[/red]")
            console.print(f"[red]响应内容: {response.text}[/red]")
            raise Exception(f"PaddleOCR API 调用失败: {response.status_code}")

        result = response.json()["result"]

        console.print(f"[green]✓ 解析成功![/green]")

        # 保存结果
        if save_output:
            os.makedirs(output_dir, exist_ok=True)

            # 保存 JSON 结果
            filename = Path(image_path).stem + "_struct.json"
            output_path = os.path.join(output_dir, filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            console.print(f"[green]结构化结果已保存到: {output_path}[/green]")

            # 下载并保存图片资源
            file_prefix = Path(image_path).stem
            self._save_images(result, output_dir, file_prefix)

        return result

    def _save_images(self, result: Dict[str, Any], output_dir: str, file_prefix: str = ""):
        """下载并保存结果中的图片资源

        Args:
            result: PaddleOCR 返回结果
            output_dir: 输出目录
            file_prefix: 文件名前缀（用于区分不同图片的输出）
        """
        for i, res in enumerate(result.get("layoutParsingResults", [])):
            # 保存 Markdown 文档
            markdown_text = res.get("markdown", {}).get("text", "")
            if markdown_text:
                md_filename = os.path.join(output_dir, f"{file_prefix}_doc_{i}.md")
                with open(md_filename, "w", encoding="utf-8") as md_file:
                    md_file.write(markdown_text)
                console.print(f"[green]Markdown 已保存: {md_filename}[/green]")

            # 下载 markdown 中的图片
            images = res.get("markdown", {}).get("images", {})
            for img_path, img_url in images.items():
                full_img_path = os.path.join(output_dir, img_path)
                os.makedirs(os.path.dirname(full_img_path), exist_ok=True)

                try:
                    img_response = requests.get(img_url)
                    if img_response.status_code == 200:
                        with open(full_img_path, "wb") as img_file:
                            img_file.write(img_response.content)
                        console.print(f"[green]图片已保存: {full_img_path}[/green]")
                    else:
                        console.print(f"[yellow]图片下载失败: {img_path}[/yellow]")
                except Exception as e:
                    console.print(f"[yellow]图片下载出错: {img_path} - {e}[/yellow]")

            # 下载输出图片
            output_images = res.get("outputImages", {})
            for img_name, img_url in output_images.items():
                try:
                    img_response = requests.get(img_url)
                    if img_response.status_code == 200:
                        filename = os.path.join(output_dir, f"{img_name}_{file_prefix}_{i}.jpg")
                        with open(filename, "wb") as f:
                            f.write(img_response.content)
                        console.print(f"[green]输出图片已保存: {filename}[/green]")
                except Exception as e:
                    console.print(f"[yellow]输出图片下载出错: {img_name} - {e}[/yellow]")

    def parse_pdf(
        self,
        pdf_path: str,
        save_output: bool = True,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """解析 PDF 并返回结构化结果

        Args:
            pdf_path: PDF 文件路径
            save_output: 是否保存输出结果
            output_dir: 输出目录（默认从环境变量 STRUCT_DIR 读取）

        Returns:
            Dict: PaddleOCR API 返回的结构化结果
        """
        if output_dir is None:
            from .utils import RUNTIME_ROOT
            output_dir = os.getenv("STRUCT_DIR", os.path.join(RUNTIME_ROOT, "struct"))

        console.print(f"[cyan]正在解析 PDF: {pdf_path}[/cyan]")

        # 读取 PDF 并转为 base64
        with open(pdf_path, "rb") as file:
            file_bytes = file.read()
            file_data = base64.b64encode(file_bytes).decode("ascii")

        # 准备请求
        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }

        payload = {
            "file": file_data,
            "fileType": 0,  # 0 表示 PDF
            "useDocOrientationClassify": self.use_doc_orientation,
            "useDocUnwarping": self.use_doc_unwarping,
            "useChartRecognition": self.use_chart_recognition,
        }

        # 调用 API
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在调用 PaddleOCR API...", total=None)

            response = requests.post(self.api_url, json=payload, headers=headers)
            progress.update(task, completed=True)

        if response.status_code != 200:
            console.print(f"[red]API 调用失败: HTTP {response.status_code}[/red]")
            console.print(f"[red]响应内容: {response.text}[/red]")
            raise Exception(f"PaddleOCR API 调用失败: {response.status_code}")

        result = response.json()["result"]

        console.print(f"[green]✓ 解析成功![/green]")

        # 保存结果
        if save_output:
            os.makedirs(output_dir, exist_ok=True)

            # 保存 JSON 结果
            filename = Path(pdf_path).stem + "_struct.json"
            output_path = os.path.join(output_dir, filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            console.print(f"[green]结构化结果已保存到: {output_path}[/green]")

            # 下载并保存图片资源
            self._save_images(result, output_dir)

        return result

    # ── 异步方法 ──────────────────────────────────────────────

    async def async_parse_image(
        self,
        session: aiohttp.ClientSession,
        image_path: str,
        save_output: bool = True,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """异步解析单张图片

        Args:
            session: aiohttp 会话（由调用方管理生命周期）
            image_path: 图片文件路径
            save_output: 是否保存输出结果
            output_dir: 输出目录

        Returns:
            Dict: PaddleOCR API 返回的结构化结果
        """
        if output_dir is None:
            from .utils import RUNTIME_ROOT
            output_dir = os.getenv("STRUCT_DIR", os.path.join(RUNTIME_ROOT, "struct"))

        console.print(f"[cyan]正在解析图片: {image_path}[/cyan]")

        # 读取图片并转为 base64
        with open(image_path, "rb") as file:
            file_bytes = file.read()
            file_data = base64.b64encode(file_bytes).decode("ascii")

        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }

        payload = {
            "file": file_data,
            "fileType": 1,
            "useDocOrientationClassify": self.use_doc_orientation,
            "useDocUnwarping": self.use_doc_unwarping,
            "useChartRecognition": self.use_chart_recognition,
        }

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            async with session.post(self.api_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data["result"]
                    break
                else:
                    text = await response.text()
                    if attempt < max_retries:
                        wait = attempt * 5
                        console.print(f"[yellow]API 调用失败 (HTTP {response.status})，{wait}s 后重试 ({attempt}/{max_retries})...[/yellow]")
                        await asyncio.sleep(wait)
                    else:
                        console.print(f"[red]API 调用失败: HTTP {response.status}，已重试 {max_retries} 次[/red]")
                        console.print(f"[red]响应内容: {text}[/red]")
                        raise Exception(f"PaddleOCR API 调用失败: {response.status}")

        console.print(f"[green]✓ 解析成功: {image_path}[/green]")

        # 保存结果
        if save_output:
            os.makedirs(output_dir, exist_ok=True)

            filename = Path(image_path).stem + "_struct.json"
            output_path = os.path.join(output_dir, filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            console.print(f"[green]结构化结果已保存到: {output_path}[/green]")

            file_prefix = Path(image_path).stem
            await self._async_save_images(session, result, output_dir, file_prefix)

        return result

    async def _async_download_image(
        self,
        session: aiohttp.ClientSession,
        url: str,
        save_path: str
    ):
        """异步下载单张图片"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, "wb") as f:
                        f.write(content)
                    console.print(f"[green]图片已保存: {save_path}[/green]")
                else:
                    console.print(f"[yellow]图片下载失败: {save_path}[/yellow]")
        except Exception as e:
            console.print(f"[yellow]图片下载出错: {save_path} - {e}[/yellow]")

    async def _async_save_images(
        self,
        session: aiohttp.ClientSession,
        result: Dict[str, Any],
        output_dir: str,
        file_prefix: str = ""
    ):
        """异步下载并保存结果中的所有图片资源

        Args:
            session: aiohttp 会话
            result: PaddleOCR 返回结果
            output_dir: 输出目录
            file_prefix: 文件名前缀（用于区分不同图片的输出，避免并发写入冲突）
        """
        for i, res in enumerate(result.get("layoutParsingResults", [])):
            # 保存 Markdown 文档（同步文件写入）
            markdown_text = res.get("markdown", {}).get("text", "")
            if markdown_text:
                md_filename = os.path.join(output_dir, f"{file_prefix}_doc_{i}.md")
                with open(md_filename, "w", encoding="utf-8") as md_file:
                    md_file.write(markdown_text)
                console.print(f"[green]Markdown 已保存: {md_filename}[/green]")

            # 收集所有图片下载任务
            download_tasks = []

            images = res.get("markdown", {}).get("images", {})
            for img_path, img_url in images.items():
                full_img_path = os.path.join(output_dir, img_path)
                download_tasks.append(
                    self._async_download_image(session, img_url, full_img_path)
                )

            output_images = res.get("outputImages", {})
            for img_name, img_url in output_images.items():
                filename = os.path.join(output_dir, f"{img_name}_{file_prefix}_{i}.jpg")
                download_tasks.append(
                    self._async_download_image(session, img_url, filename)
                )

            # 并发下载所有图片
            if download_tasks:
                await asyncio.gather(*download_tasks)

    async def parse_images_async(
        self,
        image_paths: List[str],
        save_output: bool = True,
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """异步并发解析多张图片

        Args:
            image_paths: 图片路径列表
            save_output: 是否保存输出结果
            output_dir: 输出目录

        Returns:
            List[Dict]: 每张图片的结构化结果（顺序与输入一致）
        """
        console.print(f"[bold cyan]异步并发解析 {len(image_paths)} 张图片...[/bold cyan]")

        async with aiohttp.ClientSession() as session:
            tasks = [
                self.async_parse_image(session, path, save_output, output_dir)
                for path in image_paths
            ]
            results = await asyncio.gather(*tasks)

        console.print(f"[bold green]✓ 全部 {len(results)} 张图片解析完成[/bold green]")
        return list(results)


def main():
    """测试函数"""
    client = PaddleOCRClient()

    # 测试解析图片
    test_image = "input/test.png"  # 替换为实际测试图片

    if os.path.exists(test_image):
        result = client.parse_image(test_image)
        console.print(f"\n[bold cyan]返回结果概览:[/bold cyan]")
        console.print(f"结果类型: {type(result)}")
        console.print(f"结果键: {list(result.keys())}")
    else:
        console.print(f"[red]测试图片不存在: {test_image}[/red]")
        console.print("[yellow]请在 input/ 目录下放置测试图片（命名为 test.png）[/yellow]")


if __name__ == "__main__":
    main()
