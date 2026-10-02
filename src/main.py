import argparse

from gui import App


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vfs", default="")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--script", default="")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    App(args.vfs, args.prompt, args.script).root.mainloop()
