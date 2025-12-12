from argparse import ArgumentParser
import yaml
import re

def extract_port(addr: str) -> str:
    return addr.rsplit(":", 1)[-1]




if __name__ == "__main__":
    arg_parser = ArgumentParser(description="Generate .env from hub config")
    arg_parser.add_argument(
        "--hub_config", type=str, default="configs/hub.yaml", help="Path to hub configuration YAML file"
    )
    args = arg_parser.parse_args()

    with open(args.hub_config) as f:
        cfg = yaml.safe_load(f)

    env = {}

    env["HUB_PORT"] = extract_port(cfg["zmq"]["hub_endpoint"])

    for name, fb in cfg.get("feedbacks", {}).items():
        env[f"FB_{name.upper()}_PORT"] = extract_port(fb["zmq"])

    with open(".env", "w") as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")

    print("Generated .env:")
    for k, v in env.items():
        print(f"{k}={v}")