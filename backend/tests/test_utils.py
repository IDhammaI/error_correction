"""
utils.py 工具函数的单元测试

覆盖函数：
- prepare_input (Mock pdf2image 和 PIL)
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.utils import prepare_input

@pytest.fixture
def mock_env(monkeypatch, tmp_path):
    """设置环境变量，使用临时目录作为 runtime_data"""
    runtime_root = tmp_path / "runtime_data"
    pages_dir = runtime_root / "pages"
    monkeypatch.setenv("PAGES_DIR", str(pages_dir))
    return pages_dir

class TestPrepareInput:
    """prepare_input 测试"""

    @patch("src.utils.convert_from_path")
    def test_pdf_conversion(self, mock_convert, mock_env, tmp_path):
        """测试 PDF 转图片流程"""
        # 确保环境变量已生效（虽然没有直接使用 mock_env 变量，但 fixture 必须运行）
        assert os.getenv("PAGES_DIR")

        # 模拟 PDF 文件
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        # 模拟 convert_from_path 返回两个 PIL Image 对象
        mock_img1 = MagicMock()
        mock_img2 = MagicMock()
        mock_convert.return_value = [mock_img1, mock_img2]

        # 执行 prepare_input
        result = prepare_input(str(pdf_path))

        # 验证结果
        assert len(result) == 2
        assert result[0].endswith("_page_001.png")
        assert result[1].endswith("_page_002.png")
        
        # 验证是否调用了 save
        assert mock_img1.save.called
        assert mock_img2.save.called

    @patch("src.utils.Image.open")
    def test_image_standardization(self, mock_open, mock_env, tmp_path):
        """测试图片标准化流程"""
        # 确保环境变量已生效
        assert os.getenv("PAGES_DIR")

        # 模拟图片文件
        img_path = tmp_path / "test.jpg"
        img_path.touch()

        # 模拟 Image.open
        mock_img = MagicMock()
        mock_open.return_value = mock_img

        # 执行 prepare_input
        result = prepare_input(str(img_path))

        # 验证结果
        assert len(result) == 1
        assert result[0].endswith(".png")
        assert "runtime_data" in result[0]

        # 验证是否调用了 save
        mock_img.save.assert_called_with(result[0], 'PNG')

    def test_file_not_found(self):
        """文件不存在应抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            prepare_input("non_existent_file.pdf")

    def test_unsupported_format(self, tmp_path):
        """不支持的文件格式应抛出 ValueError"""
        txt_path = tmp_path / "test.txt"
        txt_path.touch()
        
        with pytest.raises(ValueError) as excinfo:
            prepare_input(str(txt_path))
        assert "不支持的文件格式" in str(excinfo.value)
