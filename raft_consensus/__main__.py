import logging
import argparse
from dotenv import load_dotenv

from .raft_node_server import serve


def main():
    parser = argparse.ArgumentParser(description="Raft Consensus Algorithm")
    parser.add_argument(
        "-l",
        "--log-level",
        default="INFO",
        help="Set log level",
        choices=["INFO", "DEBUG", "WARNING", "ERROR"],
    )
    parser.add_argument("-v", "--verbose", action="store_true", default=True)

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)

    load_dotenv()

    serve()


if __name__ == "__main__":
    main()
