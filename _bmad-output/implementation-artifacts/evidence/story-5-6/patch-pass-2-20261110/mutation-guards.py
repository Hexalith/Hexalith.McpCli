import importlib.util,json,subprocess,sys,tempfile
from pathlib import Path
root=Path.cwd()
source=(root/'tools/proprietary-surfaces/v1/check.py').read_text()
source=source.replace("ROOT = Path(__file__).resolve().parents[3]",f'ROOT = Path({str(root)!r})')
mutations=[
('P1',[("require((binding['path'], binding['sha256']) in authorities, 'untrusted-amendment-authority')","pass"),("authority = authorities[(binding['path'], binding['sha256'])]","authority = authorities.get((binding['path'], binding['sha256']), {'decision': 'approved'})")],'test_amendment_authority_must_belong_to_validated_lineage'),
('P2',[("web = 'microsoft.net.sdk.web' in sdks","web = 'Microsoft.NET.Sdk.Web' in tree.text(path)"),("apphost = 'aspire.apphost.sdk' in sdks","apphost = 'Aspire.AppHost.Sdk' in tree.text(path)")],'test_sdk_comments_do_not_suppress_neutral_executables'),
('P3',[("values, references, documents, linked = project_metadata(tree, path, set(paths))","values, references, documents, linked = project_metadata(tree, path, {p for p in paths if p.endswith(('.props', '.targets'))})")],'test_import_xml_and_uppercase_extensions_are_metadata_and_closure'),
('P4',[("initial = [p for p in props if p in metadata_paths] + [path] + [p for p in targets if p in metadata_paths]","initial = [p for p in props if p in metadata_paths] + [p for p in targets if p in metadata_paths] + [path]")],'test_targets_import_uses_project_defined_properties'),
('P5',[("values.setdefault('PackageId', set(values['AssemblyName']))","pass")],'test_effective_sdk_package_identity_cannot_be_renamed_through_assembly'),
('P6',[(r'(?:\(|\]|<|>)',r'(?:\(|\]|<)')],'test_fsharp_vb_attributes_and_direct_construction_add_registration_signal'),
('P7',[(r"|\bMcpServer\s*\.\s*Create\s*\(|\bnew\s+(?:[A-Za-z_][\w]*\s*\.\s*)*(?:StdioServerTransport|StreamableHttpServerTransport|SseServerTransport)\s*\(",r'')],'test_fsharp_vb_attributes_and_direct_construction_add_registration_signal'),
('P8',[("expression += '(?:[^/]+/)*'","expression += '(?:[^/]+/)+'")],'test_recursive_globs_include_zero_directory_sources_and_imports'),
('P9',[("for identity in build_action_images(lines):","for identity in []:")],'test_container_action_and_supported_yaml_structures_bind_each_identity'),
('P10',[("(?:image|newName)","(?:_ignored_image|_ignored_newName)")],'test_container_action_and_supported_yaml_structures_bind_each_identity'),
('P11',[("properties.setdefault(name, set()).update(possibilities)","properties[name] = possibilities")],'test_conditional_alias_alternatives_cannot_hide_release_executable'),
('P12',[("target = metadata_path(path, raw, value)","target = metadata_path(current, raw, value)")],'test_imported_compile_paths_are_relative_to_consuming_project'),
('P13',[("choices = expanded_values(value, local_properties, path, path, required=name in PROPERTY_NAMES)","choices = {value}")],'test_unconsumed_metadata_expands_local_classification_aliases'),
('P14',[("for section in ('mcpServers', 'servers'):","for section in ('mcpServers',):")],'test_both_json_server_sections_are_validated_and_inspected'),
('P15',[("else value.partition('=')[2] if value.startswith(('--tag=', '-t=')) else ''","else ''")],'test_docker_equals_tags_and_extensionless_executable_scripts'),
('P16',[("interesting = [p for p in paths if p in shell_scripts or PROJECT.search(p)","shell_scripts = set()\n    interesting = [p for p in paths if p in shell_scripts or PROJECT.search(p)")],'test_docker_equals_tags_and_extensionless_executable_scripts'),
('P17',[("signals.add('container-identity')","pass")],'test_container_identity_alone_has_project_and_publication_candidates'),
('P18',[("PROJECT = re.compile(r'\\.(?:cs|fs|vb)proj\\Z', re.I)","PROJECT = re.compile(r'\\.csproj\\Z', re.I)")],'test_each_project_language_executable_and_orphan_reference_is_inspected'),
('P19',[("                try:\n                    safe_path(value)","                if value.startswith(('../', '/')):\n                    continue\n                try:\n                    safe_path(value)")],'test_unsafe_and_unresolved_publication_paths_fail_with_context'),
('P20',[("text = expand_workflow_projects(text, path)","pass")],'test_workflow_matrix_project_publications_cannot_hide_orphan_projects')]
runner='''import importlib.util,sys,unittest
from pathlib import Path
sys.path.insert(0,sys.argv[1])
for name,path in [('tests',sys.argv[2]),('mutant',sys.argv[3])]:
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 if name=='tests':tests=module
 else:tests.census=module
result=unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite([tests.CensusTests(sys.argv[4])]))
sys.exit(0 if result.wasSuccessful() else 1)
'''
results=[]
with tempfile.TemporaryDirectory() as temporary:
 for name,replacements,method in mutations:
  changed=source
  for before,after in replacements:
   if before not in changed:raise SystemExit('Missing mutation anchor '+name+': '+before)
   changed=changed.replace(before,after,1)
  mutant=Path(temporary)/(name+'.py');mutant.write_text(changed)
  process=subprocess.run([sys.executable,'-c',runner,str(root/'scripts'),str(root/'tools/proprietary-surfaces/v1/test_census.py'),str(mutant),method],capture_output=True,text=True)
  if process.returncode!=1 or 'FAILED (' not in process.stderr:raise SystemExit(f'{name} mutation not caught: {process.returncode}\n{process.stdout}\n{process.stderr}')
  results.append(dict(patch=name,test=method,result='detected',exitCode=process.returncode))
print(json.dumps(dict(schema='mcpcli-census-mutation-controls/v1',result='passed',mutationCount=len(results),controls=results),indent=2))
