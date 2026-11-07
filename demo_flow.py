"""Guided demo by default; explicit --stage/--batch preserves batch execution."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['all','calibration','registration','planning','targeting'])
    parser.add_argument('--trials', type=int, default=500)
    parser.add_argument('--targeting-trials', type=int, default=200000)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--batch', action='store_true', help='Regenerate results without prompts/windows')
    mode.add_argument('--interactive', action='store_true', help='Guided walkthrough (default without --stage)')
    args = parser.parse_args()
    if args.interactive and args.stage:
        parser.error('--interactive shows the full walkthrough; omit --stage')
    if args.batch or args.stage:
        subprocess.run([sys.executable, str(ROOT/'batch_demo.py'), '--stage', args.stage or 'all',
                        '--trials', str(args.trials), '--targeting-trials', str(args.targeting_trials)],
                       cwd=ROOT, check=True)
    else:
        from interactive_demo import main as guided_main
        guided_main()


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\nDemonstration stopped.')
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f'Batch calculation failed with exit code {exc.returncode}.', file=sys.stderr)
        sys.exit(exc.returncode)

# Author: Serhat Yaylacam
