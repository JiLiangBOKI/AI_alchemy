import argparse

# 创建 ArgumentParser 对象
parser = argparse.ArgumentParser(description='Process some paths.')
######################## Model parameters ########################
# 添加参数
parser.add_argument('--source_path', default='None', type=str, help='Path to the source training data')
parser.add_argument('--target_path', default='None', type=str, help='Path to the target testing data')
#解析参数
args = parser.parse_args()

print(f"Source Path: {args.source_path}")
print(f"Target Path: {args.target_path}")

# 使用参数
source_path = args.source_path
target_path = args.target_path
# Add your main logic here
# For example, initializing your model, loading data, training, etc.
