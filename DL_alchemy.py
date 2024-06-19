import sys
import re
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QLineEdit, \
    QLabel, QSpinBox, QMessageBox, QCheckBox, QTabWidget, QSizePolicy, QTextEdit, QInputDialog, QProgressBar, \
    QHBoxLayout
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
import subprocess
import ast
from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt
import matplotlib

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False  # 用于正常显示负号




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
                                if isinstance(target, ast.Attribute) and isinstance(target.value,
                                                                                    ast.Name) and target.value.id == 'self':
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


def get_dict_attributes(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)

    dict_attrs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'parameter' and isinstance(node.value, ast.Dict):
                    for key, value in zip(node.value.keys, node.value.values):
                        if isinstance(key, ast.Str):
                            key_str = key.s
                            if isinstance(value, ast.Constant):
                                dict_attrs[key_str] = value.value
                            elif isinstance(value, ast.Num):
                                dict_attrs[key_str] = value.n
                            elif isinstance(value, ast.Str):
                                dict_attrs[key_str] = value.s
    return dict_attrs


class ArgParseGUI(QWidget):
    def __init__(self, argparse_args, file_path, zen_mode=False):
        super().__init__()
        self.argparse_args = argparse_args
        self.file_path = file_path
        self.zen_mode = zen_mode  # Add zen_mode flag
        self.counter = 0  # 初始化计数器
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget(self)
        layout.addWidget(self.tab_widget)

        self.input_fields = {}
        self.switch_buttons = {}
        tab_count = 0
        args_per_tab = 10  # 每个选项卡包含的参数数量

        for i in range(0, len(self.argparse_args), args_per_tab):
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            for arg in self.argparse_args[i:i + args_per_tab]:
                row_layout = QHBoxLayout()

                switch = QCheckBox(f"zen")
                switch.setChecked(False)  # 默认不勾选
                self.switch_buttons[arg['name']] = switch
                row_layout.addWidget(switch)

                label = QLabel(f"{arg['name']} ({arg['type']}): {arg['help']}")
                label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                row_layout.addWidget(label)

                input_field = QLineEdit(self)
                input_field.setText(str(arg['default']))
                row_layout.addWidget(input_field)

                self.input_fields[arg['name']] = input_field
                tab_layout.addLayout(row_layout)

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
            if self.switch_buttons[arg['name']].isChecked():
                input_text = self.input_fields[arg['name']].text()
                new_text = re.sub(r'\d+', str(self.counter), input_text)
                self.input_fields[arg['name']].setText(new_text)
            else:
                new_text = self.input_fields[arg['name']].text()
            arg['default'] = new_text
        self.update_file()
        if not self.zen_mode:  # Only show message box if not in zen mode
            QMessageBox.information(self, '信息', '参数更新成功!')
        self.counter += 1  # Increase counter


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


class ConfigGUI(QWidget):
    def __init__(self, config_attrs, file_path, zen_mode=False):
        super().__init__()
        self.config_attrs = config_attrs
        self.file_path = file_path
        self.zen_mode = zen_mode  # Add zen_mode flag
        self.counter = 0  # 初始化计数器
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget(self)
        layout.addWidget(self.tab_widget)

        self.input_fields = {}
        self.switch_buttons = {}
        tab_count = 0
        attrs_per_tab = 10  # 每个选项卡包含的属性数量

        for i in range(0, len(self.config_attrs), attrs_per_tab):
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            for attr, value in list(self.config_attrs.items())[i:i + attrs_per_tab]:
                row_layout = QHBoxLayout()

                switch = QCheckBox(f"zen")
                switch.setChecked(False)  # 默认不勾选
                self.switch_buttons[attr] = switch
                row_layout.addWidget(switch)

                label = QLabel(f"{attr}:")
                label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                row_layout.addWidget(label)

                input_field = QLineEdit(self)
                input_field.setText(str(value))
                row_layout.addWidget(input_field)

                self.input_fields[attr] = input_field
                tab_layout.addLayout(row_layout)

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
            if self.switch_buttons[attr].isChecked():
                input_text = self.input_fields[attr].text()
                new_text = re.sub(r'\d+', str(self.counter), input_text)
                self.input_fields[attr].setText(new_text)
                self.config_attrs[attr] = new_text
        self.update_file()
        if not self.zen_mode:  # Only show message box if not in zen mode
            QMessageBox.information(self, '信息', '配置更新成功!')
        self.counter += 1  # Increase counter

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


class DictGUI(QWidget):
    def __init__(self, dict_attrs, file_path, zen_mode=False):
        super().__init__()
        self.dict_attrs = dict_attrs
        self.file_path = file_path
        self.zen_mode = zen_mode  # Add zen_mode flag
        self.counter = 0  # 初始化计数器
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget(self)
        layout.addWidget(self.tab_widget)

        self.input_fields = {}
        self.switch_buttons = {}
        tab_count = 0
        attrs_per_tab = 10  # 每个选项卡包含的属性数量

        for i in range(0, len(self.dict_attrs), attrs_per_tab):
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            for attr, value in list(self.dict_attrs.items())[i:i + attrs_per_tab]:
                row_layout = QHBoxLayout()

                switch = QCheckBox(f"zen")
                switch.setChecked(False)  # 默认不勾选
                self.switch_buttons[attr] = switch
                row_layout.addWidget(switch)

                label = QLabel(f"{attr}:")
                label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                row_layout.addWidget(label)

                input_field = QLineEdit(self)
                input_field.setText(str(value))
                row_layout.addWidget(input_field)

                self.input_fields[attr] = input_field
                tab_layout.addLayout(row_layout)

            self.tab_widget.addTab(tab, f"字典组 {tab_count + 1}")
            tab_count += 1

        save_button = QPushButton('保存', self)
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

        self.setLayout(layout)
        self.setWindowTitle('Dict GUI')
        self.show()

    def save_changes(self):
        for attr in self.dict_attrs:
            if self.switch_buttons[attr].isChecked():
                input_text = self.input_fields[attr].text()
                new_text = re.sub(r'\d+', str(self.counter), input_text)
                self.input_fields[attr].setText(new_text)
                self.dict_attrs[attr] = new_text
        self.update_file()
        if not self.zen_mode:  # Only show message box if not in zen mode
            QMessageBox.information(self, '信息', '字典参数更新成功!')
        self.counter += 1  # Increase counter

    def update_file(self):
        with open(self.file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        new_lines = []
        in_dict = False
        for line in lines:
            new_line = line
            if 'parameter = {' in line:
                in_dict = True
            elif in_dict and '}' in line:
                in_dict = False
            elif in_dict:
                for attr, value in self.dict_attrs.items():
                    if f"'{attr}':" in line:
                        before_colon, rest = line.split(':', 1)
                        after_colon = rest.split(',', 1)[1] if ',' in rest else ''
                        new_value = f"'{value}'" if isinstance(value, str) else value
                        new_line = f"{before_colon}: {new_value},{after_colon}\n"
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
            ["python", self.script_path, "--source_path", self.train_data_path, "--target_path", self.test_data_path,
             "--subset", "True"],
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

        self.zen_mode_checkbox = QCheckBox("禅模式", self)
        self.zen_mode_checkbox.setToolTip("启用禅模式（禁用绘图功能）")

        # 添加全局num设置
        self.num_label = QLabel("Specify num:")
        self.num_input = QSpinBox()
        self.num_input.setMinimum(1)
        self.num_input.setValue(1)  # 默认值设为1

        button_layout.addWidget(self.button_load_train_data)
        button_layout.addWidget(self.button_load_test_data)
        button_layout.addWidget(self.button_run_script)
        button_layout.addWidget(self.button_modify_args)
        button_layout.addWidget(self.zen_mode_checkbox)
        button_layout.addWidget(self.num_label)
        button_layout.addWidget(self.num_input)

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
        if self.zen_mode_checkbox.isChecked():
            self.load_zen_mode_train_data()
        else:
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
        if self.zen_mode_checkbox.isChecked():
            self.load_zen_mode_test_data()
        else:
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

    def load_zen_mode_train_data(self):
        self.zen_mode_train_app = ZenModeApp(self, "train")
        self.zen_mode_train_app.show()

    def load_zen_mode_test_data(self):
        self.zen_mode_test_app = ZenModeApp(self, "test")
        self.zen_mode_test_app.show()

    def set_train_data_path(self, path):
        self.train_data_path = path
        self.label_info.setText(f"训练数据加载自: {self.train_data_path}")

    def set_test_data_path(self, path):
        self.test_data_path = path
        self.label_info.setText(f"测试数据加载自: {self.test_data_path}")

    def run_script(self):
        if self.train_data_path and self.test_data_path:
            script_path = "main.py"  # 修改为你要运行的脚本路径

            # 每次运行脚本前更新参数并增加计数器的值
            if self.zen_mode_checkbox.isChecked():
                self.modify_zen_args_counter()

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
            if not self.zen_mode_checkbox.isChecked():
                self.extract_and_plot_metrics()
            else:
                self.run_next_iteration()

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
        if self.zen_mode_checkbox.isChecked():
            self.modify_zen_args()
        else:
            option, ok = QInputDialog.getItem(self, "选择选项", "你想修改什么类型的参数？",
                                              ["命令行参数", "数值型配置文件", "字典参数"], 0, False)
            if ok and option:
                if option == "命令行参数":
                    file_dialog = QFileDialog()
                    file_dialog.setNameFilter("Python 文件 (*.py)")
                    if file_dialog.exec():
                        filenames = file_dialog.selectedFiles()
                        if filenames:
                            script_path = filenames[0]
                            argparse_args = get_argparse_args(script_path)
                            self.argparse_gui = ArgParseGUI(argparse_args, script_path, self.zen_mode_checkbox.isChecked())
                            self.argparse_gui.show()
                elif option == "数值型配置文件":
                    file_dialog = QFileDialog()
                    file_dialog.setNameFilter("Python 文件 (*.py)")
                    if file_dialog.exec():
                        filenames = file_dialog.selectedFiles()
                        if filenames:
                            config_path = filenames[0]
                            config_attrs = get_config_attributes(config_path)
                            self.config_gui = ConfigGUI(config_attrs, config_path, self.zen_mode_checkbox.isChecked())
                            self.config_gui.show()
                elif option == "字典参数":
                    file_dialog = QFileDialog()
                    file_dialog.setNameFilter("Python 文件 (*.py)")
                    if file_dialog.exec():
                        filenames = file_dialog.selectedFiles()
                        if filenames:
                            dict_path = filenames[0]
                            dict_attrs = get_dict_attributes(dict_path)
                            self.dict_gui = DictGUI(dict_attrs, dict_path, self.zen_mode_checkbox.isChecked())
                            self.dict_gui.show()

    def modify_zen_args(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Python 文件 (*.py)")
        if file_dialog.exec():
            filenames = file_dialog.selectedFiles()
            if filenames:
                script_path = filenames[0]
                argparse_args = get_argparse_args(script_path)
                self.argparse_gui = ArgParseGUI(argparse_args, script_path, True)
                self.argparse_gui.show()

    def modify_zen_args_counter(self):
        if hasattr(self, 'argparse_gui') and self.argparse_gui.isVisible():
            self.argparse_gui.save_changes()

    def run_next_iteration(self):
        next_train_path = next_test_path = None

        if self.zen_mode_train_app and self.zen_mode_train_app.next_paths:
            next_train_path = self.zen_mode_train_app.next_paths.pop(0)
            self.set_train_data_path(next_train_path)

        if self.zen_mode_test_app and self.zen_mode_test_app.next_paths:
            next_test_path = self.zen_mode_test_app.next_paths.pop(0)
            self.set_test_data_path(next_test_path)

        if next_train_path and next_test_path:
            self.run_script()
        else:
            QMessageBox.information(self, "运行完成", "所有路径都已处理完毕。")


class ZenModeApp(QWidget):
    def __init__(self, main_window, data_type):
        super().__init__()
        self.main_window = main_window
        self.data_type = data_type
        self.next_paths = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Zen Mode Data Loader")
        self.setGeometry(200, 200, 400, 200)

        layout = QVBoxLayout()

        self.load_button = QPushButton("Load Dataset Folder")
        self.load_button.clicked.connect(self.load_dataset)
        layout.addWidget(self.load_button)

        self.path_label = QLabel("Dataset Path Template:")
        self.path_input = QLineEdit()
        layout.addWidget(self.path_label)
        layout.addWidget(self.path_input)

        self.modify_button = QPushButton("Modify Path")
        self.modify_button.clicked.connect(self.modify_path)
        layout.addWidget(self.modify_button)

        self.setLayout(layout)

    def load_dataset(self):
        dataset_dir = QFileDialog.getExistingDirectory(self, "Open Dataset Folder", "")
        if dataset_dir:
            self.dataset_dir = dataset_dir
            modified_path = self.create_path_template(self.dataset_dir)
            self.path_input.setText(modified_path)
            print(f"Loaded dataset directory: {self.dataset_dir}")
            print(f"Path template: {modified_path}")

    def create_path_template(self, path):
        path_template = re.sub(r'(\d+)', r'{num}', path)
        return path_template

    def modify_path(self):
        path_template = self.path_input.text()
        num = self.main_window.num_input.value()
        self.next_paths = self.replace_numbers_in_path(path_template, num)
        print("Modified paths:")
        for path in self.next_paths:
            print(path)
        if self.next_paths:
            if self.data_type == "train":
                self.main_window.set_train_data_path(self.next_paths.pop(0))
            else:
                self.main_window.set_test_data_path(self.next_paths.pop(0))

    def replace_numbers_in_path(self, path, num):
        return [path.format(num=i) for i in range(1, num + 1)]


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
