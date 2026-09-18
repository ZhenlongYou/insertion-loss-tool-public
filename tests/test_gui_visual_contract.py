# Codex说明(自动生成)： 导入 tkinter as tk，提供本文件后续流程需要的库能力。
import tkinter as tk
# Codex说明(自动生成)： 导入 unittest，组织单元测试和断言。
import unittest
# Codex说明(自动生成)： 从 tkinter 导入 ttk，提供本文件后续流程需要的库能力。
from tkinter import ttk

# Codex说明(自动生成)： 从 insertion_loss_tool.gui 导入 BASE_MINIMUM_WINDOW_SIZE, DEFAULT_WINDOW_SIZE, InsertionLossStudio，提供本文件后续流程需要的库能力。
from insertion_loss_tool.gui import (
    BASE_MINIMUM_WINDOW_SIZE,
    DEFAULT_WINDOW_SIZE,
    InsertionLossStudio,
)


# Codex说明(自动生成)： 定义 GuiVisualContractTests 类，把相关数据结构、校验规则或操作方法组织在一起。
class GuiVisualContractTests(unittest.TestCase):
    """Observable UI contract shared with the protocol comparison tool."""

    # Codex说明(自动生成)： 定义函数 setUp，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def setUp(self):
        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 self.root，供后续语句继续读取或更新。
            self.root = tk.Tk()
        # Codex说明(自动生成)： 捕获 tk.TclError，执行对应的恢复、记录或重新报错逻辑。
        except tk.TclError as exc:  # pragma: no cover - display-dependent CI boundary
            # Codex说明(自动生成)： 调用 self.skipTest，执行当前流程需要的具体操作或副作用。
            self.skipTest(f"Tk display is unavailable: {exc}")
        # Codex说明(自动生成)： 调用 self.root.withdraw，执行当前流程需要的具体操作或副作用。
        self.root.withdraw()
        # Codex说明(自动生成)： 计算并保存 self.app，供后续语句继续读取或更新。
        self.app = InsertionLossStudio(self.root)
        # A withdrawn window can retain the application's previous 1380x860
        # geometry on Windows. Map it once so the window manager applies the
        # requested pixel geometry before the minimum-size contract is read.
        self.root.deiconify()
        # Codex说明(自动生成)： 调用 self.root.update，执行当前流程需要的具体操作或副作用。
        self.root.update()

    # Codex说明(自动生成)： 定义函数 tearDown，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def tearDown(self):
        # Codex说明(自动生成)： 检查条件 hasattr(self, 'root')，根据结果选择后续执行路径。
        if hasattr(self, "root"):
            # Codex说明(自动生成)： 调用 self.root.destroy，执行当前流程需要的具体操作或副作用。
            self.root.destroy()

    # Codex说明(自动生成)： 定义函数 _visible_texts，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _visible_texts(self, widget):
        # Codex说明(自动生成)： 计算并保存 texts，供后续语句继续读取或更新。
        texts = []
        # Codex说明(自动生成)： 开始执行可能失败的代码块，并把异常、收尾或兜底逻辑交给后续分支处理。
        try:
            # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
            text = widget.cget("text")
        # Codex说明(自动生成)： 捕获 tk.TclError，执行对应的恢复、记录或重新报错逻辑。
        except tk.TclError:
            # Codex说明(自动生成)： 计算并保存 text，供后续语句继续读取或更新。
            text = ""
        # Codex说明(自动生成)： 检查条件 text，根据结果选择后续执行路径。
        if text:
            # Codex说明(自动生成)： 调用 texts.append 更新列表或集合，把当前步骤产生的数据加入结果。
            texts.append(str(text))
        # Codex说明(自动生成)： 遍历 widget.winfo_children() 中的 child，逐项执行循环体逻辑。
        for child in widget.winfo_children():
            # Codex说明(自动生成)： 调用 texts.extend 更新列表或集合，把当前步骤产生的数据加入结果。
            texts.extend(self._visible_texts(child))
        # Codex说明(自动生成)： 返回 texts，让调用方取得本函数的处理结果。
        return texts

    # Codex说明(自动生成)： 定义函数 _assert_inside_root，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def _assert_inside_root(self, widget, *, minimum_width=40, minimum_height=20):
        # Codex说明(自动生成)： 计算并保存 root_left，供后续语句继续读取或更新。
        root_left = self.root.winfo_rootx()
        # Codex说明(自动生成)： 计算并保存 root_top，供后续语句继续读取或更新。
        root_top = self.root.winfo_rooty()
        # Codex说明(自动生成)： 计算并保存 left，供后续语句继续读取或更新。
        left = widget.winfo_rootx() - root_left
        # Codex说明(自动生成)： 计算并保存 top，供后续语句继续读取或更新。
        top = widget.winfo_rooty() - root_top
        # Codex说明(自动生成)： 计算并保存 width，供后续语句继续读取或更新。
        width = widget.winfo_width()
        # Codex说明(自动生成)： 计算并保存 height，供后续语句继续读取或更新。
        height = widget.winfo_height()
        # Codex说明(自动生成)： 调用 self.assertGreaterEqual 检查测试期望，确认实际结果符合预期。
        self.assertGreaterEqual(width, minimum_width, widget)
        # Codex说明(自动生成)： 调用 self.assertGreaterEqual 检查测试期望，确认实际结果符合预期。
        self.assertGreaterEqual(height, minimum_height, widget)
        # Codex说明(自动生成)： 调用 self.assertGreaterEqual 检查测试期望，确认实际结果符合预期。
        self.assertGreaterEqual(left, 0, widget)
        # Codex说明(自动生成)： 调用 self.assertGreaterEqual 检查测试期望，确认实际结果符合预期。
        self.assertGreaterEqual(top, 0, widget)
        # Codex说明(自动生成)： 调用 self.assertLessEqual 检查测试期望，确认实际结果符合预期。
        self.assertLessEqual(left + width, self.root.winfo_width(), widget)
        # Codex说明(自动生成)： 调用 self.assertLessEqual 检查测试期望，确认实际结果符合预期。
        self.assertLessEqual(top + height, self.root.winfo_height(), widget)

    # Codex说明(自动生成)： 定义函数 test_protocol_comparison_palette_and_component_hierarchy，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_protocol_comparison_palette_and_component_hierarchy(self):
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            self.app.colors,
            {
                "bg": "#18192D",
                "panel": "#24253D",
                "panel_alt": "#2A2B47",
                "field": "#191A2D",
                "text": "#F7F5FF",
                "muted": "#AAA6BC",
                "accent": "#8BDEF8",
                "accent_2": "#8273FF",
                "accent_pink": "#EF75BD",
                "line": "#514E6B",
                "danger": "#FF8A9F",
            },
        )
        # Codex说明(自动生成)： 计算并保存 style，供后续语句继续读取或更新。
        style = ttk.Style(self.root)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(style.lookup("Accent.TButton", "background"), "#8BDEF8")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(style.lookup("Secondary.TButton", "background"), "#403F66")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(style.lookup("Card.TFrame", "background"), "#24253D")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(style.lookup("Status.TFrame", "background"), "#20213A")
        # Codex说明(自动生成)： 调用 self.assertTrue 检查测试期望，确认实际结果符合预期。
        self.assertTrue(hasattr(self.app, "brand_mark"))

    # Codex说明(自动生成)： 定义函数 test_main_page_uses_concise_chinese_copy，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_main_page_uses_concise_chinese_copy(self):
        # Codex说明(自动生成)： 计算并保存 texts，供后续语句继续读取或更新。
        texts = self._visible_texts(self.app.generator_page)
        # Codex说明(自动生成)： 遍历 {'插损生成器', '生成', '线性', '协议公式', '手绘', '修改', '扫频', '端口', '... 中的 expected，逐项执行循环体逻辑。
        for expected in {
            "插损生成器",
            "生成",
            "线性",
            "协议公式",
            "手绘",
            "修改",
            "扫频",
            "端口",
            "起始频率",
            "终止频率",
            "点数",
            "输出文件",
            "选择",
            "采样无源 · 宽带因果性未认证",
        }:
            # Codex说明(自动生成)： 调用 self.assertIn 检查测试期望，确认实际结果符合预期。
            self.assertIn(expected, texts)
        # Codex说明(自动生成)： 计算并保存 all_copy，供后续语句继续读取或更新。
        all_copy = "\n".join(texts)
        # Codex说明(自动生成)： 遍历 {'Insertion Loss Studio', 'Model: sampled-passive appro... 中的 removed，逐项执行循环体逻辑。
        for removed in {
            "Insertion Loss Studio",
            "Model: sampled-passive approximation; broadband causality is not certified.",
            "Start frequency",
            "Stop frequency",
            "Through paths",
        }:
            # Codex说明(自动生成)： 调用 self.assertNotIn 检查测试期望，确认实际结果符合预期。
            self.assertNotIn(removed, all_copy)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(
            [button.cget("text") for button in self.app.mode_buttons.values()],
            ["线性", "协议公式", "手绘", "修改"],
        )

    # Codex说明(自动生成)： 定义函数 test_tabs_and_status_are_visually_consistent，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_tabs_and_status_are_visually_consistent(self):
        # Codex说明(自动生成)： 计算并保存 tabs，供后续语句继续读取或更新。
        tabs = [
            self.app.workspace_notebook.tab(tab_id, "text")
            for tab_id in self.app.workspace_notebook.tabs()
        ]
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(tabs, ["常规生成", "图片生成"])
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(self.app.run_button.cget("style"), "Accent.TButton")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(self.app.status_bar.cget("style"), "Status.TFrame")
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(self.app.datasheet_footer.cget("style"), "Status.TFrame")

    # Codex说明(自动生成)： 定义函数 test_datasheet_settings_stack_at_minimum_width，把一段可复用的业务步骤、计算过程或入口逻辑封装起来。
    def test_datasheet_settings_stack_at_minimum_width(self):
        # Codex说明(自动生成)： 计算并保存 minimum_size，供后续语句继续读取或更新。
        minimum_size = self.root.minsize()
        # Codex说明(自动生成)： 计算并保存 required_size，供后续语句继续读取或更新。
        required_size = (self.root.winfo_reqwidth(), self.root.winfo_reqheight())
        # Codex说明(自动生成)： 调用 self.assertLessEqual 检查测试期望，确认实际结果符合预期。
        self.assertLessEqual(required_size[0], DEFAULT_WINDOW_SIZE[0])
        # Codex说明(自动生成)： 调用 self.assertLessEqual 检查测试期望，确认实际结果符合预期。
        self.assertLessEqual(required_size[1], DEFAULT_WINDOW_SIZE[1])
        # Codex说明(自动生成)： 计算并保存 expected_minimum，供后续语句继续读取或更新。
        expected_minimum = tuple(
            min(default, max(base, required))
            for default, base, required in zip(
                DEFAULT_WINDOW_SIZE,
                BASE_MINIMUM_WINDOW_SIZE,
                required_size,
            )
        )
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(minimum_size, expected_minimum)
        # Codex说明(自动生成)： 调用 self.root.geometry，执行当前流程需要的具体操作或副作用。
        self.root.geometry(f"{minimum_size[0]}x{minimum_size[1]}")
        # Codex说明(自动生成)： 调用 self.app.workspace_notebook.select，执行当前流程需要的具体操作或副作用。
        self.app.workspace_notebook.select(self.app.generator_page)
        # Codex说明(自动生成)： 调用 self.root.update_idletasks，执行当前流程需要的具体操作或副作用。
        self.root.update_idletasks()
        # Codex说明(自动生成)： 计算并保存 actual_size，供后续语句继续读取或更新。
        actual_size = (self.root.winfo_width(), self.root.winfo_height())
        # Tk geometry and winfo dimensions use the same client-pixel unit for
        # this non-gridded window, including on DPI-aware Windows builds.
        self.assertEqual(actual_size, minimum_size)
        # Codex说明(自动生成)： 遍历 (self.app.run_button, self.app.controls_canvas, self.ap... 中的 widget，逐项执行循环体逻辑。
        for widget in (
            self.app.run_button,
            self.app.controls_canvas,
            self.app.plot_notebook,
            self.app.status_bar,
        ):
            # Codex说明(自动生成)： 调用 self._assert_inside_root，执行当前流程需要的具体操作或副作用。
            self._assert_inside_root(widget)
        # Codex说明(自动生成)： 调用 self.root.withdraw，执行当前流程需要的具体操作或副作用。
        self.root.withdraw()

        # Codex说明(自动生成)： 调用 self.app.workspace_notebook.select，执行当前流程需要的具体操作或副作用。
        self.app.workspace_notebook.select(self.app.datasheet_page)
        # Codex说明(自动生成)： 调用 self.root.update_idletasks，执行当前流程需要的具体操作或副作用。
        self.root.update_idletasks()
        # Codex说明(自动生成)： 计算并保存 output_grid，供后续语句继续读取或更新。
        output_grid = self.app.datasheet_output_entry.grid_info()
        # Codex说明(自动生成)： 计算并保存 phase_grid，供后续语句继续读取或更新。
        phase_grid = self.app.datasheet_phase_combo.grid_info()
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(int(output_grid["row"]), 2)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(int(output_grid["column"]), 1)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(int(output_grid["columnspan"]), 5)
        # Codex说明(自动生成)： 调用 self.assertEqual 检查测试期望，确认实际结果符合预期。
        self.assertEqual(int(phase_grid["row"]), 3)
        # Codex说明(自动生成)： 遍历 (self.app.datasheet_network_list, self.app.datasheet_re... 中的 widget，逐项执行循环体逻辑。
        for widget in (
            self.app.datasheet_network_list,
            self.app.datasheet_resource_list,
            self.app.datasheet_detail_host,
            self.app.datasheet_output_entry,
            self.app.datasheet_phase_combo,
            self.app.datasheet_footer,
        ):
            # Codex说明(自动生成)： 调用 self._assert_inside_root，执行当前流程需要的具体操作或副作用。
            self._assert_inside_root(widget)


# Codex说明(自动生成)： 检查条件 __name__ == '__main__'，根据结果选择后续执行路径。
if __name__ == "__main__":
    # Codex说明(自动生成)： 调用 unittest.main，执行当前流程需要的具体操作或副作用。
    unittest.main()
