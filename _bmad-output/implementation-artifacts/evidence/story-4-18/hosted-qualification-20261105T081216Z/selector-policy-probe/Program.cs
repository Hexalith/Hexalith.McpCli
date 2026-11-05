using System.Text.Json;
using Hexalith.EventStore.Contracts.Routing;
var rows = new List<object>();
foreach (var (wire, projection, selector) in new[] {
    ("PartyDetail", "party-detail", "PartyDetailProjectionQueryActor"),
    ("PartyIndex", "party-index", "PartyIndexProjectionQueryActor"),
    ("PartySearch", "party-index", "PartyIndexProjectionQueryActor") })
{
    var execution = new RouteExecutionDeclaration("owner-handler", "exact", [wire], "domain-service", "projection", []);
    var route = new RouteContractDeclaration("party-query", "query", "party", wire, projection, "v1", null, "workload", "query", null, [], execution);
    bool noBinding = RouteCatalogQuerySelectorPolicy.Matches(route, selector);
    bool exactBinding = RouteCatalogQuerySelectorPolicy.Matches(route with { Execution = execution with { CompatibilityProjectionActorTypes = [selector] } }, selector);
    bool wrongBinding = RouteCatalogQuerySelectorPolicy.Matches(route with { Execution = execution with { CompatibilityProjectionActorTypes = ["ForeignQueryActor"] } }, selector);
    rows.Add(new { wire, selector, withoutOwnerBinding = noBinding, withExactOwnerBinding = exactBinding, withForeignBinding = wrongBinding });
    if (noBinding || !exactBinding || wrongBinding) throw new Exception("Unexpected SDK selector policy");
}
Console.WriteLine(JsonSerializer.Serialize(rows));
