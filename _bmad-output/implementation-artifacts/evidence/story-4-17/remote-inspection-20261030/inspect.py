"""Authorized bounded metadata/manifests only; no Secret reads or remote writes."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
CONTEXT = 'jpiquot@local'
API = 'https://192.168.1.30:6443'


def now():
    return datetime.now(timezone.utc).isoformat()


def command(argv, timeout=20):
    started = now()
    try:
        result = subprocess.run(argv, capture_output=True, timeout=timeout)
        receipt = {'argv': argv, 'startedAt': started, 'exitCode': result.returncode}
        if result.returncode:
            diagnostic = result.stderr.decode(errors='replace').lower()
            categories = [('manifest-not-found', ('not found', 'manifest unknown')),
                          ('authentication-required', ('unauthorized', 'authentication required')),
                          ('access-denied', ('denied', 'forbidden')),
                          ('tls-validation', ('x509', 'certificate'))]
            receipt['errorCategory'] = next((name for name, markers in categories if any(m in diagnostic for m in markers)), 'tool-error')
        return receipt, result.stdout
    except subprocess.TimeoutExpired:
        return {'argv': argv, 'startedAt': started, 'exitCode': None, 'outcome': 'timeout'}, b''


def public_endpoint(value):
    if not isinstance(value, str):
        return None
    value = value.split(',', 1)[0]
    parsed = urlsplit(value if '://' in value else '//' + value)
    try:
        if parsed.hostname and re.fullmatch(r'[a-zA-Z0-9._:-]+', parsed.hostname):
            return {'scheme': parsed.scheme or None, 'host': parsed.hostname, 'port': parsed.port}
    except ValueError:
        pass
    return None


def metadata(item):
    meta = item.get('metadata', {})
    result = {k: meta[k] for k in ('name', 'namespace', 'uid') if k in meta}
    result['kind'] = item['kind']
    spec = item.get('spec', {})
    pod = spec if item['kind'] == 'Pod' else spec.get('template', {}).get('spec', {})
    containers = pod.get('containers', []) + pod.get('initContainers', [])
    if containers:
        result['images'] = [c['image'] for c in containers]
        result['resources'] = {c['name']: c.get('resources', {}) for c in containers}
        refs = []
        for container in containers:
            for env in container.get('env', []):
                ref = env.get('valueFrom', {}).get('secretKeyRef')
                if ref:
                    refs.append({k: ref[k] for k in ('name', 'key') if k in ref})
        result['secretReferencesOnly'] = refs
        result['configMapReferences'] = [v['configMap']['name'] for v in pod.get('volumes', []) if 'configMap' in v]
    if item['kind'] == 'Service':
        result.update(serviceType=spec.get('type'), ports=spec.get('ports', []))
    if item['kind'] == 'StorageClass':
        result.update(provisioner=item.get('provisioner'), volumeBindingMode=item.get('volumeBindingMode'),
                      reclaimPolicy=item.get('reclaimPolicy'))
    if item['kind'] == 'Component':
        result.update(componentType=spec.get('type'), componentVersion=spec.get('version'), scopes=item.get('scopes', []))
        result['metadataBindings'] = []
        for field in spec.get('metadata', []):
            entry = {'name': field['name']}
            if 'secretKeyRef' in field:
                entry['secretKeyRef'] = field['secretKeyRef']
            elif field['name'].lower() in ('redishost', 'vaultaddr', 'endpoint', 'host', 'server', 'broker'):
                entry['publicEndpoint'] = public_endpoint(field.get('value'))
            result['metadataBindings'].append(entry)
    if item['kind'] == 'Configuration':
        result['mtls'] = {'enabled': spec.get('mtls', {}).get('enabled')}
        result['accessControl'] = {k: spec.get('accessControl', {}).get(k) for k in ('defaultAction', 'trustDomain')}
    status = item.get('status', {})
    result['status'] = {k: status[k] for k in ('phase', 'replicas', 'readyReplicas', 'availableReplicas') if k in status}
    return result


def cluster():
    check, raw = command(['kubectl', '--context=' + CONTEXT, 'config', 'view', '--minify', '-o',
                          'jsonpath={.clusters[0].cluster.server}'])
    if check['exitCode'] != 0 or raw.decode().strip() != API:
        raise RuntimeError('Approved context/API binding not established; no remote read performed.')
    records = []
    selections = [('namespaces', False), ('deployments,statefulsets,pods,services', True),
                  ('storageclasses', False), ('components.dapr.io,configurations.dapr.io', True)]
    for kinds, all_namespaces in selections:
        argv = ['kubectl', '--context=' + CONTEXT, '--request-timeout=10s', 'get', kinds]
        if all_namespaces:
            argv.append('-A')
        argv += ['-o', 'json']
        receipt, raw = command(argv)
        if receipt['exitCode'] == 0:
            items = json.loads(raw).get('items', [])
            receipt.update(resourceCount=len(items), selectedMetadata=[metadata(item) for item in items])
        records.append(receipt)
        print(json.dumps({'read': kinds, 'exitCode': receipt['exitCode'], 'resourceCount': receipt.get('resourceCount')}), flush=True)
    report = {'observedAt': now(), 'context': CONTEXT, 'api': API, 'commands': records,
              'limits': 'Selected metadata only. No Secret resource, credential value, logs, deployment, registry write or application call.'}
    (HERE / 'cluster.json').write_text(json.dumps(report, indent=2) + '\n')


def registry():
    candidates = ['eventstore:3.128.3', 'eventstore:3.128.4', 'parties:1.5.1', 'parties:2.0.0',
                  'tenants:5.10.0', 'tenants:5.11.1', 'tenants-api:5.11.1', 'memories:3.0.10',
                  'memories-domain-service:3.0.10', 'memories-access-telemetry-clock:3.0.10',
                  'memories-access-telemetry:3.0.10']
    records = []
    for candidate in candidates:
        reference = 'registry.hexalith.com/' + candidate
        argv = ['docker', 'buildx', 'imagetools', 'inspect', reference]
        receipt, raw = command(argv, 35)
        if receipt['exitCode'] == 0:
            lines = raw.decode().splitlines()
            receipt['digests'] = [m.group(1) for line in lines if (m := re.match(r'\s*Digest:\s+(sha256:[0-9a-f]{64})\s*$', line))]
            receipt['platforms'] = [m.group(1) for line in lines if (m := re.match(r'\s*Platform:\s+([a-zA-Z0-9/_-]+)\s*$', line))]
        receipt['reference'] = reference
        records.append(receipt)
        print(json.dumps({'manifest': reference, 'exitCode': receipt['exitCode'], 'digests': receipt.get('digests')}), flush=True)
        (HERE / 'registry.json').write_text(json.dumps({'observedAt': now(), 'commands': records,
            'limits': 'Manifest inspection only. Digest availability does not establish owner/source compatibility, node pullability or runtime readiness.'}, indent=2) + '\n')


def registry_followup():
    records = []
    for candidate in ['tenants-api:5.11.1', 'memories-domain-service:3.0.10', 'tenants-api:5.10.0']:
        reference = 'registry.hexalith.com/' + candidate
        receipt, raw = command(['docker', 'buildx', 'imagetools', 'inspect', reference], 35)
        receipt['reference'] = reference
        if receipt['exitCode'] == 0:
            receipt['digests'] = re.findall(r'(?m)^\s*Digest:\s+(sha256:[0-9a-f]{64})\s*$', raw.decode())
        records.append(receipt)
        print(json.dumps(receipt), flush=True)
    (HERE / 'registry-followup.json').write_text(json.dumps({'observedAt': now(), 'commands': records,
        'purpose': 'Distinguish missing manifests from access failures and check the accepted Tenants version; 14 total candidate requests.'}, indent=2) + '\n')


if __name__ == '__main__':
    import sys
    {'cluster': cluster, 'registry': registry, 'registry-followup': registry_followup}[sys.argv[1]]()
