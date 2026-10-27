# HW6 运行与提交说明

1. 在本文件所在文件夹打开 VS Code 终端，先安装依赖：

```bash
python -m pip install -r requirements.txt
```

2. 打开 `hw6_interest_rate_products.ipynb`，选择 Python 3.11 内核。点击 Restart，再点击 Run All。
3. 17 个代码单元运行完成后，按 Ctrl + S 保存输出。
4. 在同一文件夹的终端运行：

```bash
python verify_assignment6.py
```

应显示 6 行 PASS。主要现值约为：
- FRA：87.090294
- RFR swap：-2629.679575
- Overnight basis swap：8446.472471

`fixedincomelib` 内的模块由 Notebook 自动调用，不用逐个运行。
`Part_I_Answers.pdf` 是理论题英文答案，包含三道小问。

## GitHub
按 HW5 的流程 Fork HW6 仓库、克隆并创建 `Chuyu_Wu_Branch`。将本文件夹内的内容复制到克隆仓库根目录，覆盖对应文件，不要嵌套整个外层文件夹。Commit 后 Publish branch / Push origin。

老师的仓库：
https://github.com/Jerry0108-SJ/FRE-GY-9743-Assignments-6

上传到 GitHub 后，仍需按课程要求在提交入口填写链接或进行其他提交步骤。
