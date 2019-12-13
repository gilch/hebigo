from typing import Optional

from ipykernel.kernelbase import Kernel

from hebi import parser


class HebigoKernel(Kernel):
    implementation = "hebigo"
    implementation_version = "hebigo"
    language = "hebigo"
    language_version = "hebigo"
    banner = "hebigo"

    language_info = {"mimetype": "text/hebigo", "file_extension": "hebi"}

    def do_execute(
        self,
        code: str,
        silent: bool,
        store_history: bool = True,
        user_expressions: Optional[dict] = None,
        allow_stdin: bool = False,
    ):
        """
        code (str) – The code to be executed.
        silent (bool) – Whether to display output.
        store_history (bool) – Whether to record this code in history
            and increase the execution count. If silent is True, this
            is implicitly False.
        user_expressions (dict) – Mapping of names to expressions to
            evaluate after the code has run. You can ignore this if
            you need to.
        allow_stdin (bool) – Whether the frontend can provide input on
            request (e.g. for Python’s raw_input()).

        returns a dict containing the fields described in Execution
        results.
        """
        # To display output, it can send messages using
        # send_response(). See Messaging in IPython for details of the
        # different message types.
        result = str(list(parser.reads(code)))
        if not silent:
            stream_content = {'name': 'stdout', 'text': result}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        return {
            'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],  # Deprecated?
            'user_expressions': {},  # Unused?
        }

    def do_is_complete(self, code: str):
        status = 'incomplete'
        if ':' not in code or code.endswith('\n'):
            status = 'complete'
        try:
            list(parser.reads(code))
        except:
            status = 'incomplete'
        assert status in {'complete', 'incomplete', 'invalid', 'unknown'}
        return {'status': status}


if __name__ == "__main__":
    from ipykernel.kernelapp import IPKernelApp

    IPKernelApp.launch_instance(kernel_class=HebigoKernel)
