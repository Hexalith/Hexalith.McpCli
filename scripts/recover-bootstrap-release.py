#!/usr/bin/env python3
"""Recover a tagged bootstrap release without republishing an existing package."""

import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile


def load_script(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def content(path):
    # NuGet adds a repository signature; pack regenerates its core-properties ID/date.
    # All consumer content, including nuspec, compile DLL, analyzer and README, must match.
    with ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()
                if name != '.signature.p7s' and not name.startswith('package/services/metadata/core-properties/')}


def verify_source(phase, version):
    subprocess.run(['python3', str(Path(__file__).with_name('verify-release-source.py')),
                    os.environ.get('DISPATCH_SHA', ''), os.environ.get('DISPATCH_REF', ''), phase,
                    '--tagged-recovery', version], check=True)


def recover(version, phase):
    request = load_script('release-request')
    request.validate_request(version, phase)
    verify_source(phase, version)
    staging = Path('nupkgs/bootstrap')
    subprocess.run(['python3', 'scripts/validate-release-packages.py', str(staging), version, phase], check=True)
    package_name = f'Hexalith.McpCli.Abstractions.{version}.nupkg'
    prepared = staging / package_name
    load_script('release-receipt').verify_receipt('nupkgs/bootstrap.sha256', prepared,
                                                 os.environ.get('DISPATCH_SHA', ''))
    if not request.version_is_published(version):
        subprocess.run(['bash', str(Path(__file__).with_name('release-publish.sh')), version], check=True,
                       env={**os.environ, 'MCPCLI_RELEASE_PHASE': phase,
                            'MCPCLI_RECOVERY_VERSION': version})
    else:
        print(f'Hexalith.McpCli.Abstractions {version} is already published; verifying without a second push.')

    with tempfile.TemporaryDirectory() as temporary:
        public = Path(temporary) / 'public'
        public.mkdir()
        downloaded = public / package_name
        url = (f'https://api.nuget.org/v3-flatcontainer/hexalith.mcpcli.abstractions/{version.lower()}/'
               f'hexalith.mcpcli.abstractions.{version.lower()}.nupkg')
        try:
            with urlopen(url, timeout=30) as response:
                if response.status != 200:
                    raise ValueError('unexpected package download status')
                downloaded.write_bytes(response.read())
        except Exception:
            raise ValueError('Could not verify the public package: uncertain registry response') from None
        subprocess.run(['python3', 'scripts/validate-release-packages.py', str(public), version, phase], check=True)
        if content(prepared) != content(downloaded):
            raise ValueError('The published package content does not match the tagged bootstrap package.')
        subprocess.run(['bash', 'scripts/smoke-bootstrap-consumer.sh', version, str(public),
                        str(Path(temporary) / 'consumer')], check=True)
        verify_source(phase, version)
        print(f'Verified public package {url} SHA-256 {hashlib.sha256(downloaded.read_bytes()).hexdigest()}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version')
    parser.add_argument('phase')
    args = parser.parse_args()
    try:
        recover(args.version, args.phase)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Bootstrap recovery failed: {error}\n')


if __name__ == '__main__':
    main()
