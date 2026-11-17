"""Bound product subprocesses, retain sanitized diagnostics and clean only owned descendants."""
from __future__ import annotations
import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from evidence_redaction import sanitized


class LinuxTree:
    def __init__(self):
        self.libc = ctypes.CDLL(None, use_errno=True)
        previous = ctypes.c_int()
        if self.libc.prctl(37, ctypes.byref(previous), 0, 0, 0) or self.libc.prctl(36, 1, 0, 0, 0):
            raise OSError(ctypes.get_errno(), 'Cannot establish owned child supervision')
        self.previous = previous.value
        self.baseline = self.children(os.getpid())

    @staticmethod
    def children(pid):
        found = set()
        for file in Path('/proc', str(pid), 'task').glob('*/children'):
            try: found.update(map(int, file.read_text().split()))
            except FileNotFoundError: pass
        return found

    @staticmethod
    def identity(pid):
        try: return Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
        except (FileNotFoundError, ProcessLookupError): return None

    def owned(self, child):
        pending = ({child.pid} if child.returncode is None else set()) | (self.children(os.getpid()) - self.baseline)
        result = {}
        while pending:
            pid = pending.pop()
            if pid in result or pid == os.getpid(): continue
            identity = self.identity(pid)
            if identity is None: continue
            result[pid] = identity
            pending.update(self.children(pid))
        return result

    def close(self, child, grace):
        try:
            deadline = time.monotonic() + grace
            while True:
                child.poll()
                owned = self.owned(child)
                if not owned: break
                current_signal = signal.SIGTERM if time.monotonic() < deadline else signal.SIGKILL
                for pid, identity in owned.items():
                    if self.identity(pid) == identity:
                        try: os.kill(pid, current_signal)
                        except ProcessLookupError: pass
                for pid in owned:
                    if pid != child.pid:
                        try: os.waitpid(pid, os.WNOHANG)
                        except ChildProcessError: pass
                if time.monotonic() > deadline + 5:
                    raise RuntimeError('Owned product descendants did not stop within cleanup grace.')
                time.sleep(.02)
            child.wait(timeout=5)
        finally:
            self.libc.prctl(36, self.previous, 0, 0, 0)


class PosixGroup:
    def close(self, child, grace):
        try: os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError: pass
        try: child.wait(timeout=grace)
        except subprocess.TimeoutExpired: pass
        try: os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        child.wait(timeout=5)
        deadline = time.monotonic() + 5
        while True:
            try: os.killpg(child.pid, 0)
            except ProcessLookupError: break
            if time.monotonic() >= deadline:
                raise RuntimeError('Owned product process group remained after SIGKILL.')
            time.sleep(.02)


class WindowsJob:
    """The gated child cannot create descendants until assigned to this non-breakaway job."""
    def __init__(self):
        from ctypes import c_uint32 as DWORD, c_uint64 as QWORD, c_size_t as SIZE, c_int64 as LARGE
        class Basic(ctypes.Structure):
            _fields_ = [('process_time', LARGE), ('job_time', LARGE), ('flags', DWORD),
                        ('minimum', SIZE), ('maximum', SIZE), ('active_limit', DWORD),
                        ('affinity', SIZE), ('priority', DWORD), ('scheduling', DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(name, QWORD) for name in ('read', 'write', 'other', 'read_bytes', 'write_bytes', 'other_bytes')]
        class Extended(ctypes.Structure):
            _fields_ = [('basic', Basic), ('io', IO), ('process_memory', SIZE), ('job_memory', SIZE),
                        ('peak_process', SIZE), ('peak_job', SIZE)]
        class Accounting(ctypes.Structure):
            _fields_ = [(name, LARGE) for name in ('user', 'kernel', 'period_user', 'period_kernel')] + [
                (name, DWORD) for name in ('faults', 'total', 'active', 'terminated')]
        self.accounting = Accounting
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        for name, arguments, result in (
            ('CreateJobObjectW', [ctypes.c_void_p, ctypes.c_wchar_p], ctypes.c_void_p),
            ('SetInformationJobObject', [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, DWORD], ctypes.c_int),
            ('AssignProcessToJobObject', [ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
            ('OpenProcess', [DWORD, ctypes.c_int, DWORD], ctypes.c_void_p),
            ('TerminateJobObject', [ctypes.c_void_p, DWORD], ctypes.c_int),
            ('QueryInformationJobObject', [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, DWORD, ctypes.c_void_p], ctypes.c_int),
            ('CloseHandle', [ctypes.c_void_p], ctypes.c_int)):
            function = getattr(self.kernel, name); function.argtypes = arguments; function.restype = result
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle: raise ctypes.WinError(ctypes.get_last_error())
        limit = Extended(); limit.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limit), ctypes.sizeof(limit)):
            self.kernel.CloseHandle(self.handle)
            raise ctypes.WinError(ctypes.get_last_error())

    def assign(self, child):
        handle = self.kernel.OpenProcess(0x0101, False, child.pid)  # SET_QUOTA | TERMINATE
        if not handle: raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not self.kernel.AssignProcessToJobObject(self.handle, handle):
                raise ctypes.WinError(ctypes.get_last_error())
        finally: self.kernel.CloseHandle(handle)

    def close(self, child, grace):
        try:
            if not self.kernel.TerminateJobObject(self.handle, 1):
                raise ctypes.WinError(ctypes.get_last_error())
            deadline = time.monotonic() + grace
            while True:
                info = self.accounting()
                if not self.kernel.QueryInformationJobObject(self.handle, 1, ctypes.byref(info), ctypes.sizeof(info), None):
                    raise ctypes.WinError(ctypes.get_last_error())
                if info.active == 0: break
                if time.monotonic() >= deadline: raise RuntimeError('Owned Windows product processes did not stop.')
                time.sleep(.02)
            child.wait(timeout=5)
        finally: self.kernel.CloseHandle(self.handle)


_GATE = """import pathlib,subprocess,sys,time
ready=pathlib.Path(sys.argv[1]);deadline=time.monotonic()+30
while not ready.is_file():
 if time.monotonic()>deadline:sys.exit(125)
 time.sleep(.01)
sys.exit(subprocess.call(sys.argv[2:]))
"""


def run(command, *, cwd: Path, output: Path, timeout: float, environment=None, grace=20):
    """Execute once; nonzero, timeout and cleanup failures retain a failing command receipt."""
    environment = os.environ.copy() if environment is None else environment
    command = list(map(str, command)); output.parent.mkdir(parents=True, exist_ok=True)
    supervisor = None
    child = None; timed_out = False; cleanup_error = None
    with tempfile.TemporaryDirectory(prefix='mcpcli-process-', dir=os.environ.get('RUNNER_TEMP') or os.environ.get('TMPDIR')) as temporary, \
            tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        gate = Path(temporary) / 'assigned'
        actual = [sys.executable, '-c', _GATE, str(gate), *command] if os.name == 'nt' else command
        try:
            supervisor = WindowsJob() if os.name == 'nt' else LinuxTree() if sys.platform.startswith('linux') else PosixGroup()
            child = subprocess.Popen(actual, cwd=cwd, env=environment, stdout=stdout, stderr=stderr,
                                     start_new_session=os.name != 'nt')
            if os.name == 'nt': supervisor.assign(child); gate.touch()
            try: child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                raise
        finally:
            failure = sys.exc_info()[1]
            if child is not None:
                try: supervisor.close(child, grace)
                except BaseException as error:
                    cleanup_error = error
                    if child.poll() is None: child.kill(); child.wait(timeout=5)
            elif isinstance(supervisor, LinuxTree):
                supervisor.libc.prctl(36, supervisor.previous, 0, 0, 0)
            elif isinstance(supervisor, WindowsJob):
                supervisor.kernel.CloseHandle(supervisor.handle)
            stdout.seek(0); stderr.seek(0)
            output.with_suffix('.stdout.txt').write_text(sanitized(stdout.read().decode(errors='replace'), environment=environment), encoding='utf-8', newline='\n')
            output.with_suffix('.stderr.txt').write_text(sanitized(stderr.read().decode(errors='replace'), environment=environment), encoding='utf-8', newline='\n')
            output.with_suffix('.command.json').write_text(sanitized(json.dumps({'command': command,
                'exitCode': child.returncode if child else None, 'timeoutSeconds': timeout, 'timedOut': timed_out,
                'error': str(failure) if failure else None,
                'cleanup': 'failed' if cleanup_error else 'complete', 'cleanupError': str(cleanup_error) if cleanup_error else None}), environment=environment)+'\n')
            if cleanup_error: raise RuntimeError('Product process cleanup failed; see ' + str(output)) from cleanup_error
    if child.returncode:
        raise subprocess.CalledProcessError(child.returncode, command,
            output=output.with_suffix('.stdout.txt').read_text(encoding='utf-8'),
            stderr=output.with_suffix('.stderr.txt').read_text(encoding='utf-8'))
    return subprocess.CompletedProcess(command, child.returncode,
        stdout=output.with_suffix('.stdout.txt').read_text(encoding='utf-8'),
        stderr=output.with_suffix('.stderr.txt').read_text(encoding='utf-8'))
