import os
import sys
import subprocess


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Gemini 默认配置
    config_file = os.environ.get("CONFIG_FILE", "configs/sim_gemini3f_10s_10b_10r_runs5_base.yaml")
    model_type = os.environ.get("MODEL_TYPE", "gemini-3-flash-preview")
    exp_root = f"{model_type}/paper_important_results"

    print("==========================================")
    print("Paper Experiments: New 3-RQ Pipeline (Gemini)")
    print("==========================================")
    print(f"Using config file: {config_file}")
    print(f"Model type: {model_type}")
    print(f"Experiment root: experiments/{exp_root}")

    env = os.environ.copy()
    env["CONFIG_FILE"] = config_file
    env["MODEL_TYPE"] = model_type
    env["EXP_ROOT"] = exp_root

    scripts_to_run = [
        "run_rq1_intent.py",
        "run_rq2_welfare.py",
        "run_rq3_resilience.py"
    ]

    for script in scripts_to_run:
        script_path = os.path.join(project_root, "scripts", script)
        print(f"\n>>> Executing {script} ...")
        try:
            subprocess.run([sys.executable, script_path], cwd=project_root, env=env, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing {script}: {e}")
            sys.exit(1)

    print("\n==========================================")
    print("All experiments submitted for new RQ1/RQ2/RQ3 framing.")
    print("==========================================")


if __name__ == "__main__":
    main()