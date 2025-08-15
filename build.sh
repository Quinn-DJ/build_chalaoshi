#!/bin/bash

# 查老师完整构建脚本
# 包含：下载压缩包 -> 解压 -> 数据处理 -> web文件夹构建

echo "🎓 查老师 - 浙江大学教师评价查询系统"
echo "========================================"
echo "开始完整构建流程..."
echo ""

# 错误处理函数
handle_error() {
    echo "❌ 构建失败: $1"
    exit 1
}

# 进度显示函数
show_progress() {
    echo ""
    echo "📋 当前步骤: $1"
    echo "----------------------------------------"
}

# 检查必要的命令
check_requirements() {
    show_progress "检查运行环境"
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        handle_error "Python3 未安装，请先安装 Python3"
    fi
    echo "✅ Python3 已安装: $(python3 --version)"
    
    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        handle_error "pip3 未安装，请先安装 pip3"
    fi
    echo "✅ pip3 已安装"
    
    # 创建必要的目录
    echo "📁 创建目录结构..."
    mkdir -p logs
    mkdir -p comment/extracted
    echo "✅ 目录结构创建完成"
}

# 安装Python依赖
install_dependencies() {
    show_progress "安装Python依赖"
    
    if [ ! -f "requirements.txt" ]; then
        handle_error "requirements.txt 文件不存在"
    fi
    
    echo "📦 安装依赖包..."
    pip3 install -r requirements.txt > /dev/null 2>&1
    
    if [ $? -ne 0 ]; then
        echo "⚠️  使用 --user 方式安装依赖..."
        pip3 install --user -r requirements.txt
        if [ $? -ne 0 ]; then
            handle_error "依赖包安装失败"
        fi
    fi
    
    echo "✅ Python依赖安装完成"
}

# 下载压缩包
download_archive() {
    show_progress "下载数据压缩包"
    
    # 检查是否已经存在压缩包
    ARCHIVE_FILE="comment/chalaoshi_csv20250502_5399305_2696_26893D_sha256.zip"
    if [ -f "$ARCHIVE_FILE" ]; then
        echo "✅ 压缩包已存在: $ARCHIVE_FILE"
        return 0
    fi
    
    echo "📥 开始下载压缩包..."
    python3 src/file_downloader.py --from-config
    
    if [ $? -ne 0 ]; then
        handle_error "压缩包下载失败"
    fi
    
    if [ ! -f "$ARCHIVE_FILE" ]; then
        handle_error "下载完成但找不到压缩包文件"
    fi
    
    echo "✅ 压缩包下载完成: $ARCHIVE_FILE"
}

# 解压压缩包
extract_archive() {
    show_progress "解压数据文件"
    
    # 检查是否已经解压
    if [ -d "comment/extracted" ] && [ "$(ls -A comment/extracted 2>/dev/null)" ]; then
        echo "✅ 数据文件已解压"
        return 0
    fi
    
    echo "📂 开始解压压缩包..."
    python3 src/file_extractor.py --from-config
    
    if [ $? -ne 0 ]; then
        handle_error "压缩包解压失败"
    fi
    
    # 检查解压结果
    if [ ! -d "comment/extracted" ] || [ ! "$(ls -A comment/extracted 2>/dev/null)" ]; then
        handle_error "解压完成但找不到解压文件"
    fi
    
    echo "✅ 压缩包解压完成"
    echo "📊 解压文件数量: $(ls comment/extracted/*.csv 2>/dev/null | wc -l)"
}

# 处理数据并构建web文件
build_web_data() {
    show_progress "处理数据并构建Web文件"
    
    echo "🔄 开始数据处理..."
    python3 src/build_html.py
    
    if [ $? -ne 0 ]; then
        handle_error "数据处理失败"
    fi
    
    # 检查生成的文件
    if [ ! -f "web/index.html" ]; then
        handle_error "HTML文件生成失败"
    fi
    
    echo "✅ Web数据构建完成"
}

# 构建教师评论索引
build_html_files() {
    show_progress "构建HTML文件"

    echo "🔄 开始构建HTML文件..."
    python3 src/build_html.py

    if [ $? -ne 0 ]; then
        handle_error "HTML文件构建失败"
    fi
    
    # 检查生成的文件
    if [ ! -f "web/index.html" ]; then
        handle_error "HTML文件生成失败"
    fi
    
    echo "✅ HTML文件构建完成"
}

# 验证构建结果
verify_build() {
    show_progress "验证构建结果"
    
    # 检查关键文件
    local required_files=(
        "web/index.html"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            handle_error "缺少关键文件: $file"
        fi
        echo "✅ $file"
    done
    
    echo "✅ HTML文件验证完成"
}

# 显示完成信息
show_completion() {
    show_progress "构建完成"
    
    # 获取网站目录的绝对路径
    WEB_DIR=$(cd web && pwd)
    INDEX_FILE="$WEB_DIR/index.html"
    
    echo "🎉 查老师网站构建完成！"
    echo ""
    echo "📁 网站文件位置: $WEB_DIR"
    echo "🌐 主页文件: $INDEX_FILE"
    echo ""
    echo "🚀 启动方式："
    echo "   方式1 - 直接打开文件:"
    echo "     open '$INDEX_FILE'"
    echo ""
    echo "   方式2 - 启动本地服务器:"
    echo "     cd web && python3 -m http.server 8000"
    echo "     然后访问: http://localhost:8000"
    echo ""
    echo "💡 功能特色："
    echo "   • 完全离线使用，无需网络连接"
    echo "   • 支持教师姓名、学院、课程搜索"
    echo "   • 教师评分和评论详情查看"
    echo "   • 课程信息查询和GPA数据展示"
    echo "   • 课程统计图表和排行榜"
    echo "   • 响应式设计，支持手机和电脑"
    echo "   • 高效的评论索引，快速加载教师详情"
    echo ""
    echo "✨ 构建统计:"
    echo "   ✅ HTML文件已生成完成"
    echo ""
}

# 主函数
main() {
    # 记录开始时间
    START_TIME=$(date +%s)
    
    # 执行构建步骤
    check_requirements
    install_dependencies
    download_archive
    extract_archive
    build_web_data
    verify_build
    show_completion
    
    # 计算总用时
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo ""
    echo "⏱️  总用时: ${DURATION} 秒"
    echo "🎯 构建成功完成！"
}

# 捕获中断信号
trap 'echo ""; echo "❌ 构建被中断"; exit 1' INT TERM

# 运行主函数
main "$@"
