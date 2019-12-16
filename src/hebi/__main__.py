# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import subprocess
import time

from jupyter_console import app


def main():
    kernel = subprocess.Popen(["python", "-m", "hebi.kernel"])

    time.sleep(1)  # TODO: this seems brittle.
    app.launch_new_instance(
        argv=["jupyter", "console", "--existing", f"kernel-{kernel.pid}.json"]
    )
    print("killing kernel")
    kernel.kill()


main()
