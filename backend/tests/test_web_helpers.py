"""
web_app.py 中纯函数的单元测试

覆盖函数：
- allowed_file
- _safe_join
- _vite_collect_imports
"""

import os
import pytest
from web_app import allowed_file, _safe_join, _vite_collect_imports


# ═══════════════════════════════════════════════════════════
# allowed_file
# ═══════════════════════════════════════════════════════════


class TestAllowedFile:
    """allowed_file 测试"""

    def test_pdf(self):
        assert allowed_file("test.pdf") is True

    def test_png(self):
        assert allowed_file("photo.png") is True

    def test_jpg(self):
        assert allowed_file("image.jpg") is True

    def test_jpeg(self):
        assert allowed_file("image.jpeg") is True

    def test_bmp(self):
        assert allowed_file("image.bmp") is True

    def test_tiff(self):
        assert allowed_file("image.tiff") is True

    def test_webp(self):
        assert allowed_file("image.webp") is True

    def test_exe_rejected(self):
        assert allowed_file("malware.exe") is False

    def test_py_rejected(self):
        assert allowed_file("script.py") is False

    def test_txt_rejected(self):
        assert allowed_file("notes.txt") is False

    def test_no_extension(self):
        assert allowed_file("noext") is False

    def test_empty_string(self):
        assert allowed_file("") is False

    def test_case_insensitive(self):
        """扩展名大写应被接受"""
        assert allowed_file("photo.PNG") is True
        assert allowed_file("doc.PDF") is True

    def test_multiple_dots(self):
        """多个点的文件名应以最后一个扩展名为准"""
        assert allowed_file("my.file.pdf") is True
        assert allowed_file("my.pdf.exe") is False

    def test_hidden_file(self):
        assert allowed_file(".pdf") is True  # "." 在 filename 中，后缀为 "pdf"


# ═══════════════════════════════════════════════════════════
# _safe_join
# ═══════════════════════════════════════════════════════════


class TestSafeJoin:
    """_safe_join 路径安全校验测试"""

    def test_valid_relative_path(self, tmp_path):
        base = str(tmp_path)
        result = _safe_join(base, "file.txt")
        assert result is not None
        assert result == os.path.abspath(os.path.join(base, "file.txt"))

    def test_nested_path(self, tmp_path):
        base = str(tmp_path)
        result = _safe_join(base, "sub/dir/file.txt")
        assert result is not None

    def test_traversal_rejected(self, tmp_path):
        """目录遍历攻击应被阻止"""
        base = str(tmp_path)
        result = _safe_join(base, "../../../etc/passwd")
        assert result is None

    def test_double_dot_in_middle(self, tmp_path):
        base = str(tmp_path)
        result = _safe_join(base, "sub/../../../etc/passwd")
        assert result is None

    def test_valid_dotdot_within_base(self, tmp_path):
        """不跳出 base 的 .. 应被允许"""
        base = str(tmp_path)
        # sub/../file.txt 等价于 file.txt，仍在 base 内
        result = _safe_join(base, "sub/../file.txt")
        assert result is not None

    def test_empty_rel_path(self, tmp_path):
        """空路径不应通过（等于 base 本身，不以 base+sep 开头）"""
        base = str(tmp_path)
        result = _safe_join(base, "")
        assert result is None


# ═══════════════════════════════════════════════════════════
# _vite_collect_imports
# ═══════════════════════════════════════════════════════════


class TestViteCollectImports:
    """_vite_collect_imports 测试"""

    def test_no_imports(self):
        manifest = {
            "index.html": {"file": "main.js"}
        }
        result = _vite_collect_imports(manifest, "index.html")
        assert result == []

    def test_single_import(self):
        manifest = {
            "index.html": {
                "file": "main.js",
                "imports": ["_vendor.js"]
            },
            "_vendor.js": {
                "file": "assets/vendor-abc.js"
            }
        }
        result = _vite_collect_imports(manifest, "index.html")
        assert result == ["assets/vendor-abc.js"]

    def test_chain_imports(self):
        """A → B → C 链式依赖"""
        manifest = {
            "index.html": {
                "file": "main.js",
                "imports": ["_a.js"]
            },
            "_a.js": {
                "file": "assets/a.js",
                "imports": ["_b.js"]
            },
            "_b.js": {
                "file": "assets/b.js"
            }
        }
        result = _vite_collect_imports(manifest, "index.html")
        # 栈式遍历，先 pop _a.js，发现 _b.js → pop _b.js → 输出 b, a
        assert set(result) == {"assets/a.js", "assets/b.js"}

    def test_circular_imports(self):
        """循环依赖不应死循环"""
        manifest = {
            "index.html": {
                "file": "main.js",
                "imports": ["_a.js"]
            },
            "_a.js": {
                "file": "assets/a.js",
                "imports": ["_b.js"]
            },
            "_b.js": {
                "file": "assets/b.js",
                "imports": ["_a.js"]  # 循环
            }
        }
        result = _vite_collect_imports(manifest, "index.html")
        assert len(result) == 2

    def test_missing_entry(self):
        """入口不存在时返回空"""
        result = _vite_collect_imports({}, "nonexistent")
        assert result == []

    def test_missing_import_key(self):
        """import 引用的 key 在 manifest 中不存在"""
        manifest = {
            "index.html": {
                "file": "main.js",
                "imports": ["_missing.js"]
            }
        }
        result = _vite_collect_imports(manifest, "index.html")
        assert result == []

    def test_diamond_dependency(self):
        """菱形依赖：A → B,C; B → D; C → D — D 只应出现一次"""
        manifest = {
            "index.html": {
                "file": "main.js",
                "imports": ["_b.js", "_c.js"]
            },
            "_b.js": {
                "file": "assets/b.js",
                "imports": ["_d.js"]
            },
            "_c.js": {
                "file": "assets/c.js",
                "imports": ["_d.js"]
            },
            "_d.js": {
                "file": "assets/d.js"
            }
        }
        result = _vite_collect_imports(manifest, "index.html")
        assert len(result) == 3
        assert result.count("assets/d.js") == 1
