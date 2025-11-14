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
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import glob as glob_module

app = Flask(__name__, static_folder='../frontend')
CORS(app)  # Enable CORS for frontend access

# Global storage for conversion tasks
tasks = {}
tasks_lock = threading.Lock()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
HTML_PATTERNS = [
    str(PROJECT_ROOT / "*.html"),
    str(PROJECT_ROOT / "**/*.html"),
]
EXCLUDE_PATTERNS = [
    "**/node_modules/**",
    "**/output/**",
    "**/.git/**",
    "**/dist/**",
    "**/build/**",
    "**/frontend/**"
]


class ConversionTask:
    """Represents a conversion task"""

    def __init__(self, task_id, settings):
        self.task_id = task_id
        self.settings = settings
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


def scan_html_files():
    """Scan for HTML files in the project"""
    all_files = []

    for pattern in HTML_PATTERNS:
        try:
            files = glob_module.glob(pattern, recursive=True)
            for file in files:
                # Check if file matches any exclude pattern
                should_exclude = False
                for exclude in EXCLUDE_PATTERNS:
                    if glob_module.fnmatch.fnmatch(file, exclude):
                        should_exclude = True
                        break
                if not should_exclude:
                    all_files.append(file)
        except Exception as e:
            print(f"Error scanning pattern {pattern}: {e}")

    # Remove duplicates and convert to relative paths
    unique_files = list(set(all_files))
    relative_files = [os.path.relpath(f, PROJECT_ROOT) for f in unique_files]
    return sorted(relative_files)


def run_conversion(task):
    """Run the conversion process in a background thread"""
    try:
        task.status = 'running'
        task.progress = 0
        task.message = '正在准备转换...'

        # Step 1: Convert HTML to images (50% of progress)
        task.message = '正在将HTML转换为图片...'
        task.progress = 10

        # Update html-to-images.js config
        update_html_to_images_config(task.settings['image'])

        # Run Node.js script
        result = subprocess.run(
            ['node', str(PROJECT_ROOT / 'src' / 'html-to-images.js')],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"HTML to images conversion failed: {result.stderr}")

        task.progress = 50
        task.message = 'HTML转换完成，正在生成PPT...'

        # Step 2: Convert images to PPT (50% of progress)
        # Update images-to-ppt.py based on settings
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / 'src' / 'images-to-ppt-advanced.py'),
             '--settings', json.dumps(task.settings['ppt'])],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"PPT generation failed: {result.stderr}")

        task.progress = 100
        task.status = 'completed'
        task.message = '转换完成！'
        task.output_dir = str(PROJECT_ROOT / 'output')

    except Exception as e:
        task.status = 'error'
        task.error = str(e)
        task.message = f'转换失败: {str(e)}'
        print(f"Conversion error: {e}")


def update_html_to_images_config(image_settings):
    """Update html-to-images.js configuration based on settings"""
    config_path = PROJECT_ROOT / 'src' / 'html-to-images-config.json'

    config = {
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


@app.route('/api/scan', methods=['GET'])
def scan():
    """Scan for HTML files"""
    try:
        files = scan_html_files()
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/convert', methods=['POST'])
def convert():
    """Start a conversion task"""
    try:
        settings = request.json

        # Create a new task
        task_id = str(uuid.uuid4())
        task = ConversionTask(task_id, settings)

        with tasks_lock:
            tasks[task_id] = task

        # Start conversion in background thread
        thread = threading.Thread(target=run_conversion, args=(task,))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'task_id': task_id
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
    print('🚀 Starting API Server...')
    print(f'📁 Project root: {PROJECT_ROOT}')
    print('🌐 Server running on http://localhost:5000')
    print('📊 Frontend: http://localhost:5000/frontend')
    print('\nPress Ctrl+C to stop the server\n')

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)


if __name__ == '__main__':
    main()
