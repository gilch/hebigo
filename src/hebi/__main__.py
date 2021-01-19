# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import subprocess
import sys
import time

from jupyter_console import app


def main():
    print("Attempting to start Hebigo kernel without installing kernelspec.")
    kernel = subprocess.Popen([sys.executable, "-m", "hebi.kernel"])
    print("Waiting for kernel to start.")
    time.sleep(3)  # TODO: this seems brittle.
    print("Starting Jupyter Console with the most recent active kernel...")
    app.launch_new_instance(argv=["jupyter", "console", "--existing"])
    print("Console exit. Terminating Hebigo kernel.")
    kernel.kill()


if __name__ == "__main__":
    main()
