# Pythonで科学計算

https://ruoyu0088.github.io/scipybook

## 使い方（日本語）

両言語で共通の資産は `shared/`（`helper/`, `data/`, `images/`, `_static/`）にあります。
各言語のディレクトリにある同名のディレクトリは、ビルド前にコピーされる生成物で、Git では管理していません。

### ノートブックを実行する

```bash
python sync_assets.py --apply --all
cd scipybook
jupyter lab
```

中国語版を動かす場合は、`cd scipybook` を `cd scipybook_cn` に読み替えてください。

- Jupyter は必ず本のディレクトリで起動してください。notebook の `data/...`、`images/...`、`import helper` はカレントディレクトリ基準です。
- 実行に必要なパッケージは `scipybook/requirements_conda.txt` にまとまっています（`index.md` の micromamba 手順を参照）。
- `requirements.txt` はビルド用で、実行用ではありません。

### ビルド

```bash
python sync_assets.py --apply --all
jupyter-book build scipybook
jupyter-book build scipybook_cn
```

### 資産の変更

`shared/` だけを編集し、`python sync_assets.py --apply --all` を実行してください。
`python sync_assets.py --check` で同期ずれを確認できます。

## 使用说明（中文）

两种语言共用的资源放在 `shared/`（`helper/`、`data/`、`images/`、`_static/`）。
各语言目录下的同名目录是构建前复制的生成物，不纳入 Git。

### 运行 notebook

```bash
python sync_assets.py --apply --all
cd scipybook_cn
jupyter lab
```

日文版把 `cd scipybook_cn` 换成 `cd scipybook`。

- Jupyter 必须从书目录启动，notebook 里的 `data/...`、`images/...` 和 `import helper` 都按当前目录解析。
- 运行依赖汇总在 `scipybook/requirements_conda.txt`，安装步骤见 `index.md` 里的 micromamba 说明。
- `requirements.txt` 只用于构建站点，不包含运行依赖。

### 构建

```bash
python sync_assets.py --apply --all
jupyter-book build scipybook
jupyter-book build scipybook_cn
```

### 修改资源

只修改 `shared/`，然后运行 `python sync_assets.py --apply --all`。
`python sync_assets.py --check` 可以检查是否同步。
