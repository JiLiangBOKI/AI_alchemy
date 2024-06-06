import ast
import os
import sys
import subprocess
import re
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, \
    QFileDialog, QProgressBar, QMessageBox, QTextEdit, QInputDialog, QLineEdit, QTabWidget, QSizePolicy
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPalette


def get_argparse_args(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)

    argparse_args = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, 'attr', None) == 'add_argument':
            kwargs = {kw.arg: kw.value for kw in node.keywords}
            args = [arg.s for arg in node.args if isinstance(arg, ast.Str)]
            arg_info = {
                'name': args[0] if args else '',
                'default': None,
                'type': 'str',
                'help': ''
            }
            if 'default' in kwargs:
                if isinstance(kwargs['default'], ast.Constant):
                    arg_info['default'] = kwargs['default'].value
                elif isinstance(kwargs['default'], ast.Str):
                    arg_info['default'] = kwargs['default'].s
                elif isinstance(kwargs['default'], ast.Num):
                    arg_info['default'] = kwargs['default'].n
            if 'type' in kwargs:
                if isinstance(kwargs['type'], ast.Name):
                    arg_info['type'] = kwargs['type'].id
            if 'help' in kwargs:
                if isinstance(kwargs['help'], ast.Str):
                    arg_info['help'] = kwargs['help'].s
            argparse_args.append(arg_info)
    return argparse_args


class ArgParseGUI(QWidget):
    def __init__(self, argparse_args, file_path):
        super().__init__()
        self.argparse_args = argparse_args
        self.file_path = file_path
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget(self)
        layout.addWidget(self.tab_widget)

        self.input_fields = {}
        tab_count = 0
        args_per_tab = 10  # 每个选项卡包含的参数数量

        for i in range(0, len(self.argparse_args), args_per_tab):
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            for arg in self.argparse_args[i:i + args_per_tab]:
                label = QLabel(f"{arg['name']} ({arg['type']}): {arg['help']}")
                label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                tab_layout.addWidget(label)
                input_field = QLineEdit(self)
                input_field.setText(str(arg['default']))
                tab_layout.addWidget(input_field)
                self.input_fields[arg['name']] = input_field
            self.tab_widget.addTab(tab, f"参数组 {tab_count + 1}")
            tab_count += 1

        save_button = QPushButton('保存', self)
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

        self.setLayout(layout)
        self.setWindowTitle('ArgParse GUI')
        self.show()

    def save_changes(self):
        for arg in self.argparse_args:
            arg['default'] = self.input_fields[arg['name']].text()
        self.update_file()
        QMessageBox.information(self, '信息', '参数更新成功!')

    def update_file(self):
        with open(self.file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        new_lines = []
        for line in lines:
            new_line = line
            for arg in self.argparse_args:
                if f"'{arg['name']}'" in line and 'default=' in line:
                    new_line = self.update_line(line, arg)
            new_lines.append(new_line)

        with open(self.file_path, 'w', encoding='utf-8') as file:
            file.writelines(new_lines)

    def update_line(self, line, arg):
        before_default, rest = line.split('default=', 1)
        after_default = rest.split(',', 1)[1] if ',' in rest else ''
        new_default = f"'{arg['default']}'" if arg['type'] == 'str' else arg['default']
        new_line = f"{before_default}default={new_default},{after_default}"
        return new_line


def get_config_attributes(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)

    config_attrs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'Config':
            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef) and body_item.name == '__init__':
                    for stmt in body_item.body:
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                    attr_name = target.attr
                                    if isinstance(stmt.value, ast.Constant):
                                        attr_value = stmt.value.value
                                    elif isinstance(stmt.value, ast.Num):
                                        attr_value = stmt.value.n
                                    elif isinstance(stmt.value, ast.Str):
                                        attr_value = stmt.value.s
                                    else:
                                        attr_value = None
                                    config_attrs[attr_name] = attr_value
    return config_attrs


class ConfigGUI(QWidget):
    def __init__(self, config_attrs, file_path):
        super().__init__()
        self.config_attrs = config_attrs
        self.file_path = file_path
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget(self)
        layout.addWidget(self.tab_widget)

        self.input_fields = {}
        tab_count = 0
        attrs_per_tab = 10  # 每个选项卡包含的属性数量

        for i in range(0, len(self.config_attrs), attrs_per_tab):
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            for attr, value in list(self.config_attrs.items())[i:i + attrs_per_tab]:
                label = QLabel(f"{attr}:")
                label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                tab_layout.addWidget(label)
                input_field = QLineEdit(self)
                input_field.setText(str(value))
                tab_layout.addWidget(input_field)
                self.input_fields[attr] = input_field
            self.tab_widget.addTab(tab, f"配置组 {tab_count + 1}")
            tab_count += 1

        save_button = QPushButton('保存', self)
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

        self.setLayout(layout)
        self.setWindowTitle('Config GUI')
        self.show()

    def save_changes(self):
        for attr in self.config_attrs:
            self.config_attrs[attr] = self.input_fields[attr].text()
        self.update_file()
        QMessageBox.information(self, '信息', '配置更新成功!')

    def update_file(self):
        with open(self.file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        new_lines = []
        in_init = False
        for line in lines:
            new_line = line
            if 'def __init__(self' in line:
                in_init = True
            elif in_init and line.strip().startswith('self.') and '=' in line:
                for attr, value in self.config_attrs.items():
                    if f'self.{attr}' in line:
                        parts = line.split('=')
                        before_equals = parts[0]
                        new_line = f"{before_equals}= {value}\n"
            elif in_init and line.strip().startswith('self.') and not '=' in line:
                in_init = False
            new_lines.append(new_line)

        with open(self.file_path, 'w', encoding='utf-8') as file:
            file.writelines(new_lines)


class ScriptRunner(QThread):
    output = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, script_path, train_data_path, test_data_path):
        super().__init__()
        self.script_path = script_path
        self.train_data_path = train_data_path
        self.test_data_path = test_data_path

    def run(self):
        process = subprocess.Popen(
            ["python", self.script_path, "--source_path", self.train_data_path, "--target_path", self.test_data_path, "--subset", "True"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding='utf-8'
        )

        for line in process.stdout:
            self.output.emit(line)
        for line in process.stderr:
            self.output.emit(line)

        process.stdout.close()
        process.stderr.close()
        return_code = process.wait()
        self.finished.emit(return_code)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ai_alchemy")
        self.setGeometry(100, 100, 1000, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        top_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        self.button_load_train_data = QPushButton("加载训练数据", self)
        self.button_load_train_data.setToolTip("点击加载训练数据")
        self.button_load_train_data.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button_load_train_data.setStyleSheet(
            "background-color: #4CAF50; color: white; border-radius: 5px; padding: 5px;")

        self.button_load_test_data = QPushButton("加载测试数据", self)
        self.button_load_test_data.setToolTip("点击加载测试数据")
        self.button_load_test_data.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button_load_test_data.setStyleSheet(
            "background-color: #FFC107; color: white; border-radius: 5px; padding: 5px;")

        self.button_run_script = QPushButton("运行脚本", self)
        self.button_run_script.setToolTip("点击运行脚本")
        self.button_run_script.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button_run_script.setStyleSheet(
            "background-color: #008CBA; color: white; border-radius: 5px; padding: 5px;")

        self.button_modify_args = QPushButton("修改参数", self)
        self.button_modify_args.setToolTip("点击修改参数")
        self.button_modify_args.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button_modify_args.setStyleSheet(
            "background-color: #9C27B0; color: white; border-radius: 5px; padding: 5px;")

        button_layout.addWidget(self.button_load_train_data)
        button_layout.addWidget(self.button_load_test_data)
        button_layout.addWidget(self.button_run_script)
        button_layout.addWidget(self.button_modify_args)

        top_layout.addLayout(button_layout)

        self.label_info = QLabel("尚未加载数据", self)
        self.label_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self.label_info)

        self.layout.addLayout(top_layout)

        self.label_separator = QLabel("------------------------------", self)
        self.label_separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label_separator)

        bottom_layout = QVBoxLayout()

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setStyleSheet(
            "QProgressBar {border: 2px solid grey; border-radius: 5px; background-color: #f0f0f0;}"
            "QProgressBar::chunk {background-color: #4CAF50;}")
        bottom_layout.addWidget(self.progress_bar)

        self.output_text = QTextEdit(self)
        self.output_text.setReadOnly(True)
        bottom_layout.addWidget(self.output_text, 1)

        self.layout.addLayout(bottom_layout)

        self.train_data_path = None
        self.test_data_path = None
        self.outputs = []

        self.button_load_train_data.clicked.connect(self.load_train_data)
        self.button_load_test_data.clicked.connect(self.load_test_data)
        self.button_run_script.clicked.connect(self.run_script)
        self.button_modify_args.clicked.connect(self.modify_args)

    def load_train_data(self):
        option, ok = QInputDialog.getItem(self, "选择选项", "你想加载文件还是文件夹？",
                                          ["文件", "文件夹"], 0, False)
        if ok and option:
            if option == "文件":
                file_dialog = QFileDialog()
                file_dialog.setNameFilter("数据文件 (*.pt *.mat *.csv *.hdf5)")
                if file_dialog.exec():
                    filenames = file_dialog.selectedFiles()
                    if filenames:
                        self.train_data_path = filenames[0]
                        self.label_info.setText(f"训练数据加载自: {self.train_data_path}")
            elif option == "文件夹":
                dir_dialog = QFileDialog()
                dir_dialog.setFileMode(QFileDialog.FileMode.Directory)
                if dir_dialog.exec():
                    directories = dir_dialog.selectedFiles()
                    if directories:
                        self.train_data_path = directories[0]
                        self.label_info.setText(f"训练数据加载自: {self.train_data_path}")

    def load_test_data(self):
        option, ok = QInputDialog.getItem(self, "选择选项", "你想加载文件还是文件夹？",
                                          ["文件", "文件夹"], 0, False)
        if ok and option:
            if option == "文件":
                file_dialog = QFileDialog()
                file_dialog.setNameFilter("数据文件 (*.pt *.mat *.csv *.hdf5)")
                if file_dialog.exec():
                    filenames = file_dialog.selectedFiles()
                    if filenames:
                        self.test_data_path = filenames[0]
                        self.label_info.setText(f"测试数据加载自: {self.test_data_path}")
            elif option == "文件夹":
                dir_dialog = QFileDialog()
                dir_dialog.setFileMode(QFileDialog.FileMode.Directory)
                if dir_dialog.exec():
                    directories = dir_dialog.selectedFiles()
                    if directories:
                        self.test_data_path = directories[0]
                        self.label_info.setText(f"测试数据加载自: {self.test_data_path}")

    def run_script(self):
        if self.train_data_path and self.test_data_path:
            script_path = "main.py"  # 修改为你要运行的脚本路径
            self.script_runner = ScriptRunner(script_path, self.train_data_path, self.test_data_path)
            self.script_runner.output.connect(self.append_output)
            self.script_runner.finished.connect(self.on_script_finished)
            self.script_runner.start()
        else:
            QMessageBox.warning(self, "未加载数据",
                                "请先加载训练和测试数据，然后再运行脚本。")

    def append_output(self, text):
        self.outputs.append(text)
        self.output_text.append(text)

    def on_script_finished(self, return_code):
        if return_code != 0:
            QMessageBox.warning(self, "脚本错误", "脚本运行时出现错误，请检查输出信息。")
        else:
            QMessageBox.information(self, "脚本执行", "脚本已完成运行。")
            self.extract_and_plot_metrics()

    def extract_and_plot_metrics(self):
        full_output = "\n".join(self.outputs)

        epoch_pattern = re.compile(r'Epoch\s*[:=]\s*(\d+)')
        metric_pattern = re.compile(r'([a-zA-Z_ ]+)\s*[:=]\s*([\d.]+)')

        metrics = {}
        epochs = []

        for line in full_output.split("\n"):
            epoch_match = epoch_pattern.search(line)
            if epoch_match:
                epoch = int(epoch_match.group(1))
                epochs.append(epoch)
                continue

            for match in metric_pattern.finditer(line):
                key, value = match.groups()
                key = key.strip().replace(" ", "_")
                if key not in metrics:
                    metrics[key] = []
                metrics[key].append(float(value))

        metrics = {k: v for k, v in metrics.items() if len(v) > 1}

        self.plot_combined_metrics(epochs, metrics)
        self.plot_separate_metrics(epochs, metrics)

    def plot_combined_metrics(self, epochs, metrics):
        plt.figure(figsize=(10, 6))
        for key, values in metrics.items():
            if len(values) == len(epochs):
                plt.plot(epochs, values, label=key)

        plt.xlabel('Epoch')
        plt.ylabel('Metrics')
        plt.title('训练和测试指标')

        step = max(1, len(epochs) // 10)
        plt.xticks(epochs[::step])

        plt.legend()
        plt.tight_layout()
        plt.show()

    def plot_separate_metrics(self, epochs, metrics):
        num_metrics = len(metrics)
        num_cols = 2
        num_rows = (num_metrics + 1) // num_cols

        fig, axes = plt.subplots(num_rows, num_cols, figsize=(8, 4 * num_rows))
        axes = axes.flatten()

        for idx, (key, values) in enumerate(metrics.items()):
            if len(values) == len(epochs):
                axes[idx].plot(epochs, values, label=key)
                axes[idx].set_xlabel('Epoch')
                axes[idx].set_ylabel(key)
                axes[idx].set_title(key)

                step = max(1, len(epochs) // 10)
                axes[idx].set_xticks(epochs[::step])

                axes[idx].legend()

        for i in range(num_metrics, len(axes)):
            fig.delaxes(axes[i])

        plt.tight_layout()
        plt.show()

    def modify_args(self):
        option, ok = QInputDialog.getItem(self, "选择选项", "你想修改什么类型的参数？",
                                          ["命令行参数", "数值型配置文件"], 0, False)
        if ok and option:
            if option == "命令行参数":
                file_dialog = QFileDialog()
                file_dialog.setNameFilter("Python 文件 (*.py)")
                if file_dialog.exec():
                    filenames = file_dialog.selectedFiles()
                    if filenames:
                        script_path = filenames[0]
                        argparse_args = get_argparse_args(script_path)
                        self.argparse_gui = ArgParseGUI(argparse_args, script_path)
                        self.argparse_gui.show()
            elif option == "数值型配置":
                file_dialog = QFileDialog()
                file_dialog.setNameFilter("Python 文件 (*.py)")
                if file_dialog.exec():
                    filenames = file_dialog.selectedFiles()
                    if filenames:
                        config_path = filenames[0]
                        config_attrs = get_config_attributes(config_path)
                        self.config_gui = ConfigGUI(config_attrs, config_path)
                        self.config_gui.show()


def main():
    app = QApplication(sys.argv)

    app.setStyle("Fusion")
    dark_palette = app.palette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(142, 45, 197).lighter())
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(dark_palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
