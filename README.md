# Web to Presentation Converter

将 HTML 网页报告转换为高清图片和 PowerPoint 演示文稿的自动化工具。

## 功能特性

- ✅ **高保真渲染**：使用 Playwright 无头浏览器，完美还原网页样式
- ✅ **图表支持**：完整支持 Chart.js 等动态图表库
- ✅ **高分辨率**：输出 300 DPI × 3 倍缩放的高清图片（900 DPI）
- ✅ **按页分割**：自动识别 `.page` 元素，每页单独输出
- ✅ **自动化 PPT**：将图片自动组装成 PowerPoint 文件
- ✅ **批量处理**：支持同时转换多个 HTML 文件
- ✅ **自动扫描**：自动识别根目录及子目录下的所有 HTML 文件，无需手动配置

## 系统要求

- **Node.js** 16+
- **Python** 3.8+
- **npm** 或 **yarn**
- **pip3**

## 快速开始

### 1. 准备 HTML 文件

将需要转换的 HTML 文件或包含 HTML 文件的项目文件夹放到本项目的根目录下。例如：

```
web_to_presentation/
├── 报告1.html
├── 报告2.html
├── my_project/
│   ├── index.html
│   └── report.html
└── ...
```

脚本会**自动扫描**根目录及所有子目录下的 HTML 文件，无需手动配置！

### 2. 运行转换

最简单的方式是使用一键转换脚本（会自动安装依赖）：

```bash
chmod +x convert.sh
./convert.sh
```

或者手动安装依赖后运行：

```bash
# 安装 Node.js 依赖
npm install

# 安装 Python 依赖
pip3 install -r requirements.txt

# 运行转换
./convert.sh
```

### 3. 查看输出

转换完成后，文件将保存在：

- **图片**：`output/images/` 目录
- **PPT**：`output/` 目录下的 `.pptx` 文件

## 使用方法

### 完整流程（HTML → 图片 → PPT）

```bash
./convert.sh
```

### 仅生成图片

```bash
./convert.sh --images-only
```

### 仅生成 PPT（需要先有图片）

```bash
./convert.sh --ppt-only
```

### 分步执行

#### 步骤 1：HTML 转图片

```bash
node src/html-to-images.js
```

#### 步骤 2：图片转 PPT

```bash
python3 src/images-to-ppt.py
```

## 配置说明

### HTML 文件扫描

脚本会**自动扫描**以下位置的 HTML 文件：
- 项目根目录下的所有 `.html` 文件
- 所有子目录下的 `.html` 文件

**自动排除**以下目录（不会扫描）：
- `node_modules/`
- `output/`
- `.git/`
- `dist/`
- `build/`

如需修改扫描规则，可以在 `src/html-to-images.js` 中调整：

```javascript
const CONFIG = {
  // 扫描模式
  scanPatterns: [
    path.join(__dirname, '../*.html'),           // 根目录
    path.join(__dirname, '../**/*.html'),        // 所有子目录
  ],
  // 排除模式
  excludePatterns: [
    '**/node_modules/**',
    '**/output/**',
    '**/.git/**',
    // 可以添加更多排除规则...
  ],
  // ...
};
```

### 图片分辨率

在 `src/html-to-images.js` 中调整：

```javascript
viewport: {
  width: 3508,  // 297mm at 300 DPI
  height: 2480, // 210mm at 300 DPI
  deviceScaleFactor: 2 // 2x for higher quality (effectively 600 DPI)
}
```

### PPT 页面尺寸

在 `src/images-to-ppt.py` 中调整：

```python
CONFIG = {
    'slide_width': Cm(29.7),  # A4 landscape width
    'slide_height': Cm(21.0), # A4 landscape height
}
```

## 工作原理

### 第一步：HTML → 图片

1. **加载 HTML**：Puppeteer 在无头浏览器中打开 HTML 文件
2. **等待渲染**：等待网络空闲和 Chart.js 完成绘制（3秒）
3. **定位元素**：查找所有 `.page` 类的 DOM 元素
4. **截图保存**：为每个页面元素生成高清 PNG 截图

### 第二步：图片 → PPT

1. **扫描图片**：读取 `output/images/` 目录下的所有 PNG 文件
2. **分组处理**：根据文件名前缀分组（每个 HTML 对应一个 PPT）
3. **创建幻灯片**：为每张图片创建一个空白幻灯片
4. **适配布局**：保持图片宽高比，居中填充幻灯片
5. **保存文件**：输出为 `.pptx` 格式

## 输出文件命名规则

### 图片文件

```
{HTML文件名}_page_{页码}.png
```

示例：
- `版本2_page_01.png`
- `版本2_page_02.png`
- `理想汽车供应链报告-优化版-2025-1031-1636_page_01.png`

### PPT 文件

```
{HTML文件名}.pptx
combined_reports.pptx  （所有页面合并版）
```

## 项目结构

```
web_to_presentation/
├── src/
│   ├── html-to-images.js     # HTML 转图片工具（Node.js + Puppeteer）
│   └── images-to-ppt.py      # 图片转 PPT 工具（Python + python-pptx）
├── output/
│   ├── images/               # 生成的图片
│   └── *.pptx                # 生成的 PPT
├── 版本2.html                 # 示例 HTML 报告 1
├── 理想汽车供应链报告-优化版-2025-1031-1636.html  # 示例 HTML 报告 2
├── package.json              # Node.js 依赖配置
├── requirements.txt          # Python 依赖配置
├── convert.sh                # 一键转换脚本
└── README.md                 # 本文档
```

## 常见问题

### Q: 图表没有正确渲染？

A: 确保 HTML 文件中的 Chart.js 已正确加载。可以增加 `html-to-images.js` 中的等待时间：

```javascript
await page.waitForTimeout(5000); // 从 3000 增加到 5000
```

### Q: 图片分辨率不够高？

A: 调整 `deviceScaleFactor` 参数：

```javascript
deviceScaleFactor: 3 // 从 2 增加到 3 (900 DPI)
```

### Q: PPT 中图片显示不完整？

A: 检查 HTML 页面尺寸是否为标准 A4 横向（297mm × 210mm）。

### Q: 转换速度太慢？

A: 可以调整截图质量或减少等待时间，但可能影响输出质量。

## 技术栈

- **Puppeteer**：无头 Chrome 浏览器自动化
- **Chart.js**：图表库（HTML 中使用）
- **python-pptx**：Python PowerPoint 生成库
- **Pillow**：Python 图像处理库

## License

MIT

## 作者

Created for converting HTML reports to high-quality presentations.
