#!/usr/bin/env python3
"""
Flask API Backend for DebtGuardianAgentic Web UI
Provides REST API endpoints for the React frontend
Supports multiple file types and folder uploads
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
import traceback

# Import DebtGuardian components
#from debt_guardian import DebtGuardianPipeline
from pipeline_adapter import DebtGuardianPipeline
from program_slicer import ProgramSlicerAgent
from debt_detector import ClassDebtDetector, MethodDebtDetector
import config

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'java', 'cpp', 'cs', 'py', 'js'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB for folder uploads

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_language(filename):
    """Determine programming language from file extension"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    language_map = {
        'java': 'Java',
        'cpp': 'C++',
        'cs': 'C#',
        'py': 'Python',
        'js': 'JavaScript'
    }
    return language_map.get(ext, 'Unknown')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'supported_languages': list(ALLOWED_EXTENSIONS)
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'agents': {
            'class_detector': {
                'enabled': config.AGENT_CONFIGS['class_detector']['enabled'],
                'model': config.AGENT_CONFIGS['class_detector']['model'],
                'shot': config.AGENT_CONFIGS['class_detector']['shot']
            },
            'method_detector': {
                'enabled': config.AGENT_CONFIGS['method_detector']['enabled'],
                'model': config.AGENT_CONFIGS['method_detector']['model'],
                'shot': config.AGENT_CONFIGS['method_detector']['shot']
            },
            'explanation': {
                'enabled': config.AGENT_CONFIGS['explanation']['enabled']
            },
            'fix_suggestion': {
                'enabled': config.AGENT_CONFIGS['fix_suggestion']['enabled']
            },
            'program_slicer': {
                'enabled': config.AGENT_CONFIGS.get('program_slicer', {}).get('enabled', True)
            }
        },
        'coordinator': config.AGENT_CONFIGS['coordinator'],
        'debt_categories': config.TD_CATEGORIES,
        'supported_extensions': list(ALLOWED_EXTENSIONS)
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        data = request.json
        
        # Update agent configurations
        if 'enableClassDetection' in data:
            config.AGENT_CONFIGS['class_detector']['enabled'] = data['enableClassDetection']
        
        if 'enableMethodDetection' in data:
            config.AGENT_CONFIGS['method_detector']['enabled'] = data['enableMethodDetection']
        
        if 'enableExplanations' in data:
            config.AGENT_CONFIGS['explanation']['enabled'] = data['enableExplanations']
        
        if 'enableFixSuggestions' in data:
            config.AGENT_CONFIGS['fix_suggestion']['enabled'] = data['enableFixSuggestions']
        
        if 'applyProgramSlicing' in data:
            if 'program_slicer' not in config.AGENT_CONFIGS:
                config.AGENT_CONFIGS['program_slicer'] = {}
            config.AGENT_CONFIGS['program_slicer']['enabled'] = data['applyProgramSlicing']
        
        if 'minConfidence' in data:
            config.AGENT_CONFIGS['coordinator']['min_confidence'] = float(data['minConfidence'])
        
        if 'conflictStrategy' in data:
            config.AGENT_CONFIGS['coordinator']['conflict_resolution_strategy'] = data['conflictStrategy']
        
        return jsonify({'status': 'success', 'message': 'Configuration updated'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Upload code files for analysis (supports both individual files and folders)"""
    try:
        if 'files' not in request.files:
            return jsonify({'status': 'error', 'message': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if not files or files[0].filename == '':
            return jsonify({'status': 'error', 'message': 'No files selected'}), 400
        
        # Create temporary directory for this upload session
        session_dir = tempfile.mkdtemp(dir=UPLOAD_FOLDER)
        uploaded_files = []
        skipped_files = []
        
        # Process each file
        for file in files:
            if file and file.filename:
                # Check if file extension is allowed
                if not allowed_file(file.filename):
                    skipped_files.append({
                        'name': file.filename,
                        'reason': 'Unsupported file type'
                    })
                    continue
                
                # Get the original filename (might include path for folder uploads)
                original_filename = file.filename
                
                # For folder uploads, preserve directory structure
                if '/' in original_filename or '\\' in original_filename:
                    # This is a folder upload with path
                    # Normalize path separators
                    relative_path = original_filename.replace('\\', '/')
                    filepath = os.path.join(session_dir, relative_path)
                    
                    # Create subdirectories if needed
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                else:
                    # Single file upload
                    filename = secure_filename(original_filename)
                    filepath = os.path.join(session_dir, filename)
                
                # Save the file
                try:
                    file.save(filepath)
                    file_size = os.path.getsize(filepath)
                    language = get_file_language(original_filename)
                    
                    uploaded_files.append({
                        'name': original_filename,
                        'path': filepath,
                        'size': file_size,
                        'language': language
                    })
                except Exception as e:
                    skipped_files.append({
                        'name': original_filename,
                        'reason': f'Failed to save: {str(e)}'
                    })
        
        if not uploaded_files:
            # Clean up session directory if no files were uploaded
            shutil.rmtree(session_dir, ignore_errors=True)
            return jsonify({
                'status': 'error', 
                'message': 'No valid code files uploaded',
                'skipped_files': skipped_files
            }), 400
        
        # Group files by language
        files_by_language = {}
        for file_info in uploaded_files:
            lang = file_info['language']
            if lang not in files_by_language:
                files_by_language[lang] = 0
            files_by_language[lang] += 1
        
        return jsonify({
            'status': 'success',
            'session_id': os.path.basename(session_dir),
            'files': uploaded_files,
            'skipped_files': skipped_files,
            'summary': {
                'total_uploaded': len(uploaded_files),
                'total_skipped': len(skipped_files),
                'by_language': files_by_language
            }
        })
    
    except Exception as e:
        print(f"Error in upload: {str(e)}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_code():
    """Analyze uploaded code files"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'No session ID provided'}), 400
        
        session_dir = os.path.join(UPLOAD_FOLDER, session_id)
        
        if not os.path.exists(session_dir):
            return jsonify({'status': 'error', 'message': 'Invalid session ID'}), 400
        
        print(f"[Info] Starting analysis for session: {session_id}")
        print(f"[Info] Session directory: {session_dir}")
        
        # Count files by language
        all_files = []
        for root, dirs, files in os.walk(session_dir):
            for file in files:
                if allowed_file(file):
                    full_path = os.path.join(root, file)
                    all_files.append(full_path)
        
        print(f"[Info] Found {len(all_files)} code files to analyze")
        
        # Create pipeline and analyze
        try:
            pipeline = DebtGuardianPipeline(
                repo_path=session_dir,
                output_dir=tempfile.mkdtemp()
            )
            
            # Run analysis
            results = pipeline.analyze_repository()
            
            print(f"[Info] Analysis complete. Found {len(results)} issues")
            
        except Exception as e:
            print(f"[Error] Pipeline execution failed: {str(e)}")
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'message': f'Analysis pipeline failed: {str(e)}'
            }), 500
        
        # Generate summary
        summary = pipeline.coordinator.generate_report(results)
        
        # Add file statistics to summary
        files_by_language = {}
        for file_path in all_files:
            lang = get_file_language(file_path)
            if lang not in files_by_language:
                files_by_language[lang] = 0
            files_by_language[lang] += 1
        
        summary['files_analyzed'] = len(all_files)
        summary['by_language'] = files_by_language
        
        # Format response
        response = {
            'status': 'success',
            'summary': {
                'total_issues': summary['total_issues'],
                'by_category': summary['by_category'],
                'by_severity': summary['by_severity'],
                'by_granularity': summary['by_granularity'],
                'files_analyzed': summary['files_analyzed'],
                'by_language': summary['by_language']
            },
            'issues': []
        }
        
        # Format each issue
        for result in results:
            cat = result.get('detected_category_int', -1)
            if cat > 0:
                debt_info = config.TD_CATEGORIES.get(cat, {})
                
                # Make file path relative to session dir for display
                file_path = result.get('file_path', 'unknown')
                try:
                    relative_path = os.path.relpath(file_path, session_dir)
                except:
                    relative_path = file_path
                
                issue = {
                    'id': len(response['issues']) + 1,
                    'file_path': relative_path,
                    'code_name': result.get('code_name', 'unknown'),
                    'code_type': result.get('code_type', 'unknown'),
                    'debt_type': debt_info.get('name', 'Unknown'),
                    'severity': debt_info.get('severity', 'unknown'),
                    'confidence': result.get('confidence', 0.0),
                    'granularity': result.get('granularity', 'unknown'),
                    'language': get_file_language(file_path)
                }
                
                # Add localization if available
                if 'localization' in result:
                    loc = result['localization']
                    issue['start_line'] = loc.get('start_line')
                    issue['end_line'] = loc.get('end_line')
                
                # Add explanation if available
                if 'explanation' in result and 'text' in result['explanation']:
                    issue['explanation'] = result['explanation']['text']
                
                # Add fix suggestion if available
                if 'fix_suggestion' in result and 'text' in result['fix_suggestion']:
                    issue['fix_suggestion'] = result['fix_suggestion']['text']
                
                # Add code snippet (truncated)
                if 'code_snippet' in result:
                    issue['code_snippet'] = result['code_snippet'][:500]
                
                response['issues'].append(issue)
        
        # Clean up session directory after analysis (optional)
        # shutil.rmtree(session_dir, ignore_errors=True)
        
        return jsonify(response)
    
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Analysis failed: {str(e)}'
        }), 500


@app.route('/api/analyze/file', methods=['POST'])
def analyze_single_file():
    """Analyze a single code snippet (for quick testing)"""
    try:
        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'java')
        granularity = data.get('granularity', 'class')  # 'class' or 'method'
        
        if not code:
            return jsonify({'status': 'error', 'message': 'No code provided'}), 400
        
        # Determine file extension from language
        ext_map = {
            'java': '.java',
            'cpp': '.cpp',
            'cs': '.cs',
            'python': '.py',
            'javascript': '.js'
        }
        extension = ext_map.get(language.lower(), '.java')
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Slice the code
            slicer = ProgramSlicerAgent()
            slices = slicer.slice_file(temp_file)
            
            # Detect based on granularity
            results = []
            
            if granularity == 'class' and slices.get('classes'):
                detector = ClassDebtDetector(shot_type='few')
                for cls in slices['classes']:
                    result = detector.detect(cls)
                    results.append(result)
            
            elif granularity == 'method' and slices.get('methods'):
                detector = MethodDebtDetector(shot_type='zero')
                for method in slices['methods']:
                    result = detector.detect(method)
                    results.append(result)
            
            # Format response
            response_issues = []
            for result in results:
                cat = result.get('detected_category_int', -1)
                if cat > 0:
                    debt_info = config.TD_CATEGORIES.get(cat, {})
                    response_issues.append({
                        'code_name': result.get('code_name', 'unknown'),
                        'debt_type': debt_info.get('name', 'Unknown'),
                        'severity': debt_info.get('severity', 'unknown'),
                        'confidence': result.get('confidence', 0.0),
                        'language': language
                    })
            
            return jsonify({
                'status': 'success',
                'issues': response_issues,
                'slices_found': {
                    'classes': len(slices.get('classes', [])),
                    'methods': len(slices.get('methods', []))
                }
            })
        
        finally:
            # Clean up temp file
            os.unlink(temp_file)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Analysis failed: {str(e)}'
        }), 500


@app.route('/api/export/<session_id>', methods=['GET'])
def export_results(session_id):
    """Export analysis results as JSON file"""
    try:
        # In a real implementation, can retrieve stored results
        # For now, return a placeholder
        return jsonify({
            'status': 'error',
            'message': 'Export functionality requires result persistence'
        }), 501
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/models', methods=['GET'])
def list_models():
    """List available Ollama models"""
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True, check=True)
        
        # Parse model list
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        models = []
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if parts:
                    models.append({
                        'name': parts[0],
                        'size': parts[1] if len(parts) > 1 else 'unknown'
                    })
        
        return jsonify({
            'status': 'success',
            'models': models
        })
    
    except subprocess.CalledProcessError:
        return jsonify({
            'status': 'error',
            'message': 'Ollama is not running or not installed'
        }), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List active analysis sessions"""
    try:
        sessions = []
        for session_dir in os.listdir(UPLOAD_FOLDER):
            session_path = os.path.join(UPLOAD_FOLDER, session_dir)
            if os.path.isdir(session_path):
                # Count files in session
                file_count = sum(1 for root, dirs, files in os.walk(session_path) 
                               for f in files if allowed_file(f))
                
                sessions.append({
                    'session_id': session_dir,
                    'created': datetime.fromtimestamp(os.path.getctime(session_path)).isoformat(),
                    'file_count': file_count
                })
        
        return jsonify({
            'status': 'success',
            'sessions': sessions
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete an analysis session"""
    try:
        session_path = os.path.join(UPLOAD_FOLDER, session_id)
        
        if not os.path.exists(session_path):
            return jsonify({'status': 'error', 'message': 'Session not found'}), 404
        
        shutil.rmtree(session_path)
        
        return jsonify({
            'status': 'success',
            'message': 'Session deleted'
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        'status': 'error',
        'message': f'File(s) too large. Maximum total size is {MAX_FILE_SIZE // (1024*1024)}MB'
    }), 413


@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


def cleanup_old_sessions():
    """Clean up old upload sessions (run periodically)"""
    try:
        current_time = datetime.now().timestamp()
        
        for session_dir in os.listdir(UPLOAD_FOLDER):
            session_path = os.path.join(UPLOAD_FOLDER, session_dir)
            
            if os.path.isdir(session_path):
                # Remove sessions older than 2 hours
                dir_age = current_time - os.path.getctime(session_path)
                if dir_age > 7200:  # 2 hours
                    print(f"[Cleanup] Removing old session: {session_dir}")
                    shutil.rmtree(session_path, ignore_errors=True)
    
    except Exception as e:
        print(f"Cleanup error: {str(e)}")


if __name__ == '__main__':
    print("="*80)
    print("DebtGuardianAgentic API Server Starting...")
    print("="*80)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Supported languages: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"Max upload size: {MAX_FILE_SIZE // (1024*1024)}MB")
    print("\nAPI Endpoints:")
    print("  GET  /api/health              - Health check")
    print("  GET  /api/config              - Get configuration")
    print("  POST /api/config              - Update configuration")
    print("  POST /api/upload              - Upload files/folders")
    print("  POST /api/analyze             - Analyze uploaded code")
    print("  POST /api/analyze/file        - Analyze single snippet")
    print("  GET  /api/models              - List Ollama models")
    print("  GET  /api/sessions            - List active sessions")
    print("  DELETE /api/sessions/<id>    - Delete a session")
    print("\nAPI will be available at http://localhost:5000")
    print("="*80 + "\n")
    
    # Run periodic cleanup
    import threading
    import time
    
    def periodic_cleanup():
        while True:
            time.sleep(3600)  # Every hour
            cleanup_old_sessions()
    
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
