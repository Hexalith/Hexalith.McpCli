import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const tools=JSON.parse(readFileSync(new URL('./advertised-tools.json', import.meta.url),'utf8')).tools;
const schema=name=>tools.find(tool=>tool.name===name).outputSchema.oneOf[0];
const checks=[
 [schema('list_modules').properties.modules.items.properties.name,'sample-module','Sample-module'],
 [schema('list_operations').properties.module,'sample','sample--bad'],
 [schema('describe_operation').properties.name,'sample.get-item','sample.Bad'],
 [schema('describe_operation').properties.envelope.properties.fixedTenant,'a--b','Acme'],
 [schema('describe_operation').properties.envelope.properties.platformScope,'platform:scope-1','platform:scope--1'],
 [schema('describe_operation').properties.lintFindings.items.properties.property,'/properties/a~1b/~0key','/properties/a~2b'],
 [schema('send_command').properties.aggregateId,'Party_42.v1','bad:aggregate'],
 ...['messageId','correlationId','idempotencyKey'].map(name=>[schema('send_command').properties[name],'01ARZ3NDEKTSV4RRFFQ69G5FAV','01arz3ndektsv4rrffq69g5fav']),
];
for(const [rule,valid,invalid] of checks){
 const expression=new RegExp(rule.pattern,'u');
 assert(expression.test(valid),`${rule.pattern} must accept ${valid}`);
 assert(!expression.test(invalid),`${rule.pattern} must reject ${invalid}`);
 if(!valid.startsWith('/')){
  const schemaAccepts=value=>expression.test(value)&&(rule.maxLength===undefined||value.length<=rule.maxLength);
  assert(!schemaAccepts(`${valid}\n`),`${rule.pattern} must reject a trailing newline`);
 }
}
let total=0;
function visit(node){if(node&&typeof node==='object'){if(typeof node.pattern==='string'){new RegExp(node.pattern,'u');total++;}Object.values(node).forEach(visit);}}
tools.forEach(tool=>visit(tool.outputSchema));
console.log(`Native JavaScript compiled ${total} advertised patterns and passed ${checks.length} valid/invalid boundary checks, including strict ends.`);
