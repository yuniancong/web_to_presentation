# Web to Presentation Converter

将 HTML 网页报告转换为高清图片和 PowerPoint 演示文稿的自动化工具，提供可视化的前端设置界面。

## 功能特性

- ✅ **可视化设置界面**：Web界面配置所有转换参数，实时监控转换进度
- ✅ **高保真渲染**：使用 Playwright 无头浏览器，完美还原网页样式
- ✅ **图表支持**：完整支持 Chart.js 等动态图表库
- ✅ **灵活分辨率**：1x-5x DPI倍数可选（96-480 DPI）
- ✅ **多种导出模式**：图片模式、混合模式（文字矢量）、纯矢量模式
- ✅ **按页分割**：自动识别 `.page` 元素，每页单独输出
- ✅ **自动化 PPT**：将图片自动组装成 PowerPoint 文件
- ✅ **批量处理**：支持同时转换多个 HTML 文件
- ✅ **自动扫描**：自动识别根目录及子目录下的所有 HTML 文件，无需手动配置
- ✅ **实时进度**：转换过程实时显示进度和状态

## 系统要求

- **Node.js** 16+
- **Python** 3.8+
- **npm** 或 **yarn**
- **pip3**

## 🚀 快速开始

### 方式一：使用可视化界面（推荐）

```bash
# 启动应用（会自动安装依赖并打开浏览器）
python3 start.py
```

或使用npm：

```bash
npm start
```

启动后会自动：
- ✅ 检查并安装所需依赖
- ✅ 启动后端API服务器
- ✅ 打开前端设置页面（http://localhost:5000）

在前端界面中可以：
1. 📂 扫描HTML文件
2. ⚙️ 配置图片和PPT参数
3. 🚀 一键启动转换
4. 📊 实时查看转换进度

### 方式二：使用命令行（传统）

```bash
# 1. 安装依赖
npm install
pip3 install flask flask-cors python-pptx Pillow

# 2. 转换HTML为图片
node src/html-to-images.js

# 3. 转换图片为PPT
python3 src/images-to-ppt.py
```

### 准备 HTML 文件

将需要转换的 HTML 文件放到项目根目录或子目录下：

```
web_to_presentation/
├── 报告1.html
├── 报告2.html
├── my_project/
│   ├── index.html
│   └── report.html
└── ...
```

脚本会**自动扫描**所有 HTML 文件！

### 查看输出

转换完成后，文件保存在：
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
├── frontend/                          # 前端设置界面
│   └── index.html                    # Web可视化配置页面
├── src/
│   ├── html-to-images.js             # HTML转图片（Node.js + Playwright）
│   ├── html-to-images-config.json    # 图片转换配置（自动生成）
│   ├── images-to-ppt.py              # 图片转PPT（原始版本）
│   ├── images-to-ppt-advanced.py     # 高级PPT生成（支持多种模式）
│   └── api_server.py                 # Flask API服务器
├── output/
│   ├── images/                       # 生成的图片
│   └── *.pptx                        # 生成的PPT文件
├── start.py                          # 启动脚本（推荐）
├── package.json                      # Node.js依赖配置
├── README.md                         # 本文档
└── USAGE.md                          # 详细使用指南
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
