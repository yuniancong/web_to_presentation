#!/usr/bin/env python3
"""
API Server for Web to Presentation Converter
Provides REST API for frontend to control conversion process
"""

import os
import sys
import json
import uuid
import threading
import subprocess
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import glob as glob_module

app = Flask(__name__, static_folder='../frontend')
CORS(app)  # Enable CORS for frontend access

# Global storage for conversion tasks
tasks = {}
tasks_lock = threading.Lock()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
UPLOAD_FOLDER = PROJECT_ROOT / 'temp_uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'html', 'htm'}


class ConversionTask:
    """Represents a conversion task"""

    def __init__(self, task_id, settings, uploaded_files, output_path):
        self.task_id = task_id
        self.settings = settings
        self.uploaded_files = uploaded_files  # List of uploaded file paths
        self.output_path = output_path  # Custom output path
        self.status = 'pending'  # pending, running, completed, error
        self.progress = 0
        self.message = ''
        self.error = None
        self.output_dir = None

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'error': self.error,
            'output_dir': self.output_dir
        }


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_files(files):
    """Save uploaded files and return their paths"""
    saved_paths = []
    task_folder = UPLOAD_FOLDER / str(uuid.uuid4())
    task_folder.mkdir(exist_ok=True)

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = task_folder / filename
            file.save(str(file_path))
            saved_paths.append(str(file_path))

    return saved_paths, str(task_folder)


def run_conversion(task):
    """Run the conversion process in a background thread"""
    temp_folder = None
    try:
        task.status = 'running'
        task.progress = 0
        task.message = '正在准备转换...'

        export_type = task.settings.get('exportType', 'both')

        # Determine output directory
        if task.output_path:
            output_dir = Path(task.output_path)
            if not output_dir.is_absolute():
                output_dir = PROJECT_ROOT / output_dir
        else:
            output_dir = PROJECT_ROOT / 'output'

        # Create output directories
        images_dir = output_dir / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)

        # Determine which steps to run
        run_images = export_type in ['both', 'images']
        run_ppt = export_type in ['both', 'ppt']

        # Step 1: Convert HTML to images (if needed)
        if run_images:
            task.message = '正在将HTML转换为图片...'
            task.progress = 10
            print(f"\n{'='*60}")
            print("正在将HTML转换为图片...")
            print(f"上传的文件: {len(task.uploaded_files)} 个")
            print(f"{'='*60}")

            # Update html-to-images.js config with custom output path
            update_html_to_images_config(task.settings['image'], str(images_dir))

            # Process each uploaded HTML file
            for i, html_file in enumerate(task.uploaded_files):
                print(f"\n处理文件 {i+1}/{len(task.uploaded_files)}: {Path(html_file).name}")

                # Run Node.js script with real-time output for each file
                process = subprocess.Popen(
                    ['node', str(PROJECT_ROOT / 'src' / 'html-to-images.js'), html_file],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                # Stream output and update progress
                for line in iter(process.stdout.readline, ''):
                    if line:
                        print(line.rstrip())
                        # Update progress based on output
                        if '📄 Processing:' in line:
                            task.progress = min(task.progress + 3, 45)
                        elif '✓ Page' in line:
                            task.progress = min(task.progress + 1, 45)

                process.wait()

                if process.returncode != 0:
                    raise Exception(f"HTML to images conversion failed with code {process.returncode}")

            task.progress = 50
            task.message = 'HTML转换完成'
            print(f"\n✅ HTML转换完成")
        else:
            task.progress = 50
            task.message = '跳过图片生成，使用现有图片...'
            print("\n⏭️  跳过图片生成，使用现有图片")

        # Step 2: Convert images to PPT (if needed)
        if run_ppt:
            task.message = '正在生成PPT...'
            task.progress = 55
            print(f"\n{'='*60}")
            print("正在生成PPT...")
            print(f"{'='*60}")

            # Run Python script with real-time output and custom output path
            process = subprocess.Popen(
                [sys.executable, str(PROJECT_ROOT / 'src' / 'images-to-ppt-advanced.py'),
                 '--settings', json.dumps(task.settings['ppt']),
                 '--images-dir', str(images_dir),
                 '--output-dir', str(output_dir)],
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Stream output and update progress
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
                    # Update progress based on output
                    if '✓ Slide' in line:
                        task.progress = min(task.progress + 2, 95)
                    elif 'Creating' in line:
                        task.progress = min(task.progress + 5, 95)

            process.wait()

            if process.returncode != 0:
                raise Exception(f"PPT generation failed with code {process.returncode}")

            task.progress = 100
            task.message = 'PPT生成完成'
            print(f"\n✅ PPT生成完成")
        else:
            task.progress = 100
            task.message = '仅图片导出完成'
            print("\n✅ 仅图片导出完成")

        task.status = 'completed'
        task.output_dir = str(output_dir)
        print(f"\n🎉 转换完成！输出目录: {task.output_dir}")

        # Clean up temporary upload folder
        if task.uploaded_files and len(task.uploaded_files) > 0:
            temp_folder = str(Path(task.uploaded_files[0]).parent)
            try:
                shutil.rmtree(temp_folder)
                print(f"✓ 清理临时文件: {temp_folder}")
            except Exception as cleanup_error:
                print(f"⚠️  清理临时文件失败: {cleanup_error}")

    except Exception as e:
        task.status = 'error'
        task.error = str(e)
        task.message = f'转换失败: {str(e)}'
        print(f"\n❌ 转换错误: {e}")

        # Clean up on error
        if task.uploaded_files and len(task.uploaded_files) > 0:
            temp_folder = str(Path(task.uploaded_files[0]).parent)
            try:
                shutil.rmtree(temp_folder)
            except:
                pass


def update_html_to_images_config(image_settings, output_dir):
    """Update html-to-images.js configuration based on settings"""
    config_path = PROJECT_ROOT / 'src' / 'html-to-images-config.json'

    config = {
        'outputDir': output_dir,
        'viewport': {
            'width': 1122,
            'height': 794,
            'deviceScaleFactor': image_settings['deviceScaleFactor']
        },
        'imageFormat': image_settings['format'],
        'imageQuality': image_settings['quality']
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


@app.route('/api/convert', methods=['POST'])
def convert():
    """Start a conversion task with uploaded files"""
    try:
        # Get uploaded files
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            }), 400

        files = request.files.getlist('files')

        if not files or len(files) == 0:
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            }), 400

        # Save uploaded files
        saved_paths, temp_folder = save_uploaded_files(files)

        if not saved_paths:
            return jsonify({
                'success': False,
                'error': '没有有效的HTML文件'
            }), 400

        # Parse settings
        settings_json = request.form.get('settings', '{}')
        settings = json.loads(settings_json)

        # Get output path
        output_path = settings.get('outputPath')

        # Create a new task
        task_id = str(uuid.uuid4())
        task = ConversionTask(task_id, settings, saved_paths, output_path)

        with tasks_lock:
            tasks[task_id] = task

        # Start conversion in background thread
        thread = threading.Thread(target=run_conversion, args=(task,))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'task_id': task_id,
            'files_count': len(saved_paths)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    """Get progress of a conversion task"""
    with tasks_lock:
        task = tasks.get(task_id)

    if not task:
        return jsonify({
            'success': False,
            'error': 'Task not found'
        }), 404

    return jsonify(task.to_dict())


@app.route('/api/settings', methods=['GET'])
def get_default_settings():
    """Get default settings"""
    return jsonify({
        'image': {
            'deviceScaleFactor': 3,
            'quality': 100,
            'format': 'png'
        },
        'ppt': {
            'exportMode': 'hybrid',
            'extractText': True,
            'separateReports': True,
            'createCombined': True
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})


@app.route('/')
def index():
    """Serve frontend page"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory(app.static_folder, path)


def main():
    """Start the API server"""
    # Support configurable port via environment variable or default to 5001
    port = int(os.environ.get('PORT', 5001))

    print('🚀 Starting API Server...')
    print(f'📁 Project root: {PROJECT_ROOT}')
    print(f'🌐 Server running on http://localhost:{port}')
    print(f'📊 Frontend: http://localhost:{port}/frontend')
    print('\nPress Ctrl+C to stop the server\n')

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


if __name__ == '__main__':
    main()
