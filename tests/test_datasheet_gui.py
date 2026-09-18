import tkinter as tk
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from insertion_loss_tool.gui import (
    DATASHEET_CURVES,
    InsertionLossStudio,
)


class DatasheetGuiTests(unittest.TestCase):
    """Full regression checks for the datasheet-image Tk page.

    The backend-only GUI self-test intentionally avoids opening a display, so
    it cannot catch failures that occur while this page constructs widgets.
    These checks create the actual window, exercise its state and file paths,
    and then tear it down without entering the event loop.
    """

    def test_datasheet_workbench_combines_multiple_images_into_multiple_networks(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - display-dependent CI boundary
            self.skipTest(f"Tk display is unavailable: {exc}")
        root.withdraw()
        try:
            app = InsertionLossStudio(root)
            tab_names = [app.workspace_notebook.tab(tab_id, "text") for tab_id in app.workspace_notebook.tabs()]
            self.assertEqual(tab_names, ["常规生成", "图片生成"])
            self.assertEqual(len(DATASHEET_CURVES), 4)

            self.assertEqual(len(app.datasheet_networks), 2)
            self.assertEqual(
                [network["name"].get() for network in app.datasheet_networks],
                ["输出 1", "输出 2"],
            )
            self.assertEqual(
                [network["output"].get() for network in app.datasheet_networks],
                ["output_1.s4p", "output_2.s2p"],
            )
            self.assertEqual(app.datasheet_networks[0]["port_count"].get(), "4")
            self.assertEqual(app.datasheet_networks[1]["port_count"].get(), "2")

            with tempfile.TemporaryDirectory() as temp_dir:
                image_paths = []
                for name, color in (("adapter_tx.png", "#355cff"), ("cable_rx.png", "#49bf63")):
                    path = Path(temp_dir) / name
                    photo = tk.PhotoImage(width=8, height=6)
                    photo.put(color, to=(0, 0, 8, 6))
                    photo.write(path, format="png")
                    image_paths.append(path)
                app._load_datasheet_images(image_paths)
                source_options = app._datasheet_source_options()
                self.assertIn("图1-A · 深蓝", source_options)
                self.assertIn("图2-D · 浅蓝", source_options)
                self.assertIn("默认 −20 dB", source_options)
                self.assertIn("复制转置", source_options)
                self.assertIn("公式", source_options)
                self.assertNotIn("默认 · 反射 −20 dB", source_options)
                self.assertFalse(any("/ 曲线" in option for option in source_options))

            first_network = app.datasheet_networks[0]
            self.assertEqual(len(first_network["mappings"]), 16)
            self.assertEqual(first_network["mappings"]["S11"].get(), "默认 −20 dB")
            self.assertEqual(first_network["mappings"]["S12"].get(), "复制 S21")
            self.assertEqual(first_network["mappings"]["S13"].get(), "默认 −80 dB")
            first_network["mappings"]["S31"].set("图2-D · 浅蓝")
            self.assertEqual(first_network["mappings"]["S31"].get(), "图2-D · 浅蓝")

            app.datasheet["network_count"].set("3")
            app._apply_datasheet_network_count()
            self.assertEqual(len(app.datasheet_networks), 3)
            self.assertEqual(app.datasheet_networks[2]["name"].get(), "输出 3")
            self.assertEqual(app.datasheet_networks[2]["output"].get(), "output_3.s2p")
            app._select_datasheet_network(2)
            app.datasheet_networks[2]["port_count"].set("3")
            app._apply_selected_network_ports()
            self.assertEqual(len(app.datasheet_networks[2]["mappings"]), 9)
            self.assertEqual(app.datasheet_networks[2]["output"].get(), "output_3.s3p")
            app.datasheet_networks[2]["output"].set("my_fixture.s3p")
            app.datasheet_networks[2]["port_count"].set("4")
            app._apply_selected_network_ports()
            self.assertEqual(app.datasheet_networks[2]["output"].get(), "my_fixture.s3p")

            with self.assertRaisesRegex(IndexError, "Datasheet network index"):
                app._select_datasheet_network(99)
        finally:
            root.destroy()

    def test_datasheet_workbench_uses_compact_user_facing_copy(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - display-dependent CI boundary
            self.skipTest(f"Tk display is unavailable: {exc}")
        root.withdraw()
        try:
            app = InsertionLossStudio(root)
            tab_names = [app.workspace_notebook.tab(tab_id, "text") for tab_id in app.workspace_notebook.tabs()]
            self.assertEqual(tab_names, ["常规生成", "图片生成"])

            def visible_texts(widget):
                texts = []
                try:
                    text = widget.cget("text")
                except tk.TclError:
                    text = ""
                if text:
                    texts.append(str(text))
                for child in widget.winfo_children():
                    texts.extend(visible_texts(child))
                return texts

            texts = visible_texts(app.datasheet_page)
            for expected in {
                "图片生成 S 参数",
                "导入图片",
                "输出",
                "图片",
                "Sij · 网络 1",
                "数量",
                "＋ 输出",
                "＋ 图片",
                "校准",
                "检查",
                "预览",
            }:
                self.assertIn(expected, texts)

            all_copy = "\n".join(texts)
            for redundant in (
                "建立多个输出网络",
                "每个文件可以独立选择",
                "每张图片独立识别",
                "每个下拉框可以选择",
                "1 · 待生成",
                "2 · 图片",
                "3 · 当前网络",
                "尚未实现",
            ):
                self.assertNotIn(redundant, all_copy)
            self.assertEqual(app.datasheet["status"].get(), "未生成")
        finally:
            root.destroy()

    def test_datasheet_output_and_port_boundaries(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - display-dependent CI boundary
            self.skipTest(f"Tk display is unavailable: {exc}")
        root.withdraw()
        try:
            app = InsertionLossStudio(root)
            app.datasheet["network_count"].set("1")
            app._apply_datasheet_network_count()
            self.assertEqual(len(app.datasheet_networks), 1)
            self.assertEqual(app.datasheet_selected_network, 0)

            app.datasheet["network_count"].set("6")
            app._apply_datasheet_network_count()
            self.assertEqual(len(app.datasheet_networks), 6)
            self.assertEqual(
                [network["name"].get() for network in app.datasheet_networks],
                [f"输出 {index}" for index in range(1, 7)],
            )
            app._add_datasheet_network()
            self.assertEqual(len(app.datasheet_networks), 6)
            self.assertEqual(app.datasheet["status"].get(), "最多 6 个输出")

            app._select_datasheet_network(5)
            network = app.datasheet_networks[5]
            network["port_count"].set("0")
            app._apply_selected_network_ports()
            self.assertEqual(network["port_count"].get(), "1")
            self.assertEqual(list(network["mappings"]), ["S11"])
            self.assertEqual(network["output"].get(), "output_6.s1p")

            network["port_count"].set("9")
            app._apply_selected_network_ports()
            self.assertEqual(network["port_count"].get(), "8")
            self.assertEqual(len(network["mappings"]), 64)
            self.assertEqual(network["output"].get(), "output_6.s8p")
            self.assertEqual(app.datasheet["selected_network_summary"].get(), "网络 6 · 8 端口 · 64 个 Sij")
        finally:
            root.destroy()

    def test_datasheet_image_pool_handles_png_failure_and_clear(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - display-dependent CI boundary
            self.skipTest(f"Tk display is unavailable: {exc}")
        root.withdraw()
        try:
            app = InsertionLossStudio(root)
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                png_path = temp_path / "plot.png"
                photo = tk.PhotoImage(width=8, height=6)
                photo.put("#ff4f4f", to=(0, 0, 8, 6))
                photo.write(png_path, format="png")

                app._load_datasheet_images([png_path])
                self.assertEqual(app.datasheet_image_paths, [png_path])
                self.assertEqual(app.datasheet_image_path, png_path)
                self.assertEqual(app.datasheet["status"].get(), "1 图 · 4 候选")
                self.assertTrue(app._show_datasheet_image(0))
                self.assertTrue(all(hasattr(canvas, "preview_photo") for canvas in app.datasheet_preview_canvases))
                self.assertTrue(
                    all(
                        any(canvas.type(item) == "image" for item in canvas.find_all())
                        for canvas in app.datasheet_preview_canvases
                    )
                )
                app.datasheet_networks[0]["mappings"]["S31"].set("图1-A · 深蓝")

                unsupported_path = temp_path / "plot.jpg"
                unsupported_path.write_bytes(b"not-an-image")
                app._load_datasheet_images([unsupported_path])
                self.assertEqual(app.datasheet["status"].get(), "1 文件 · 预览受限")
                self.assertFalse(any(option.startswith("图1-") for option in app._datasheet_source_options()))
                self.assertEqual(app.datasheet_networks[0]["mappings"]["S31"].get(), "未知")
                app._check_datasheet_mappings()
                self.assertEqual(app.datasheet["status"].get(), "默认 17 · 待定 1")
                self.assertTrue(
                    all(
                        not any(canvas.type(item) == "image" for item in canvas.find_all())
                        and not hasattr(canvas, "preview_photo")
                        for canvas in app.datasheet_preview_canvases
                    )
                )
                item = app.datasheet_resource_list.winfo_children()[0]
                item_texts = [child.cget("text") for child in item.winfo_children()]
                self.assertIn("图1 · plot.jpg · 预览受限", item_texts)

                app._load_datasheet_images([unsupported_path, png_path])
                self.assertEqual(app.datasheet_image_path, png_path)
                self.assertEqual(app.datasheet["status"].get(), "2 图 · 4 候选 · 1 受限")
                mixed_options = app._datasheet_source_options()
                self.assertFalse(any(option.startswith("图1-") for option in mixed_options))
                self.assertTrue(any(option.startswith("图2-") for option in mixed_options))
                self.assertTrue(
                    all(
                        any(canvas.type(item) == "image" for item in canvas.find_all())
                        for canvas in app.datasheet_preview_canvases
                    )
                )

                app._load_datasheet_images([])
                self.assertEqual(app.datasheet_image_paths, [])
                self.assertIsNone(app.datasheet_image_path)
                self.assertEqual(app.datasheet["status"].get(), "未生成")
                self.assertTrue(
                    all(
                        not any(canvas.type(item) == "image" for item in canvas.find_all())
                        and not hasattr(canvas, "preview_photo")
                        for canvas in app.datasheet_preview_canvases
                    )
                )
                empty_texts = [child.cget("text") for child in app.datasheet_resource_list.winfo_children()]
                self.assertEqual(empty_texts, ["暂无图片"])
        finally:
            root.destroy()

    def test_datasheet_browser_cancels_cleanly_and_deduplicates_paths(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - display-dependent CI boundary
            self.skipTest(f"Tk display is unavailable: {exc}")
        root.withdraw()
        try:
            app = InsertionLossStudio(root)
            with tempfile.TemporaryDirectory() as temp_dir:
                first = Path(temp_dir) / "first.png"
                second = Path(temp_dir) / "second.png"
                for path in (first, second):
                    photo = tk.PhotoImage(width=8, height=6)
                    photo.put("#355cff", to=(0, 0, 8, 6))
                    photo.write(path, format="png")
                app._load_datasheet_images([first])

                with patch("tkinter.filedialog.askopenfilenames", return_value=()):
                    app._browse_datasheet_images()
                self.assertEqual(app.datasheet_image_paths, [first])

                with patch(
                    "tkinter.filedialog.askopenfilenames",
                    return_value=(str(first), str(second)),
                ):
                    app._browse_datasheet_images()
                self.assertEqual(app.datasheet_image_paths, [first, second])
                self.assertEqual(len(app._datasheet_source_options()), 15)
        finally:
            root.destroy()

    def test_datasheet_unavailable_actions_are_disabled_and_check_is_live(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - display-dependent CI boundary
            self.skipTest(f"Tk display is unavailable: {exc}")
        root.withdraw()
        try:
            app = InsertionLossStudio(root)

            def buttons(widget):
                found = {}
                for child in widget.winfo_children():
                    if isinstance(child, app.ttk.Button):
                        found[str(child.cget("text"))] = child
                    found.update(buttons(child))
                return found

            page_buttons = buttons(app.datasheet_page)
            self.assertIn("disabled", page_buttons["校准"].state())
            self.assertIn("disabled", page_buttons["预览"].state())

            app.datasheet_networks[1]["mappings"]["S11"].set("未知")
            page_buttons["检查"].invoke()
            self.assertEqual(app.datasheet["status"].get(), "默认 17 · 待定 1")

            app.datasheet_networks[0]["mappings"]["S31"].set("图1-A · 深蓝")
            page_buttons["检查"].invoke()
            self.assertEqual(app.datasheet["status"].get(), "默认 16 · 待定 2")
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
