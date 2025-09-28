import sys
from dataclasses import dataclass, field

@dataclass
class Process:
    """Holds all information about a single process."""
    name: str
    arrival: int
    burst: int
    priority: int = 0  # Lower number means higher priority
    
    # Fields for metrics, calculated during simulation
    start_time: int = -1
    finish_time: int = -1
    wait_time: int = 0
    turnaround_time: int = 0

class Scheduler:
    """
    Handles parsing the input file, running the scheduling simulation,
    and printing the final results and metrics.
    """
    def __init__(self, filename):
        self.filename = filename
        self.processes: list[Process] = []
        self.completed_processes: list[Process] = []
        self.runfor = 0
        self.algorithm = ""

    def parse_file(self):
        """Reads the input file and populates the scheduler's configuration."""
        try:
            with open(self.filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split()
                    command = parts[0].lower()

                    if command == "processcount":
                        pass
                    elif command == "runfor":
                        self.runfor = int(parts[1])
                    elif command == "use":
                        self.algorithm = parts[1].lower()
                        if self.algorithm not in ['fcfs', 'sjf', 'priority']:
                            raise ValueError(f"Unsupported algorithm: {self.algorithm}")
                    elif command == "process":
                        name = parts[2]
                        arrival = int(parts[4])
                        burst = int(parts[6])
                        priority = int(parts[8]) if 'priority' in parts else 0
                        self.processes.append(Process(name, arrival, burst, priority))
                    elif command == "end":
                        break
            
            self.processes.sort(key=lambda p: p.arrival)
            
        except FileNotFoundError:
            print(f"Error: Input file '{self.filename}' not found.")
            sys.exit(1)
        except (ValueError, IndexError) as e:
            print(f"Error parsing input file '{self.filename}': {e}")
            sys.exit(1)

    def run(self):
        """Executes the scheduling simulation based on the chosen algorithm."""
        current_time = 0
        ready_queue: list[Process] = []
        running_process: Process | None = None
        future_processes = self.processes[:]
        
        print(f"--- Running {self.algorithm.upper()} Simulation ---")
        
        simulation_end_time = self.runfor
        if not future_processes and not ready_queue and not running_process:
             simulation_end_time = 0

        while current_time < simulation_end_time:
            arrived_now = [p for p in future_processes if p.arrival <= current_time]
            for p in arrived_now:
                ready_queue.append(p)
                future_processes.remove(p)

            if running_process is None and ready_queue:
                if self.algorithm == 'fcfs':
                    ready_queue.sort(key=lambda p: p.arrival)
                elif self.algorithm == 'sjf':
                    ready_queue.sort(key=lambda p: (p.burst, p.arrival))
                elif self.algorithm == 'priority':
                    ready_queue.sort(key=lambda p: (p.priority, p.arrival))
                
                running_process = ready_queue.pop(0)
                running_process.start_time = current_time

            if running_process:
                if current_time >= (running_process.start_time + running_process.burst):
                    running_process.finish_time = current_time
                    running_process.turnaround_time = running_process.finish_time - running_process.arrival
                    running_process.wait_time = running_process.turnaround_time - running_process.burst
                    self.completed_processes.append(running_process)
                    running_process = None

            if not future_processes and not ready_queue and not running_process:
                break
                
            current_time += 1
        
        self.completed_processes.sort(key=lambda p: p.finish_time)


    def print_results(self):
        """Prints the Gantt chart, detailed stats, and summary metrics."""
        if not self.completed_processes:
            print("\nNo processes were completed in the given time frame.")
            return

        print("\n--- Simulation Results ---")

        print("\nGantt Chart:")
        chart_str = "|"
        time_str = "0"
        last_finish_time = 0
        
        for p in self.completed_processes:
            if p.start_time > last_finish_time:
                idle_duration = p.start_time - last_finish_time
                chart_str += f" IDLE({idle_duration}) |"
                time_str += f"{' ' * (len(str(last_finish_time)))}{str(p.start_time).ljust(len(f' IDLE({idle_duration}) ') + 1)}"

            process_label = f"  {p.name}  |"
            chart_str += process_label
            time_str += f"{' ' * max(0, len(str(p.start_time)) - 1)}{str(p.finish_time).ljust(len(process_label))}"
            last_finish_time = p.finish_time
            
        print(chart_str)
        print(time_str)

        print("\nProcess Details:")
        print("-" * 80)
        print(f"{'Name':<10} {'Arrival':<10} {'Burst':<10} {'Priority':<10} {'Finish':<10} {'Turnaround':<15} {'Wait Time':<10}")
        print("-" * 80)
        for p in sorted(self.completed_processes, key=lambda p: p.name):
            print(f"{p.name:<10} {p.arrival:<10} {p.burst:<10} {p.priority:<10} {p.finish_time:<10} {p.turnaround_time:<15} {p.wait_time:<10}")
        print("-" * 80)
        
        total_wait_time = sum(p.wait_time for p in self.completed_processes)
        total_turnaround_time = sum(p.turnaround_time for p in self.completed_processes)
        total_burst_time = sum(p.burst for p in self.completed_processes)
        num_processes = len(self.completed_processes)
        last_process_finish_time = max(p.finish_time for p in self.completed_processes) if self.completed_processes else 0

        avg_wait = total_wait_time / num_processes if num_processes > 0 else 0
        avg_turnaround = total_turnaround_time / num_processes if num_processes > 0 else 0
        cpu_utilization = (total_burst_time / last_process_finish_time) * 100 if last_process_finish_time > 0 else 0

        print("\nPerformance Metrics:")
        print(f"  Average Waiting Time:      {avg_wait:.2f}")
        print(f"  Average Turnaround Time:   {avg_turnaround:.2f}")
        print(f"  CPU Utilization:           {cpu_utilization:.2f}%")
        print("-" * 35)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scheduler-gpt.py <input_file>")
        sys.exit(1)
        
    scheduler = Scheduler(sys.argv[1])
    scheduler.parse_file()
    scheduler.run()
    scheduler.print_results()
