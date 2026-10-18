# Python科学计算

## 序言

随着科学技术的发展，计算已经成为研究和工程中不可缺少的一环。数值分析、数据分析、机器学习、仿真等许多领域，都在借助计算的力量。在这些领域中，Python 以简洁的语法、很高的可读性和强大的扩展性，成为科学计算中广泛采用的编程语言。

Python 是一门解释型、面向对象、动态的高级编程语言。它诞生于 20 世纪 90 年代初，长期用于系统管理和 Web 开发，如今在科学计算领域也迅速普及。很多研究机构和大学用 Python 讲授编程，面向科学计算的库也相当丰富。

有代表性的库如下：

- **NumPy**：高速的数组运算
- **SciPy**：数值计算
- **matplotlib**：绘图
- **Pandas**：数据处理
- **scikit-learn**：机器学习
- **OpenCV**：计算机视觉
- **VTK**：3 维可视化

把这些库组合起来，工程师和研究者就能方便地处理实验数据、做可视化，进而开发科学计算的应用。

### 与 MATLAB 的比较

说到科学计算，可能先想到 MATLAB，但 Python 已经是替代 MATLAB 的有力选择。与 MATLAB 相比，Python 的优点如下：

1. **成本**：MATLAB 是商业软件，价格高；Python 可以免费使用。
2. **可读性与易学性**：Python 的语法更严谨、可读性更高，学习和维护都容易。
3. **通用性**：Python 不只做科学计算，还能做文件管理、GUI 开发、网络通信等广泛的用途。

### 本书的目的

本书按从基础到应用的顺序编排，让读者系统地学习用 Python 做科学计算。重点介绍用主要库做数据处理和可视化的方法，并通过与 MATLAB 的比较，探讨用 Python 做科学计算的有效方式。

希望读者读完本书后，能够把 Python 用到科学计算的实际工作里。无论是初学者还是进阶读者，只要对用 Python 做计算感兴趣，都能从这本书里得到帮助。

## 安装 Python 环境

管理科学计算的库，常用 `conda`；它有一个轻量又快速的替代品 `micromamba`。`micromamba` 用 C++ 实现，创建环境和安装包都很快。它只有单个可执行文件，安装很简单。

`micromamba` 与 `conda` 保持兼容，同时做到快速、轻量的环境管理。想高效利用计算资源、或者想要轻量环境的人，可以把它作为一个选择。另外，有些库只提供 `pip` 包，那时要用 `pip install` 补上。

### 安装 `micromamba`

从 [micromamba 官方页面](https://mamba.readthedocs.io/en/latest/installation.html) 下载 Windows 版的可执行文件。把下载的 ZIP 解压到一个合适的文件夹（例如 `C:\micromamba\`）。

[micromamba 的 release 页面](https://github.com/mamba-org/micromamba-releases/releases)

接下来把 `C:\micromamba` 加到系统环境变量 `PATH` 里。在 `cmd.exe` 中用下面的命令初始化 `micromamba`。

```cmd
micromamba shell init -s cmd.exe -p C:\micromamba
```

### 创建 Python 环境

创建 Python 环境时，先重新打开命令提示符，再执行下面的命令。`-n myenv` 把环境名指定为 `myenv`。

```cmd
micromamba create -n myenv
```

要启用创建好的环境，执行下面的命令。

```cmd
micromamba activate myenv
```

环境处于启用状态时，用下面的命令安装本书提供的 `requirements_conda.txt` 里的全部库。

```cmd
micromamba install --file requirements_conda.txt 
```

本书用到的 `graphviz` 库，用下面的命令安装。

```cmd
pip install graphviz
```

```{tableofcontents}
```
