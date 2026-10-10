import os
import sys
import subprocess


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    config_file = os.environ.get("CONFIG_FILE", "configs/sim_gpt4omini_10s_10b_10r_runs5_base.yaml")
    model_type = os.environ.get("MODEL_TYPE", "gpt-4o-mini")
    exp_root = os.environ.get("EXP_ROOT", f"{model_type}/newresults")

    print("==========================================")
    print("RQ3: Communication Interference & Resistance")
    print(f"Config: {config_file}")
    print(f"Output: experiments/{exp_root}/rq3_resilience")
    print("==========================================")

    markets = ["reputation_only", "reputation_and_warrant"]
    scenarios = ["platform_fee_pressure", "price_war_pressure", "financial_distress_pressure"]
    comm_types = ["Real", "Fake"]

    for comm_type in comm_types:
        comm_prefix = "R" if comm_type == "Real" else "F"
        for market in markets:
            prefix = "r" if market == "reputation_only" else "rw"

            for scenario in scenarios:
                exp_id = f"{exp_root}/rq3_resilience/{prefix}_wsc_{comm_prefix}_{scenario}"
                print(f"Running: {exp_id}")

                cmd = [
                    sys.executable, "./example/run_market_condition_experiment.py",
                    "--experiment-id", exp_id,
                    "--market-type", market,
                    "--communication", "seller",
                    "--communication-channel-type", comm_type,
                    "--config", config_file,
                    "--Posts4Seller", scenario,
                    "--disable-reentry"
                ]

                try:
                    subprocess.run(cmd, cwd=project_root, check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Error running RQ3 (Market: {market}, Scenario: {scenario}, Comm: {comm_type}): {e}")
                    sys.exit(1)

    print("\nRQ3 done.")


if __name__ == "__main__":
    main()