# DL_alchemy

## Installation
- Python 3.X
- PyQt6 6.7.0
- matplotlib

## 用法功能介绍

请以`args_config.py`为例修改你的模型中的包含数据集路径的脚本（使用 `argparse` 模块来解析命令行参数），以便与`DL_alchemy.py`函数绑定并使用加载数据集路径功能。

### 主界面

普通模式：数据集读取支持文件（pt，mat，csv，hcf5格式）/文件夹路径。

![image](https://github.com/JiLiangBOKI/DL_alchemy/assets/142667410/216776c5-58cf-4a5c-a373-d0f520a915c6)

参数修改支持命令行参数，数值型配置以及字典参数。

例如：
```bash
python main.py --dataset_path your_dataset_path
```

运行脚本自动调起`main.py`文件，打印语句会显示到输出框中，特别添加绘图功能，会根据输出语句自动生成epoch为横轴的指标图，汇总和单变量图都有以便可视化观察可视化指标。
![image](https://github.com/JiLiangBOKI/DL_alchemy/assets/142667410/cda91b15-bd0a-4cb7-b7e6-ae5f13728b50)
![image](https://github.com/JiLiangBOKI/DL_alchemy/assets/142667410/0a508d6f-7ba1-43a6-b8be-97f5880f4f03)

### 禅（zen）模式

大大简化了批量处理功能，对于需要处理大量数据，跨源域单被试的繁琐操作。开启开关后，禁用绘图功能，禁用提示框，从而提供更流畅的批处理体验。数据集加载将仅支持文件夹类型，读取后自动转化路径如下图：
![image](https://github.com/JiLiangBOKI/DL_alchemy/assets/142667410/c468c61f-d39b-4d47-a0c9-840994155385)


另外绘制界面，可在此修改参数决定是否使用批量处理功能，{num}会在每一次运行前赋值为1至主界面中的num为方便检查，会输出所有路径在控制台。

修改参数依旧支持上文提及的三种模式，在选择需要配置的py文件后输出新界面。

在勾选前面的禅模式开关后并点击保存后，自动将参数中存在的数值修改为1至num，此处的功能实现并不使用主界面的全局参数num而是使用计数器，以便根据用户需要在脚本中实现不同的参数逻辑修改。

![image](https://github.com/JiLiangBOKI/DL_alchemy/assets/142667410/608bf8fe-3188-4131-b66e-453f09e16db3)


在点击运行脚本后，运行你的模型，在脚本运行结束后不会停止，而是自动按照前面设定好的路径与参数逻辑修改，并再次运行模型，这个过程不需要点击确认即可完成，当然路径会输出在控制台，参数修改会更新在GUI界面以便观察，在次数达到主界面设置的num后会停止运行模型并弹出提示框。

![image](https://github.com/JiLiangBOKI/DL_alchemy/assets/142667410/6e072501-9fd3-4987-8af3-b4f32f67a37f)

### 功能全面
涵盖了数据加载、参数修改、脚本运行、输出显示和结果可视化等各个方面的功能，适用于机器学习模型的训练和调试。

### 用户友好
界面设计简洁直观，用户可以通过按钮和输入框方便地进行各种操作。

### 可扩展性强
通过分离不同的 GUI 类和功能模块，代码结构清晰，易于扩展和维护。

### 支持批处理
禅模式下的批量处理功能，对于需要处理大量数据，跨源域单被试的用户非常实用。

### 代码示例
以下是`args_config.py`的代码示例：

**args_config.py**
```python
# args_config.py

import argparse

def get_args():
    parser = argparse.ArgumentParser(description='Argument Configuration Script')
    parser.add_argument('--dataset_path', type=str, default='path/to/default/dataset', help='Path to the dataset')
    # Add more arguments as needed
    return parser.parse_args()
