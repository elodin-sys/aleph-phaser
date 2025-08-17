#!/usr/bin/env python3
"""
Progress tracker for Aleph-Phaser Integration Project
Reads the IMPLEMENTATION_PLAN.md and shows current progress
"""

import re
import sys
from pathlib import Path
from datetime import datetime

def parse_checkboxes(content):
    """Parse markdown checkboxes and return statistics"""
    phases = {}
    current_phase = None
    
    lines = content.split('\n')
    for line in lines:
        # Detect phase headers
        if line.startswith('## Phase '):
            match = re.match(r'## Phase (\d+):(.*)', line)
            if match:
                phase_num = match.group(1)
                phase_name = match.group(2).strip()
                current_phase = f"Phase {phase_num}"
                phases[current_phase] = {
                    'name': phase_name,
                    'total': 0,
                    'completed': 0,
                    'items': []
                }
        
        # Count checkboxes
        if current_phase and '- [' in line:
            if '- [x]' in line or '- [X]' in line:
                phases[current_phase]['completed'] += 1
                phases[current_phase]['items'].append((True, line.strip()))
            elif '- [ ]' in line:
                phases[current_phase]['items'].append((False, line.strip()))
            phases[current_phase]['total'] += 1
    
    return phases

def print_progress(phases):
    """Print formatted progress report"""
    print("\n" + "="*60)
    print(" ALEPH-PHASER INTEGRATION PROGRESS REPORT")
    print(f" Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    total_tasks = sum(p['total'] for p in phases.values())
    total_complete = sum(p['completed'] for p in phases.values())
    
    if total_tasks > 0:
        overall_progress = (total_complete / total_tasks) * 100
    else:
        overall_progress = 0
    
    print(f"\nOVERALL PROGRESS: {total_complete}/{total_tasks} tasks ({overall_progress:.1f}%)")
    print_progress_bar(overall_progress)
    
    print("\n" + "-"*60)
    print("PHASE BREAKDOWN:")
    print("-"*60)
    
    for phase_key, phase_data in phases.items():
        if phase_data['total'] > 0:
            progress = (phase_data['completed'] / phase_data['total']) * 100
        else:
            progress = 0
        
        status = "✅ COMPLETE" if progress == 100 else "🔄 IN PROGRESS" if progress > 0 else "⏳ NOT STARTED"
        
        print(f"\n{phase_key}: {phase_data['name']}")
        print(f"Status: {status}")
        print(f"Progress: {phase_data['completed']}/{phase_data['total']} tasks ({progress:.1f}%)")
        print_progress_bar(progress, width=40)
        
        # Show next uncompleted task
        for completed, item in phase_data['items']:
            if not completed:
                task_desc = item.replace('- [ ]', '').strip()
                print(f"Next task: {task_desc[:50]}...")
                break

def print_progress_bar(percentage, width=50):
    """Print a visual progress bar"""
    filled = int(width * percentage / 100)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    print(f"[{bar}]")

def show_current_tasks(phases):
    """Show current actionable tasks"""
    print("\n" + "="*60)
    print(" CURRENT ACTION ITEMS")
    print("="*60)
    
    # Find first incomplete phase
    for phase_key, phase_data in phases.items():
        if phase_data['completed'] < phase_data['total']:
            print(f"\n{phase_key}: {phase_data['name']}")
            print("-"*40)
            
            count = 0
            for completed, item in phase_data['items']:
                if not completed and count < 5:  # Show up to 5 tasks
                    task_desc = item.replace('- [ ]', '').strip()
                    print(f"  □ {task_desc}")
                    count += 1
            
            if count > 0:
                print(f"\n  ({phase_data['total'] - phase_data['completed']} tasks remaining in this phase)")
            break
    
    print("\n" + "="*60)

def main():
    # Find the implementation plan
    plan_path = Path(__file__).parent.parent / "IMPLEMENTATION_PLAN.md"
    
    if not plan_path.exists():
        print(f"Error: Could not find {plan_path}")
        sys.exit(1)
    
    # Read and parse the plan
    with open(plan_path, 'r') as f:
        content = f.read()
    
    phases = parse_checkboxes(content)
    
    if not phases:
        print("No phases found in implementation plan")
        sys.exit(1)
    
    # Show progress
    print_progress(phases)
    show_current_tasks(phases)
    
    # Quick summary
    total_tasks = sum(p['total'] for p in phases.values())
    total_complete = sum(p['completed'] for p in phases.values())
    remaining = total_tasks - total_complete
    
    if remaining > 0:
        print(f"\n💪 Keep going! {remaining} tasks remaining.")
    else:
        print(f"\n🎉 Congratulations! All tasks complete!")

if __name__ == "__main__":
    main()
