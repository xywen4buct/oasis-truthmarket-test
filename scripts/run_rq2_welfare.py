import os
import sys
import subprocess


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    config_file = os.environ.get("CONFIG_FILE", "configs/sim_gpt4omini_10s_10b_10r_runs5_base.yaml")
    model_type = os.environ.get("MODEL_TYPE", "gpt-4o-mini")
    exp_root = os.environ.get("EXP_ROOT", f"{model_type}/newresults")

    print("==========================================")
    print("RQ2: Warrant Welfare (No Communication)")
    print(f"Config: {config_file}")
    print(f"Output: experiments/{exp_root}/rq2_welfare")
    print("==========================================")

    # 命令1：reputation_only
    cmd1 = [
        sys.executable, "./example/run_market_condition_experiment.py",
        "--experiment-id", f"{exp_root}/rq2_welfare/r_wo",
        "--market-type", "reputation_only",
        "--communication", "none",
        "--communication-channel-type", "Fake",
        "--config", config_file,
        "--disable-reentry"
    ]

    # 命令2：reputation_and_warrant
    cmd2 = [
        sys.executable, "./example/run_market_condition_experiment.py",
        "--experiment-id", f"{exp_root}/rq2_welfare/rw_wo",
        "--market-type", "reputation_and_warrant",
        "--communication", "none",
        "--communication-channel-type", "Fake",
        "--config", config_file,
        "--disable-reentry"
    ]

    try:
        print("Running Reputation-Only condition...")
        subprocess.run(cmd1, cwd=project_root, check=True)

        print("Running Reputation+Warrant condition...")
        subprocess.run(cmd2, cwd=project_root, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running RQ2: {e}")
        sys.exit(1)

    print("\nRQ2 done.")


if __name__ == "__main__":
    main()