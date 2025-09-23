#!/usr/bin/env python3
"""
Flask web server that provides a REST API for the Process Scheduler GUI.
This server interfaces with your existing scheduler-gpt.py code.
"""

import os
import sys
import tempfile
import subprocess
import json
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Path to your scheduler script
SCHEDULER_SCRIPT = "scheduler-gpt.py"

def validate_scheduler_script():
    """Check if the scheduler script exists and is executable."""
    if not os.path.isfile(SCHEDULER_SCRIPT):
        raise FileNotFoundError(f"Scheduler script '{SCHEDULER_SCRIPT}' not found in current directory")
    return True

def create_input_file(input_content):
    """Create a temporary input file for the scheduler."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.in', delete=False) as f:
        f.write(input_content)
        return f.name

def run_scheduler(input_file_path):
    """Execute the scheduler script with the given input file."""
    try:
        # Run the scheduler script
        result = subprocess.run(
            [sys.executable, SCHEDULER_SCRIPT, input_file_path],
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        if result.returncode != 0:
            return None, f"Scheduler error: {result.stderr or 'Unknown error'}"
        
        # Read the output file
        base_name = os.path.splitext(os.path.basename(input_file_path))[0]
        output_file_path = f"{base_name}.out"
        
        if not os.path.exists(output_file_path):
            return None, "Scheduler did not generate output file"
        
        with open(output_file_path, 'r') as f:
            output_content = f.read()
        
        # Clean up the output file
        os.remove(output_file_path)
        
        return output_content, None
        
    except subprocess.TimeoutExpired:
        return None, "Scheduler execution timed out"
    except Exception as e:
        return None, f"Execution error: {str(e)}"

def parse_scheduler_output(output_content):
    """Parse the scheduler output into structured data for the frontend."""
    lines = output_content.strip().split('\n')
    
    # Extract algorithm and simulation info
    algorithm_line = lines[0] if lines else ""
    simulation_line = lines[1] if len(lines) > 1 else ""
    
    # Parse timeline events
    timeline = []
    finished_processes = []
    unfinished_processes = []
    
    print(f"Parsing output with {len(lines)} lines")
    
    # Parse the timeline section
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        print(f"Processing line {i}: {line}")
        
        if line.startswith("Time "):
            # Parse time tick line: "Time   0 : P1 arrived"
            time_match = re.match(r"Time\s+(\d+)\s*:\s*(.*)", line)
            if time_match:
                time_tick = int(time_match.group(1))
                events_text = time_match.group(2).strip()
                
                # Parse events from the line
                events = []
                running_process = "IDLE"
                ready_queue = []
                
                # Extract events like "P1 arrived", "P2 selected", etc.
                if events_text:
                    events.append(events_text)
                    
                    # Determine running process
                    if "selected" in events_text:
                        # Extract process name from "P1 selected (burst 3)"
                        process_match = re.search(r"(\w+)\s+selected", events_text)
                        if process_match:
                            running_process = process_match.group(1)
                    elif "finished" in events_text or events_text == "Idle":
                        running_process = "IDLE"
                
                timeline.append({
                    'time': time_tick,
                    'running': running_process,
                    'ready_queue': ready_queue,
                    'events': events
                })
        
        elif line.startswith("P") and ("wait" in line.lower() or "turnaround" in line.lower()):
            # Parse final metrics: "P1 wait 0 turnaround 3 response 0"
            process_match = re.search(r"(\w+)\s+wait\s+(\d+)\s+turnaround\s+(\d+)\s+response\s+(\d+)", line)
            if process_match:
                finished_processes.append({
                    'name': process_match.group(1),
                    'wait_time': int(process_match.group(2)),
                    'turnaround_time': int(process_match.group(3)),
                    'response_time': int(process_match.group(4))
                })
        
        elif "did not finish" in line:
            # Parse unfinished processes
            process_name = line.split()[0]
            unfinished_processes.append({'name': process_name})
        
        i += 1
    
    result = {
        'algorithm': algorithm_line,
        'simulation_info': simulation_line,
        'timeline': timeline,
        'finished_processes': finished_processes,
        'unfinished_processes': unfinished_processes,
        'raw_output': output_content
    }
    
    print(f"Parsed result: {json.dumps(result, indent=2)}")
    return result

@app.route('/')
def index():
    """Serve the main GUI page."""
    return send_from_directory('.', 'scheduler_gui.html')

@app.route('/api/simulate', methods=['POST'])
def simulate():
    """API endpoint to run the scheduler simulation."""
    try:
        # Validate that the scheduler script exists
        validate_scheduler_script()
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        input_content = data.get('input_content')
        if not input_content:
            return jsonify({'error': 'No input content provided'}), 400
        
        # Create temporary input file
        input_file_path = None
        try:
            input_file_path = create_input_file(input_content)
            
            # Run the scheduler
            output_content, error = run_scheduler(input_file_path)
            
            if error:
                return jsonify({'error': error}), 400
            
            # Parse the output
            parsed_output = parse_scheduler_output(output_content)
            
            print(f"Sending response with {len(output_content)} chars of output")
            
            return jsonify({
                'success': True,
                'output': output_content,
                'parsed': parsed_output
            })
            
        finally:
            # Clean up temporary file
            if input_file_path and os.path.exists(input_file_path):
                os.remove(input_file_path)
                
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint to verify the server is running."""
    try:
        validate_scheduler_script()
        return jsonify({
            'status': 'ok',
            'message': 'Server is running and scheduler script is available',
            'scheduler_script': SCHEDULER_SCRIPT
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/validate-config', methods=['POST'])
def validate_config():
    """Validate a configuration without running the simulation."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Basic validation
        processes = data.get('processes', [])
        algorithm = data.get('algorithm', 'fcfs')
        runfor = data.get('runfor', 20)
        
        errors = []
        warnings = []
        
        # Validate processes
        if len(processes) == 0:
            errors.append('At least one process is required')
        
        for i, process in enumerate(processes):
            if not process.get('name'):
                errors.append(f'Process {i+1} must have a name')
            
            if process.get('burst_time', 0) <= 0:
                errors.append(f'Process {process.get("name", i+1)} must have a positive burst time')
            
            if process.get('arrival_time', 0) < 0:
                errors.append(f'Process {process.get("name", i+1)} cannot have negative arrival time')
            
            # Algorithm-specific validation
            if algorithm == 'stride' and process.get('tickets', 0) <= 0:
                errors.append(f'Process {process.get("name", i+1)} must have positive tickets for Stride scheduling')
        
        # Check if any process will finish within the time limit
        min_arrival = min(p.get('arrival_time', 0) for p in processes) if processes else 0
        min_burst = min(p.get('burst_time', 1) for p in processes) if processes else 1
        
        if min_arrival + min_burst > runfor:
            warnings.append('Simulation time may be too short for any process to complete')
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        })
        
    except Exception as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 500

if __name__ == '__main__':
    # Check if scheduler script exists before starting server
    try:
        validate_scheduler_script()
        print(f"✓ Scheduler script '{SCHEDULER_SCRIPT}' found")
        print("Starting Process Scheduler GUI Server...")
        print("Open your browser and navigate to: http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        
        app.run(debug=True, host='localhost', port=5000)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(f"Please ensure '{SCHEDULER_SCRIPT}' is in the same directory as this server script.")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)