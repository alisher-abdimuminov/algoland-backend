import os
import time
import json
import django
import shutil
import difflib
import zipfile
import subprocess
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from problems.models import (
    Language,
    Attempt,
)

class Workspace:
    def __init__(self, name: str):
        self.name = name
        self.cwd = f"{os.getcwd()}/workspaces/{self.name}"

    def init(self):
        """
        init() -> Create workspace folder with named self.name
        """
        try:
            os.mkdir(f"workspaces/{self.name}")
        except Exception as e:
            print("[ERROR]:can not init workspace.")

    def add_file(self, file_name: str, content: str):
        """
        add_file(file_name, content) -> Create file in the workspace and write content to file

        file_name - string
        content - string
        """
        with open(f"workspaces/{self.name}/{file_name}", "w") as file:
            if file.writable():
                file.write(str(content))

    def copy(self, from_path: str):
        """
        copy(from_path) -> Copy from_path to workspace

        from_path - string
        """
        shutil.copy(from_path, f"workspaces/{self.name}")

    def read(self, file_name: str):
        with open(f"workspaces/{self.name}/{file_name}", "r") as o:
            return Sandbox.clean(o.read())
        
    def clean(self):
        """
        clean() -> Delete workspace
        """
        shutil.rmtree(f"workspaces/{self.name}")


SANDBOX_VERDICTS = {
    "wc": "Wating for Compilation",
    "dce": "Dangerous Code Error",
    "cc": "Compilation Completed",
    "cle": "Compilation Limit Exceeded",
    "re": "Runtime Error",
    "tle": "Time Limit Exceeded",
    "mle": "Memory Limit Exceeded",
    "ole": "Output Limit Exceeded",
    "ac": "Accepted",
    "sig": "Runtime Error",
}

JUDEGE_VERDICTS = {
    "ce": "Compilation Error",
    "cle": "Compilation Limit Exceeded",
    "re": "Runtime Error",
    "tle": "Time Limit Exceeded",
    "mle": "Memory Limit Exceeded",
    "ole": "Output Limit Exceeded",
    "pe": "Presentation Error",
    "wa": "Wrong Answer",
    "ac": "Accepted",
    "je": "Judge Error",
}

class RESPONSE:
    status: str
    stderr: str
    stdout: str
    stdin: str
    expected: str
    diff: str
    time: float
    memory: str
    test: int

class Sandbox:
    def __init__(self, workspace: Workspace, language: Language, stdin: str, time_limit: int = 5, memory_limit: int = 64):
        self.workspace = workspace
        self.language = language
        self.stdin = stdin
        self.time_limit = time_limit
        self.memory_limit = memory_limit * 1000

    def parse_command(self, type: str = "compile"):
        return self.language.parse_command(type, **{ "cwd": self.workspace.cwd, "file": self.language.file })

    def clean(self, text: str):
        if text:
            return text.strip()
        return text
    
    @classmethod
    def clean(cls, text: str):
        if text:
            return text.strip()
        return text
    
    def parse_meta(self):
        meta = {}
        with open(f"workspaces/{self.workspace.name}/meta.json", "r") as meta_file:
            meta = json.load(meta_file)
        return {
            "time": meta.get("time", 0),
            "memory": meta.get("memory", 0),
            "exit_code": meta.get("exit_code", 0),
        }

    def compile(self):
        # start compiling...
        # send compiling to client
        start_time = time.time()
        status = "wc"
        stdout = ""
        stderr = ""

        try:
            print(self.parse_command("compile"))
            result = subprocess.run(
                self.parse_command("compile").split(),
                cwd=self.workspace.cwd,
                timeout=5,
                text=True,
                capture_output=True
            )
            stderr = result.stderr
            stdout = result.stdout
            status = "cc" if not stderr else "ce"
            elapsed_time = round((time.time() - start_time) * 1000, 2)
        except subprocess.TimeoutExpired:
            status = "cle"
            stderr = ""
            stdout = ""
            elapsed_time = round((time.time() - start_time) * 1000, 2)
        response = {
            "status": status,
            "stderr": stderr,
            "stdout": stdout,
            "stdin": "",
            "expected": "",
            "time": elapsed_time,
            "memory": 0,
            "test": 0,
        }
        return response
        # end compiling.
    
    def run(self):
        if self.language.type == "compiled":
            compile = self.compile()
            if compile.get("status") == "ce" or compile.get("status") == "cle":
                return compile
        
        start_time = time.time()
        status = "wc"
        stdout = ""
        stderr = ""
        memory = 0
        
        try:
            result = subprocess.run(
                self.parse_command("run").split(),
                cwd=self.workspace.cwd,
                timeout=self.time_limit,
                text=True,
                capture_output=True,
                input=self.stdin,
            )
            stderr = self.workspace.read("error.txt")
            stdout = self.workspace.read("output.txt")
            elapsed_time = round((time.time() - start_time) * 1000, 2)
            meta = self.parse_meta()
            memory = meta.get("memory")

            if result.stdout == "danger":
                status = "dce"

            elif meta.get("memory") > self.memory_limit:
                status = "mle"

            elif stderr:
                status = "re"

            else:
                status = "ac"
        except subprocess.TimeoutExpired:
            stderr = ""
            stdout = ""
            status = "tle"
            elapsed_time = round((time.time() - start_time) * 1000, 2)
        
        response = {
            "status": status,
            "stderr": stderr,
            "stdout": stdout,
            "stdin": self.stdin,
            "expected": "",
            "time": elapsed_time,
            "memory": memory,
            "test": 0,
        }
        return response



class Judge:
    def __init__(self, attempt: Attempt):
        self.attempt = attempt
        self.workspace = Workspace(name=str(attempt.uuid))
        self.language = attempt.language
        self.time_limit = self.attempt.problem.time_limit
        self.memory_limit = self.attempt.problem.memory_limit * 1000
        self.channel_layer = channel_layer = get_channel_layer()
        self.cases = []

        self.workspace.init()
        self.workspace.add_file(self.language.file, self.attempt.code)
        self.workspace.copy(self.language.sandbox)

    def tests(self):
        archive = zipfile.ZipFile(self.attempt.problem.tests.path, "r")

        tests = []

        for test in archive.filelist:
            if not test.is_dir():
                tests.append(test.filename)

        return [tests[i:i + 2] for i in range(0, len(tests), 2)]

    def parse_command(self, type: str = "compile"):
        return self.language.parse_command(type, **{ "cwd": self.workspace.cwd, "file": self.language.file })

    def clean(self, text: str):
        if text:
            if text[-1] == "\n":
                return text[:-1]
        return text
    
    @classmethod
    def clean(cls, text: str):
        if text:
            return text.strip()
        return text
    
    def parse_meta(self):
        meta = {}
        with open(f"workspaces/{self.workspace.name}/meta.json", "r") as meta_file:
            meta = json.load(meta_file)
        return {
            "time": meta.get("time", 0),
            "memory": meta.get("memory", 0),
            "exit_code": meta.get("exit_code", 0),
            "signal": meta.get("signal", 0),
        }

    def compile(self):
        # start compiling...
        # send compiling to client
        start_time = time.time()
        status = "wc"
        stdout = ""
        stderr = ""

        try:
            print(self.parse_command("compile"))
            result = subprocess.run(
                self.parse_command("compile").split(),
                cwd=self.workspace.cwd,
                timeout=5,
                text=True,
                capture_output=True
            )
            stderr = result.stderr
            stdout = result.stdout
            status = "cc" if not stderr else "ce"
            elapsed_time = round((time.time() - start_time) * 1000, 2)
        except subprocess.TimeoutExpired:
            status = "cle"
            stderr = ""
            stdout = ""
            elapsed_time = round((time.time() - start_time) * 1000, 2)
        response = {
            "status": status,
            "stderr": stderr,
            "stdout": stdout,
            "stdin": "",
            "expected": "",
            "time": elapsed_time,
            "memory": 0,
            "test": 0,
        }
        return response
        # end compiling.
    
    def run(self):
        if self.language.type == "compiled":
            compile = self.compile()
            if compile.get("status") == "ce" or compile.get("status") == "cle":
                async_to_sync(self.channel_layer.group_send)(
                    f"user_{self.attempt.author.pk}",
                    {
                        "type": "attempt_case",
                        "data": {
                            "status": compile.get("status"),
                            "time": compile.get("time"),
                            "memory": compile.get("memory"),
                            "stderr": compile.get("stderr"),
                            "test": 0,
                        }
                    }
                )
                self.attempt.status = compile.get("status")
                self.attempt.time = compile.get("time")
                self.attempt.memory = compile.get("memory")
                self.attempt.error = compile.get("stderr")
                self.attempt.test = 0
                self.attempt.cases = compile
                self.attempt.save()
                return compile
        
        start_time = time.time()
        status = "wc"
        stdout = ""
        stderr = ""
        memory = 0
        e_time = 0
        
        archive = zipfile.ZipFile(self.attempt.problem.tests.path, "r")

        for index, test in enumerate(self.tests()):
            try:
                if len(test) == 2:
                    input, output = test
                    input = archive.read(input).decode()
                    output = archive.read(output).decode()

                    try:
                        result = subprocess.run(
                            self.parse_command("run").split(),
                            cwd=self.workspace.cwd,
                            timeout=3,
                            text=True,
                            capture_output=True,
                            input=input,
                        )
                        elapsed_time = round((time.time() - start_time) * 1000, 2)
                        stderr = self.workspace.read("error.txt")
                        stdout = self.workspace.read("output.txt")
                        meta = self.parse_meta()
                        memory = meta.get("memory")
                        e_time = meta.get("time")
                        exit_code = meta.get("exit_code")
                        signal = meta.get("signal")

                        # Kill with dangerous code error
                        if meta.get("signal") != 0:
                            if signal == 9 and e_time > (self.time_limit) * 1000:
                                status = "tle"
                                response = {
                                    "status": status,
                                    "stderr": stderr,
                                    "stdout": stdout,
                                    "stdin": input,
                                    "expected": output,
                                    "diff": "",
                                    "time": e_time,
                                    "memory": memory,
                                    "test": index + 1,
                                }
                                async_to_sync(self.channel_layer.group_send)(
                                    f"user_{self.attempt.author.pk}",
                                    {
                                        "type": "attempt_case",
                                        "data": {
                                            "problem": str(self.attempt.problem.uuid),
                                            "attempt": str(self.attempt.uuid),
                                            "status": response.get("status"),
                                            "time": response.get("time"),
                                            "memory": response.get("memory"),
                                            "stderr": response.get("stderr"),
                                            "test": index + 1,
                                        }
                                    }
                                )
                                self.cases.append(response)

                                self.attempt.status = status
                                self.attempt.time = e_time
                                self.attempt.memory = memory
                                self.attempt.error = stderr
                                self.attempt.test = index + 1
                                self.attempt.cases = self.cases
                                self.attempt.save()
                                print(response)
                                return
                            status = "dce"
                            response = {
                                "status": status,
                                "stderr": stderr,
                                "stdout": stdout,
                                "stdin": input,
                                "diff": "",
                                "expected": output,
                                "time": e_time,
                                "memory": memory,
                                "test": index + 1,
                            }
                            async_to_sync(self.channel_layer.group_send)(
                                f"user_{self.attempt.author.pk}",
                                {
                                    "type": "attempt_case",
                                    "data": {
                                        "problem": str(self.attempt.problem.uuid),
                                        "attempt": str(self.attempt.uuid),
                                        "status": response.get("status"),
                                        "time": response.get("time"),
                                        "memory": response.get("memory"),
                                        "stderr": response.get("stderr"),
                                        "test": index + 1,
                                    }
                                }
                            )
                            self.cases.append(response)

                            self.attempt.status = status
                            self.attempt.time = e_time
                            self.attempt.memory = memory
                            self.attempt.error = stderr
                            self.attempt.test = index + 1
                            self.attempt.cases = self.cases
                            self.attempt.save()
                            print(response)
                            return
                        # Kill with memory limit exceeded
                        elif memory > self.memory_limit:
                            status = "mle"
                            response = {
                                "status": status,
                                "stderr": stderr,
                                "stdout": stdout,
                                "stdin": input,
                                "diff": "",
                                "expected": output,
                                "time": e_time,
                                "memory": memory,
                                "test": index + 1,
                            }
                            async_to_sync(self.channel_layer.group_send)(
                                f"user_{self.attempt.author.pk}",
                                {
                                    "type": "attempt_case",
                                    "data": {
                                        "problem": str(self.attempt.problem.uuid),
                                        "attempt": str(self.attempt.uuid),
                                        "status": response.get("status"),
                                        "time": response.get("time"),
                                        "memory": response.get("memory"),
                                        "stderr": response.get("stderr"),
                                        "test": index + 1,
                                    }
                                }
                            )
                            self.cases.append(response)

                            self.attempt.status = status
                            self.attempt.time = e_time
                            self.attempt.memory = memory
                            self.attempt.error = stderr
                            self.attempt.test = index + 1
                            self.attempt.cases = self.cases
                            self.attempt.save()
                            print(response)
                            return
                        # Kill with time limit exceeded
                        elif e_time > (self.time_limit) * 1000:
                            status = "tle"
                            response = {
                                "status": status,
                                "stderr": stderr,
                                "stdout": stdout,
                                "stdin": input,
                                "expected": output,
                                "diff": "",
                                "time": e_time,
                                "memory": memory,
                                "test": index + 1,
                            }
                            async_to_sync(self.channel_layer.group_send)(
                                f"user_{self.attempt.author.pk}",
                                {
                                    "type": "attempt_case",
                                    "data": {
                                        "problem": str(self.attempt.problem.uuid),
                                        "attempt": str(self.attempt.uuid),
                                        "status": response.get("status"),
                                        "time": response.get("time"),
                                        "memory": response.get("memory"),
                                        "stderr": response.get("stderr"),
                                        "test": index + 1,
                                    }
                                }
                            )
                            self.cases.append(response)

                            self.attempt.status = status
                            self.attempt.time = e_time
                            self.attempt.memory = memory
                            self.attempt.error = stderr
                            self.attempt.test = index + 1
                            self.attempt.cases = self.cases
                            self.attempt.save()
                            print(response)
                            return
                        # Kill with runtime error
                        elif stderr:
                            status = "re"
                            response = {
                                "status": status,
                                "stderr": stderr,
                                "stdout": stdout,
                                "stdin": input,
                                "expected": output,
                                "diff": "",
                                "time": e_time,
                                "memory": memory,
                                "test": index + 1,
                            }
                            async_to_sync(self.channel_layer.group_send)(
                                f"user_{self.attempt.author.pk}",
                                {
                                    "type": "attempt_case",
                                    "data": {
                                        "problem": str(self.attempt.problem.uuid),
                                        "attempt": str(self.attempt.uuid),
                                        "status": response.get("status"),
                                        "time": response.get("time"),
                                        "memory": response.get("memory"),
                                        "stderr": response.get("stderr"),
                                        "test": index + 1,
                                    }
                                }
                            )
                            self.cases.append(response)

                            self.attempt.status = status
                            self.attempt.time = e_time
                            self.attempt.memory = memory
                            self.attempt.error = stderr
                            self.attempt.test = index + 1
                            self.attempt.cases = self.cases
                            self.attempt.save()
                            print(response)
                            return
                        # Kill with presentation error
                        elif stdout.strip() == output.strip() and stdout != output:
                            diff = difflib.ndiff(stdout.splitlines(), output.splitlines())
                            status = "pe"
                            response = {
                                "status": status,
                                "stderr": stderr,
                                "stdout": stdout,
                                "stdin": input,
                                "expected": output,
                                "diff": "\n".join(diff),
                                "time": e_time,
                                "memory": memory,
                                "test": index + 1,
                            }
                            async_to_sync(self.channel_layer.group_send)(
                                f"user_{self.attempt.author.pk}",
                                {
                                    "type": "attempt_case",
                                    "data": {
                                        "problem": str(self.attempt.problem.uuid),
                                        "attempt": str(self.attempt.uuid),
                                        "status": response.get("status"),
                                        "time": response.get("time"),
                                        "memory": response.get("memory"),
                                        "stderr": response.get("stderr"),
                                        "test": index + 1,
                                    }
                                }
                            )
                            self.cases.append(response)

                            self.attempt.status = status
                            self.attempt.time = e_time
                            self.attempt.memory = memory
                            self.attempt.error = stderr
                            self.attempt.test = index + 1
                            self.attempt.cases = self.cases
                            self.attempt.save()
                            print(response)
                            return
                        # Kill with wrong answer
                        elif stdout != output:
                            diff = difflib.ndiff(stdout.splitlines(), output.splitlines())
                            status = "wa"
                            response = {
                                "status": status,
                                "stderr": stderr,
                                "stdout": stdout,
                                "stdin": input,
                                "expected": output,
                                "diff": "\n".join(diff),
                                "time": e_time,
                                "memory": memory,
                                "test": index + 1,
                            }
                            async_to_sync(self.channel_layer.group_send)(
                                f"user_{self.attempt.author.pk}",
                                {
                                    "type": "attempt_case",
                                    "data": {
                                        "problem": str(self.attempt.problem.uuid),
                                        "attempt": str(self.attempt.uuid),
                                        "status": response.get("status"),
                                        "time": response.get("time"),
                                        "memory": response.get("memory"),
                                        "stderr": response.get("stderr"),
                                        "test": index + 1,
                                    }
                                }
                            )
                            self.cases.append(response)
                            
                            self.attempt.status = status
                            self.attempt.time = e_time
                            self.attempt.memory = memory
                            self.attempt.error = stderr
                            self.attempt.test = index + 1
                            self.attempt.cases = self.cases
                            self.attempt.save()
                            print(response)
                            return
                        elif stdout == output:
                            diff = difflib.ndiff(stdout.splitlines(), output.splitlines())
                            status = "ac"
                            response = {
                                "status": status,
                                "stderr": stderr,
                                "stdout": stdout,
                                "stdin": input,
                                "expected": output,
                                "diff": "\n".join(diff),
                                "time": e_time,
                                "memory": memory,
                                "test": index + 1,
                            }
                            async_to_sync(self.channel_layer.group_send)(
                                f"user_{self.attempt.author.pk}",
                                {
                                    "type": "attempt_case",
                                    "data": {
                                        "problem": str(self.attempt.problem.uuid),
                                        "attempt": str(self.attempt.uuid),
                                        "status": response.get("status"),
                                        "time": response.get("time"),
                                        "memory": response.get("memory"),
                                        "stderr": None,
                                        "test": index + 1,
                                    }
                                }
                            )
                            self.cases.append(response)
                            self.attempt.cases = self.cases
                            self.attempt.save()
                            print(response)
                        else:
                            status = "je"
                            response = {
                                "status": status,
                                "stderr": stderr,
                                "stdout": stdout,
                                "stdin": input,
                                "expected": output,
                                "time": e_time,
                                "memory": memory,
                                "test": index + 1,
                            }
                            async_to_sync(self.channel_layer.group_send)(
                                f"user_{self.attempt.author.pk}",
                                {
                                    "type": "attempt_case",
                                    "data": {
                                        "problem": str(self.attempt.problem.uuid),
                                        "attempt": str(self.attempt.uuid),
                                        "status": response.get("status"),
                                        "time": response.get("time"),
                                        "memory": response.get("memory"),
                                        "stderr": response.get("stderr"),
                                        "test": index + 1,
                                    }
                                }
                            )
                            self.cases.append(response)

                            self.attempt.status = status
                            self.attempt.time = e_time
                            self.attempt.memory = memory
                            self.attempt.error = stderr
                            self.attempt.test = index + 1
                            self.attempt.cases = self.cases
                            self.attempt.save()
                            print(response)
                            return
                    except subprocess.TimeoutExpired:
                        status = "tle"
                        meta = self.parse_meta()
                        memory = meta.get("memory")
                        e_time = meta.get("time")
                        response = {
                            "status": status,
                            "stderr": stderr,
                            "stdout": stdout,
                            "stdin": input,
                            "expected": output,
                            "time": e_time,
                            "memory": memory,
                            "test": index + 1,
                        }
                        async_to_sync(self.channel_layer.group_send)(
                            f"user_{self.attempt.author.pk}",
                            {
                                "type": "attempt_case",
                                "data": {
                                    "problem": str(self.attempt.problem.uuid),
                                    "attempt": str(self.attempt.uuid),
                                    "attempt": str(self.attempt.uuid),
                                    "status": response.get("status"),
                                    "time": response.get("time"),
                                    "memory": response.get("memory"),
                                    "stderr": response.get("stderr"),
                                    "test": index + 1,
                                }
                            }
                        )
                        self.cases.append(response)

                        self.attempt.status = status
                        self.attempt.time = e_time
                        self.attempt.memory = memory
                        self.attempt.error = stderr
                        self.attempt.test = index + 1
                        self.attempt.cases = self.cases
                        self.attempt.save()
                        print(response)
                        return
                    except Exception as e:
                        print(e)
                else:
                    continue
            except Exception as e:
                print(e)
        async_to_sync(self.channel_layer.group_send)(
            f"user_{self.attempt.author.pk}",
            {
                "type": "attempt_status",
                "data": {
                    "problem": str(self.attempt.problem.uuid),
                    "attempt": str(self.attempt.uuid),
                    "status": status,
                    "time": e_time,
                    "memory": memory,
                    "stderr": stderr,
                }
            }
        )
        self.attempt.status = status
        self.attempt.time = e_time
        self.attempt.memory = memory
        self.attempt.error = stderr
        self.attempt.save()
