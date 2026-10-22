from pathlib import Path
import json,sys
state=json.loads(Path('/tmp/mcpcli-story411-tenants-state.json').read_text())
root=Path(state['combinedSnapshot']);output=Path(state['evidence']);sys.path.insert(0,str(root/'tools/conformance-vectors/v1'))
from run_loopback import run_catalog
selections=[(root/'packages/hexalith.parties.contracts/1.5.1/hexalith.parties.contracts.1.5.1.nupkg',('Hexalith.Parties.Contracts','1.5.1'),sorted((root/'tools/conformance-vectors/v1/modules/Hexalith.Parties.Contracts').glob('*.vector.json'))),(output/'candidate-packages/Hexalith.Tenants.Contracts.5.10.0.nupkg',('Hexalith.Tenants.Contracts','5.10.0'),sorted((output/'vectors').glob('*.vector.json')))]
result=run_catalog(root/'tests/Hexalith.McpCli.ConformanceHost/bin/Release/net10.0/Hexalith.McpCli.ConformanceHost.dll',selections,assets_path=root/'tests/Hexalith.McpCli.ConformanceHost/obj/project.assets.json',evidence_dir=output/'combined-observations',expected_modules={'Hexalith.Parties.Contracts':'parties','Hexalith.Tenants.Contracts':'tenants'})
if result['modules']!=['parties','tenants']:raise RuntimeError('Unexpected candidate combined module population')
(output/'candidate-replay.json').write_text(json.dumps({'result':'passed','scope':'unpublished-candidate-only','fullV1Accepted':False,'productionAccepted':False,'operationCount':sum(len(vectors) for _,_,vectors in selections),**result},indent=2)+'\n')
