import os
import sys
import subprocess
import io
import locale

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    print("stdout:", sys.stdout.encoding)
    print("stderr:", sys.stderr.encoding)
    print("preferred:", locale.getpreferredencoding())
    # 获取项目根目录（假设 scripts 目录的上一级就是项目根目录）
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 获取环境变量，提供默认值
    config_file = os.environ.get("CONFIG_FILE", "configs/sim_gpt4omini_10s_10b_10r_runs5_base.yaml")
    model_type = os.environ.get("MODEL_TYPE", "gpt-4o-mini")
    exp_root = os.environ.get("EXP_ROOT", f"{model_type}/newresults")

    print("==========================================")
    print("RQ1: Vulnerability Intention (Reputation-Only)")
    print(f"Config: {config_file}")
    print(f"Output: experiments/{exp_root}/rq1_intent/r_wo")
    print("==========================================")

    # 构建命令
    cmd = [
        sys.executable, "./example/run_intent_probe_experiment.py",
        "--market-type", "reputation_only",
        "--output-dir", f"experiments/{exp_root}/rq1_intent/r_wo",
        "--config", config_file,
        "--reentry-allowed-round", "2"
    ]

    # 运行命令
    try:
        subprocess.run(cmd, cwd=project_root, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running RQ1: {e}")
        sys.exit(1)

    print("\nRQ1 done.")


if __name__ == "__main__":
    main()