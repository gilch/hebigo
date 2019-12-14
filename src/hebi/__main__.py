import subprocess
import time

from jupyter_console import app

kernel = subprocess.Popen(["python", "-m", "hebi.kernel"])

time.sleep(1)  # TODO: this seems brittle.
app.launch_new_instance(
    argv=["jupyter", "console", "--existing", f"kernel-{kernel.pid}.json"]
)
print("killing kernel")
kernel.kill()
