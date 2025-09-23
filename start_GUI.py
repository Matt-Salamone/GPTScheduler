#!/usr/bin/env python3
"""
Fixed debug startup script - Windows compatible with correct input format.
"""

import os
import sys
import subprocess
import time
import webbrowser
import socket

def check_port_available(port):
    """Check if a port is available."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', port))
        sock.close()
        return True
    except:
        return False

def test_flask_import():
    """Test if Flask and dependencies can be imported."""
    try:
        import flask
        print("[ OK ] Flask imported successfully")
        
        import flask_cors
        print("[ OK ] Flask-CORS imported successfully")
        
        return True
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False

def create_test_input():
    """Create a test input file to verify the scheduler works."""
    # Fixed input format with keywords
    test_content = """processcount 2
runfor 10
use fcfs
process name P1 arrival 0 burst 3
process name P2 arrival 2 burst 4
end
"""
    
    # try:
    #     with open('test_input.in', 'w') as f:
    #         f.write(test_content)
        
    #     print("[ OK ] Created test input file")
        
    #     # Try running the scheduler with it
    #     result = subprocess.run([
    #         sys.executable, 'scheduler-gpt.py', 'test_input.in'
    #     ], capture_output=True, text=True, timeout=10)
        
    #     if result.returncode == 0:
    #         print("[ OK ] Scheduler runs successfully with test input")
            
    #         # Check if output file was created
    #         if os.path.exists('test_input.out'):
    #             print("[ OK ] Scheduler created output file")
    #             with open('test_input.out', 'r') as f:
    #                 output = f.read()
    #                 # print(f"Sample output preview:")
    #                 # print("-" * 40)
    #                 # print(output[:300] + "..." if len(output) > 300 else output)
    #                 # print("-" * 40)
    #             os.remove('test_input.out')  # Clean up
    #         else:
    #             print("[WARN] Scheduler didn't create expected output file")
    #     else:
    #         print(f"[ERROR] Scheduler failed with return code {result.returncode}")
    #         print("STDERR:", result.stderr)
    #         print("STDOUT:", result.stdout)
        
    #     # Clean up
    #     if os.path.exists('test_input.in'):
    #         os.remove('test_input.in')
            
    #     return result.returncode == 0
            
    # except Exception as e:
    #     print(f"[ERROR] Error testing scheduler: {e}")
    #     return False

def main():
    """Enhanced diagnostic main function."""
    print("Process Scheduler GUI - Debug Mode")
    print("=" * 50)
    
    # Basic file checks
    print("Checking files...")
    required_files = ['scheduler-gpt.py', 'scheduler_gui.html']
    all_files_present = True
    
    for file in required_files:
        if os.path.exists(file):
            print(f"[ OK ] {file} found")
        else:
            print(f"[ERROR] {file} missing")
            all_files_present = False
    
    if not all_files_present:
        print("\n[ERROR] Missing required files. Please ensure all files are present.")
        return 1
    
    # Test imports
    print("\nTesting Python imports...")
    if not test_flask_import():
        print("\n[ERROR] Flask import failed. Install with: pip install flask flask-cors")
        return 1
    
    # Test port availability
    print(f"\nChecking port 5000...")
    if not check_port_available(5000):
        print("[ERROR] Port 5000 is already in use. Please close other applications using this port.")
        return 1
    else:
        print("[ OK ] Port 5000 is available")
    
    # Test scheduler script with corrected input format
    # print(f"\nTesting scheduler script...")
    # if not create_test_input():
    #     print("[ERROR] Scheduler test failed. There may be an issue with your scheduler-gpt.py")
    #     return 1
    
    # Try to start the fixed server
    print(f"\nAttempting to start server...")
    
    # Check for the fixed server file
    server_files = ['scheduler_server_fixed.py', 'scheduler_server.py']
    server_file = None
    
    for file in server_files:
        if os.path.exists(file):
            server_file = file
            break
    
    if not server_file:
        print("[ERROR] No server file found. Please save the server script.")
        return 1
    
    print(f"Using server file: {server_file}")
    
    try:
        print("Starting server in subprocess...")
        server_process = subprocess.Popen([
            sys.executable, server_file
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, 
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform.startswith('win') else 0)
        
        # Wait a bit for server to start
        time.sleep(3)
        
        if server_process.poll() is None:
            print("[ OK ] Server started successfully!")
            
            # Try to open browser
            try:
                webbrowser.open('http://localhost:5000')
                print("[ OK ] Browser opened automatically")
            except:
                print("Please open your browser and navigate to: http://localhost:5000")
            
            print("\n" + "="*50)
            print("         PROCESS SCHEDULER GUI READY")
            print("="*50)
            print("URL: http://localhost:5000")
            print("To stop: Close this window or press Ctrl+C")
            print("="*50)
            
            try:
                # Keep the main process running
                while server_process.poll() is None:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping server...")
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_process.kill()
                print("Server stopped")
            
            return 0
        else:
            # Server failed to start
            stdout, stderr = server_process.communicate()
            print("[ERROR] Server subprocess failed to start")
            if stdout:
                print("Output:", stdout)
            return 1
            
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")
        return 1

if __name__ == "__main__":
    try:
        result = main()
        if result != 0:
            input("Press Enter to exit...")
        sys.exit(result)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)