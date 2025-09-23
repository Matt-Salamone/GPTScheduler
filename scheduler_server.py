#!/usr/bin/env python3
"""
Fixed Flask server for the Process Scheduler GUI - Windows Compatible
Removes Unicode characters that cause encoding issues on Windows.
"""

import os
import sys
import tempfile
import subprocess
import json
import re

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

try:
    from flask import Flask, request, jsonify, send_file
    print("[ OK ] Flask imported successfully")
except ImportError:
    print("[ERROR] Flask not found. Install with: pip install flask")
    sys.exit(1)

try:
    from flask_cors import CORS
    print("[ OK ] Flask-CORS imported successfully")
except ImportError:
    print("[WARN] Flask-CORS not found. Install with: pip install flask-cors")
    print("Continuing without CORS (may cause browser issues)")
    CORS = None

app = Flask(__name__)

# Enable CORS if available
if CORS:
    CORS(app)

# Configuration
SCHEDULER_SCRIPT = "scheduler-gpt.py"

@app.route('/')
def index():
    """Serve the main GUI page."""
    try:
        return send_file('scheduler_gui.html')
    except FileNotFoundError:
        return """
        <h1>Scheduler GUI</h1>
        <p>Error: scheduler_gui.html not found!</p>
        <p>Please save the HTML GUI file as 'scheduler_gui.html' in the same directory.</p>
        """, 404

@app.route('/api/test')
def test():
    """Test endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'Server is running',
        'scheduler_available': os.path.exists(SCHEDULER_SCRIPT)
    })

@app.route('/api/simulate', methods=['POST'])
def simulate():
    """Run simulation."""
    try:
        print("[INFO] Received simulation request")
        
        # Check if scheduler exists
        if not os.path.exists(SCHEDULER_SCRIPT):
            return jsonify({'error': f'Scheduler script {SCHEDULER_SCRIPT} not found'}), 500
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        input_content = data.get('input_content')
        if not input_content:
            return jsonify({'error': 'No input content provided'}), 400
        
        print(f"[INFO] Input content: {input_content[:100]}...")
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.in', delete=False) as temp_file:
            temp_file.write(input_content)
            temp_input_path = temp_file.name
        
        print(f"[INFO] Created temporary file: {temp_input_path}")
        
        try:
            # Run scheduler
            print(f"[INFO] Running: {sys.executable} {SCHEDULER_SCRIPT} {temp_input_path}")
            
            result = subprocess.run([
                sys.executable, SCHEDULER_SCRIPT, temp_input_path
            ], capture_output=True, text=True, timeout=30)
            
            print(f"[INFO] Scheduler finished with return code: {result.returncode}")
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                print(f"[ERROR] Scheduler failed: {error_msg}")
                return jsonify({
                    'error': f'Scheduler failed: {error_msg}'
                }), 400
            
            # Find output file
            base_name = os.path.splitext(os.path.basename(temp_input_path))[0]
            output_file = f"{base_name}.out"
            
            print(f"[INFO] Looking for output file: {output_file}")
            
            if not os.path.exists(output_file):
                return jsonify({'error': 'Scheduler did not create output file'}), 500
            
            # Read output
            with open(output_file, 'r', encoding='utf-8') as f:
                output_content = f.read()
            
            print(f"[INFO] Read output file: {len(output_content)} characters")
            
            # Clean up output file
            os.remove(output_file)
            
            # Parse output
            parsed_data = parse_output_simple(output_content)
            
            return jsonify({
                'success': True,
                'output': output_content,
                'parsed': parsed_data
            })
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
                
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Scheduler execution timed out'}), 500
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

def parse_output_simple(output):
    """Simple output parser."""
    lines = output.strip().split('\n')
    
    parsed = {
        'algorithm': '',
        'simulation_info': '',
        'timeline': [],
        'finished_processes': [],
        'unfinished_processes': [],
        'raw_output': output
    }
    
    try:
        # Parse basic info
        for line in lines:
            if 'Scheduler:' in line:
                parsed['algorithm'] = line.strip()
                break
        
        for line in lines:
            if 'Simulation run' in line:
                parsed['simulation_info'] = line.strip()
                break
        
        # Parse timeline
        for line in lines:
            line = line.strip()
            if line.startswith('Time '):
                time_match = re.match(r'Time (\d+):(.*)', line)
                if time_match:
                    time_tick = int(time_match[1])
                    events_text = time_match[2].strip() if time_match[2] else ""
                    
                    # Parse events and determine running process
                    events = []
                    running = 'IDLE'
                    
                    if events_text:
                        # Split multiple events in the same line
                        event_parts = re.split(r'(?=[A-Z]\w+\s(?:arrived|selected|finished|preempted))', events_text)
                        
                        for event in event_parts:
                            event = event.strip()
                            if event:
                                events.append(event)
                                
                                # Determine what process is running
                                if 'selected' in event:
                                    match = re.search(r'(\w+)\s+selected', event)
                                    if match:
                                        running = match.group(1)
                                elif 'finished' in event or 'preempted' in event:
                                    if 'finished' in event:
                                        running = 'IDLE'
                    
                    parsed['timeline'].append({
                        'time': time_tick,
                        'running': running,
                        'ready_queue': [],
                        'events': events
                    })
        
        # Parse final metrics
        for line in lines:
            if 'Process ' in line and 'Wait Time=' in line:
                match = re.search(r'Process (\w+): Wait Time=(\d+), Turnaround Time=(\d+), Response Time=(\d+)', line)
                if match:
                    parsed['finished_processes'].append({
                        'name': match.group(1),
                        'wait_time': int(match.group(2)),
                        'turnaround_time': int(match.group(3)),
                        'response_time': int(match.group(4))
                    })
        
        # Parse unfinished processes
        for line in lines:
            if 'did not finish' in line:
                parts = line.strip().split()
                if parts:
                    process_name = parts[0]
                    parsed['unfinished_processes'].append({'name': process_name})
        
    except Exception as e:
        print(f"[WARN] Error parsing output: {e}")
        # Return what we have even if parsing fails partially
    
    return parsed

if __name__ == '__main__':
    print("Starting Process Scheduler GUI Server...")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python: {sys.executable}")
    print(f"Scheduler script: {'Found' if os.path.exists(SCHEDULER_SCRIPT) else 'NOT FOUND'} {SCHEDULER_SCRIPT}")
    print(f"GUI file: {'Found' if os.path.exists('scheduler_gui.html') else 'NOT FOUND'} scheduler_gui.html")
    
    try:
        print("Starting server on http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        app.run(debug=False, host='localhost', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Failed to start server: {e}")
        input("Press Enter to exit...")
        sys.exit(1)