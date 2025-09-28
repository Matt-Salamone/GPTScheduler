To run the test bench...
run "python test_bench.py [PATH_TO_TESTFILES]"
e.g., "python test_bench.py ./pa1-testfiles-1"

To run the GUI...

pip install -r Flask

Run the backend: python start_GUI.py

The GUI should automatically open in your browser

To run better log:
 $env:SCHEDULER_VERBOSE_LOG = '1'; python scheduler-gpt.py {INPUT}; $env:SCHEDULER_VERBOSE_LOG = $null