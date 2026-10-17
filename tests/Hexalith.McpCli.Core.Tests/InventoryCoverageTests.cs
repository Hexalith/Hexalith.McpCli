using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Execution;
using Hexalith.McpCli.Core.Serialization;
using Hexalith.McpCli.Sample.Contracts;
using NSubstitute;
using Shouldly;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Mutation-protects the test-only inventory gate with public documents and real built descriptors.</summary>
public sealed class InventoryCoverageTests
{
    private const string FileLabel = "inventory.json";
    private static string ArtifactPath => Path.Combine(AppContext.BaseDirectory, "inventory-coverage", "v1", "sample-approved.json");

    /// <summary>The copied artifact covers all sample operations, shared references and approved exclusions.</summary>
    [Fact]
    public void ApprovedSampleMatchesUnfilteredBuiltCatalog()
    {
        CatalogProvider provider = Provider();
        ICatalog catalog = Service(provider);

        InventoryCoverageGate.CheckFile(ArtifactPath, catalog, provider).ShouldBeEmpty();
        catalog.ListOperations("sample").Document.ShouldNotBeNull().Operations.Count.ShouldBe(3);
        catalog.Describe("sample.create-item").Document.ShouldNotBeNull().Submittable.ShouldBeFalse();
        Path.IsPathFullyQualified(ArtifactPath).ShouldBeTrue();
    }

    /// <summary>Real discovery keeps mapped type identities and contract-type properties private at every public surface.</summary>
    [Fact]
    public void PublicDocumentsDoNotExposeContractTypes()
    {
        ICatalog catalog = Service(Provider());
        JsonObject inventory = Inventory();
        string[] mappedNames = inventory["targets"]!.AsArray().Select(target => target!["contractType"]!.GetValue<string>()).ToArray();
        var documents = new List<object>
        {
            catalog.ListModules().Document.ShouldNotBeNull(),
            catalog.ListOperations("sample").Document.ShouldNotBeNull(),
        };
        documents.AddRange(catalog.ListOperations("sample").Document!.Operations.Select(operation =>
            (object)catalog.Describe(operation.Name).Document.ShouldNotBeNull()));

        foreach (object document in documents)
        {
            JsonElement json = JsonSerializer.SerializeToElement(document, document.GetType(), McpCliJson.Result);
            CheckPublicDocument(json, mappedNames);
        }
    }

    /// <summary>Payload schema and example keys are domain fields rather than discovery metadata.</summary>
    [Fact]
    public void AcceptsContractTypeNamesInPayloadFieldKeys()
    {
        using JsonDocument document = JsonDocument.Parse("""
            {"name":"sample.get-item",
             "schema":{"type":"object","properties":{"contractType":{"type":"string"},"subcontractTypeId":{"type":"string"}}},
             "example":{"contractType":"agreement","nested":{"subcontractTypeId":"value"}}}
            """);

        CheckPublicDocument(document.RootElement, [typeof(GetItemQuery).FullName!]);
    }

    /// <summary>Skipping payload bodies still detects forbidden field names in actual discovery metadata.</summary>
    /// <param name="json">The metadata leak location.</param>
    [Theory]
    [InlineData("{\"contractType\":\"leak\"}")]
    [InlineData("{\"modules\":[{\"contractType\":\"leak\"}]}")]
    [InlineData("{\"operations\":[{\"clrType\":\"leak\"}]}")]
    [InlineData("{\"envelope\":{\"schema\":{\"contractType\":\"leak\"}}}")]
    public void RejectsContractTypeFieldsInPublicMetadata(string json)
    {
        using JsonDocument document = JsonDocument.Parse(json);

        Should.Throw<ShouldAssertException>(() => CheckPublicDocument(document.RootElement, []));
    }

    /// <summary>Full CLR identities remain forbidden even inside otherwise exempt payload bodies.</summary>
    /// <param name="body">The payload body carrying the leaked value.</param>
    [Theory]
    [InlineData("schema")]
    [InlineData("example")]
    public void RejectsMappedFullClrNamesInsidePayloadBodies(string body)
    {
        string fullName = typeof(GetItemQuery).FullName!;
        JsonElement document = JsonSerializer.SerializeToElement(new Dictionary<string, object>
        {
            [body] = new { contractType = fullName },
        });

        Should.Throw<ShouldAssertException>(() => CheckPublicDocument(document, [fullName]));
    }

    /// <summary>Every public mutation is compared independently from the untouched internal snapshot.</summary>
    /// <param name="mutation">The public document mutation.</param>
    [Theory]
    [InlineData("missing")]
    [InlineData("extra")]
    [InlineData("duplicate")]
    [InlineData("ordinal")]
    [InlineData("module")]
    [InlineData("error")]
    [InlineData("no-document")]
    public void RejectsPublicDiscoveryMismatch(string mutation)
    {
        CatalogProvider provider = Provider();
        OperationsDocument original = Service(provider).ListOperations("sample").Document.ShouldNotBeNull();
        OperationsDocument document = original;
        string[] expected;
        switch (mutation)
        {
            case "missing":
                document = original with { Operations = original.Operations.Skip(1).ToArray() };
                expected = ["target T01: public name expected 'sample.create-item' once; actual missing."];
                break;
            case "extra":
                document = original with { Operations = [.. original.Operations, new("sample.extra", "read", "Extra.")] };
                expected = ["public operation sample.extra: unexpected operation; no approved included target."];
                break;
            case "duplicate":
                document = original with { Operations = [.. original.Operations, original.Operations[0]] };
                expected = ["public operation sample.create-item: duplicate public entry; expected once, actual 2."];
                break;
            case "ordinal":
                document = original with { Operations = [original.Operations[0] with { Name = "sample.Create-item" }, .. original.Operations.Skip(1)] };
                expected = ["public operation sample.Create-item: unexpected operation; no approved included target.",
                    "target T01: public name expected 'sample.create-item' once; actual missing."];
                break;
            case "module":
                document = original with { Module = "other" };
                expected = ["public: module expected 'sample'; actual 'other'."];
                break;
            case "error":
                expected = ["public: ListOperations error 'catalog_invalid': Rejected."];
                break;
            default:
                expected = ["public: ListOperations returned no document."];
                break;
        }

        ICatalog mutated = Substitute.For<ICatalog>();
        mutated.ListOperations("sample").Returns(mutation switch
        {
            "error" => new(null, new OperationError("catalog_invalid", Message: "Rejected.")),
            "no-document" => new(null, null),
            _ => new CatalogLookupResult<OperationsDocument>(document, null),
        });
        Check(Inventory(), mutated, provider).ShouldBe(Diagnostics(expected));
        mutated.Received(1).ListOperations("sample", null);
    }

    /// <summary>CLR full names are checked ordinally even when every public canonical name matches.</summary>
    [Fact]
    public void RejectsWrongClrTypeDespiteMatchingPublicNames()
    {
        JsonObject inventory = Inventory();
        inventory["targets"]![0]!["contractType"] = "Hexalith.McpCli.Sample.Contracts.CreateItemcommand";
        Check(inventory).ShouldBe(Diagnostics("target T01: contractType for 'sample.create-item' expected 'Hexalith.McpCli.Sample.Contracts.CreateItemcommand'; actual 'Hexalith.McpCli.Sample.Contracts.CreateItemCommand'."));
    }

    /// <summary>An internal omission cannot be hidden by a mutated public list with matching names.</summary>
    [Fact]
    public void ChecksInternalNamesIndependently()
    {
        JsonObject inventory = Inventory();
        inventory["targets"]![0]!["name"] = "sample.absent";
        CatalogProvider provider = Provider();
        OperationsDocument original = Service(provider).ListOperations("sample").Document.ShouldNotBeNull();
        ICatalog mutated = Substitute.For<ICatalog>();
        mutated.ListOperations("sample").Returns(new CatalogLookupResult<OperationsDocument>(original with
        {
            Operations = [original.Operations[0] with { Name = "sample.absent" }, .. original.Operations.Skip(1)],
        }, null));

        Check(inventory, mutated, provider).ShouldBe(Diagnostics(
            "internal operation sample.create-item: unexpected operation / 'Hexalith.McpCli.Sample.Contracts.CreateItemCommand'; no approved included target.",
            "target T01: internal name expected 'sample.absent' once; actual 0."));
    }

    /// <summary>Approved exclusions must remain absent on both surfaces, including CLR identity aliases.</summary>
    /// <param name="sameName">Whether the excluded name itself is present, rather than only the excluded CLR identity.</param>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void RejectsPresentExclusion(bool sameName)
    {
        JsonObject inventory = Inventory();
        if (sameName)
        {
            inventory["legacyRows"]![0]!["disposition"] = "defer";
            inventory["legacyRows"]![0]!["coverage"] = "exclude";
            Check(inventory).ShouldBe(Diagnostics(
                "internal operation sample.create-item: unexpected operation / 'Hexalith.McpCli.Sample.Contracts.CreateItemCommand'; no approved included target.",
                "public operation sample.create-item: unexpected operation; no approved included target.",
                "target T01: excluded name 'sample.create-item' is publicly present.",
                "target T01: excluded target is internally present as 'sample.create-item' / 'Hexalith.McpCli.Sample.Contracts.CreateItemCommand'."));
        }
        else
        {
            inventory["targets"]!.AsArray().RemoveAt(0);
            inventory["legacyRows"]!.AsArray().RemoveAt(0);
            inventory["targets"]![2]!["contractType"] = typeof(CreateItemCommand).FullName;
            Check(inventory).ShouldBe(Diagnostics(
                "internal operation sample.create-item: unexpected operation / 'Hexalith.McpCli.Sample.Contracts.CreateItemCommand'; no approved included target.",
                "public operation sample.create-item: unexpected operation; no approved included target.",
                "target T04: excluded target is internally present as 'sample.create-item' / 'Hexalith.McpCli.Sample.Contracts.CreateItemCommand'."));
        }
    }

    /// <summary>An excluded name that is internally present fails even when the excluded CLR identity differs.</summary>
    [Fact]
    public void RejectsPresentExclusionByNameWithDifferentClrType()
    {
        JsonObject inventory = Inventory();
        inventory["targets"]!.AsArray().RemoveAt(0);
        inventory["legacyRows"]!.AsArray().RemoveAt(0);
        inventory["targets"]![2]!["name"] = "sample.create-item";
        Check(inventory).ShouldBe(Diagnostics(
            "internal operation sample.create-item: unexpected operation / 'Hexalith.McpCli.Sample.Contracts.CreateItemCommand'; no approved included target.",
            "public operation sample.create-item: unexpected operation; no approved included target.",
            "target T04: excluded name 'sample.create-item' is publicly present.",
            "target T04: excluded target is internally present as 'sample.create-item' / 'Hexalith.McpCli.Sample.Contracts.CreateItemCommand'."));
    }

    /// <summary>Conflicting identities and all invalid scope decisions fail with their stable row or target.</summary>
    /// <param name="mutation">The inventory mutation.</param>
    /// <param name="expected">The exact finding.</param>
    [Theory]
    [InlineData("row-id", "row L01 ($.legacyRows[1].id): duplicate id 'L01'; first declared at row L01 ($.legacyRows[0].id).")]
    [InlineData("target-id", "target T01 ($.targets[1].id): duplicate id 'T01'; first declared at target T01 ($.targets[0].id).")]
    [InlineData("target-name", "target T02: duplicate name 'sample.create-item'; first declared at target T01.")]
    [InlineData("target-type", "target T02: duplicate contractType 'Hexalith.McpCli.Sample.Contracts.CreateItemCommand'; first declared at target T01.")]
    [InlineData("reference", "row L01: duplicate target reference 'T01'.")]
    [InlineData("dangling", "row L01: dangling target reference 'T99'.")]
    [InlineData("orphan", "target T05: orphan target has no legacy row reference.")]
    [InlineData("conflict", "target T02: conflicting coverage in rows L02, L03.")]
    [InlineData("include-withdraw", "row L01: invalid disposition/coverage 'withdraw/include'; include requires replace; exclude requires withdraw or defer.")]
    [InlineData("include-defer", "row L01: invalid disposition/coverage 'defer/include'; include requires replace; exclude requires withdraw or defer.")]
    [InlineData("exclude-replace", "row L04: invalid disposition/coverage 'replace/exclude'; include requires replace; exclude requires withdraw or defer.")]
    [InlineData("disposition", "row L01: invalid disposition/coverage 'unknown/include'; include requires replace; exclude requires withdraw or defer.")]
    [InlineData("coverage", "row L01: coverage must be 'include' or 'exclude'; actual 'unknown'.")]
    [InlineData("approval", "row L01: approval.status must be 'approved'; actual 'pending'.")]
    [InlineData("excluded-approval", "row L04: approval.status must be 'approved'; actual 'pending'.")]
    [InlineData("authority", "row L01: approval.authority must be 'owning-maintainer' or 'synthetic-fixture'; actual 'scope-only'. Scope-only approval cannot establish release readiness.")]
    [InlineData("unknown-authority", "row L01: approval.authority must be 'owning-maintainer' or 'synthetic-fixture'; actual 'unknown'. Scope-only approval cannot establish release readiness.")]
    [InlineData("purpose", "$.purpose: expected 'fixture' or 'release'.")]
    [InlineData("module", "$.module: expected canonical module name; actual 'Sample'.")]
    [InlineData("module-suffix", "$.module: expected canonical module name; actual 'sample!'.")]
    [InlineData("target-suffix", "target T01: name must be canonical in module 'sample'; actual 'sample.create-item!'.")]
    [InlineData("target-canonical", "target T01: name must be canonical in module 'sample'; actual 'sample.Create-item'.")]
    [InlineData("target-module", "target T01: name must be canonical in module 'sample'; actual 'other.create-item'.")]
    [InlineData("target-newline", "$.targets[0].name: expected nonempty string without surrounding whitespace.")]
    public void RejectsInvalidScope(string mutation, string expected)
    {
        JsonObject inventory = Inventory();
        JsonArray targets = inventory["targets"]!.AsArray();
        JsonArray rows = inventory["legacyRows"]!.AsArray();
        switch (mutation)
        {
            case "row-id": rows[1]!["id"] = "L01"; break;
            case "target-id": targets[1]!["id"] = "T01"; rows[1]!["targetIds"]![0] = "T01"; rows[2]!["targetIds"]![0] = "T01"; break;
            case "target-name": targets[1]!["name"] = "sample.create-item"; break;
            case "target-type": targets[1]!["contractType"] = typeof(CreateItemCommand).FullName; break;
            case "reference": rows[0]!["targetIds"]!.AsArray().Add("T01"); break;
            case "dangling": rows[0]!["targetIds"]!.AsArray().Add("T99"); break;
            case "orphan": rows[4]!["targetIds"]![0] = "T04"; break;
            case "conflict": rows[1]!["disposition"] = "defer"; rows[1]!["coverage"] = "exclude"; break;
            case "include-withdraw": rows[0]!["disposition"] = "withdraw"; break;
            case "include-defer": rows[0]!["disposition"] = "defer"; break;
            case "exclude-replace": rows[3]!["disposition"] = "replace"; break;
            case "disposition": rows[0]!["disposition"] = "unknown"; break;
            case "coverage": rows[0]!["coverage"] = "unknown"; break;
            case "approval": rows[0]!["approval"]!["status"] = "pending"; break;
            case "excluded-approval": rows[3]!["approval"]!["status"] = "pending"; break;
            case "authority": rows[0]!["approval"]!["authority"] = "scope-only"; break;
            case "unknown-authority": rows[0]!["approval"]!["authority"] = "unknown"; break;
            case "purpose": inventory["purpose"] = "unknown"; break;
            case "module": inventory["module"] = "Sample"; break;
            case "module-suffix": inventory["module"] = "sample!"; break;
            case "target-suffix": targets[0]!["name"] = "sample.create-item!"; break;
            case "target-canonical": targets[0]!["name"] = "sample.Create-item"; break;
            case "target-module": targets[0]!["name"] = "other.create-item"; break;
            case "target-newline": targets[0]!["name"] = "sample.create-item\n"; break;
        }

        Check(inventory).ShouldBe(Diagnostics(expected));
    }

    /// <summary>Required fields and their value shapes fail closed throughout the document.</summary>
    /// <param name="path">The dot-separated mutation path, using numeric array indexes.</param>
    [Theory]
    [InlineData("module")]
    [InlineData("purpose")]
    [InlineData("targets.0.id")]
    [InlineData("targets.0.name")]
    [InlineData("targets.0.contractType")]
    [InlineData("legacyRows.0.id")]
    [InlineData("legacyRows.0.legacyOperation")]
    [InlineData("legacyRows.0.disposition")]
    [InlineData("legacyRows.0.coverage")]
    [InlineData("legacyRows.0.rationale")]
    [InlineData("legacyRows.0.approval.status")]
    [InlineData("legacyRows.0.approval.authority")]
    [InlineData("legacyRows.0.approval.reference")]
    public void RejectsMissingOrMalformedStringFields(string path)
    {
        foreach (string mutation in new[] { "missing", "null", "number", "empty", "whitespace", "padded" })
        {
            JsonObject inventory = Inventory();
            (JsonObject parent, string field, string location) = Field(inventory, path);
            if (mutation == "missing")
            {
                parent.Remove(field);
            }
            else
            {
                parent[field] = mutation switch
                {
                    "null" => null,
                    "number" => JsonValue.Create(3),
                    "empty" => JsonValue.Create(""),
                    "whitespace" => JsonValue.Create(" "),
                    _ => JsonValue.Create(" padded "),
                };
            }

            Check(inventory).ShouldBe(Diagnostics(location + (mutation == "missing"
                ? ": missing required field." : ": expected nonempty string without surrounding whitespace.")));
        }
    }

    /// <summary>Containers reject wrong shapes, empty arrays, missing and unknown fields.</summary>
    /// <param name="json">The complete malformed document or replacement fragment.</param>
    /// <param name="path">The field to replace, or the root.</param>
    /// <param name="expected">The exact JSON path diagnostic.</param>
    [Theory]
    [InlineData("[]", "root", "$: expected object.")]
    [InlineData("2", "formatVersion", "$.formatVersion: expected supported integer formatVersion 1.")]
    [InlineData("\"1\"", "formatVersion", "$.formatVersion: expected supported integer formatVersion 1.")]
    [InlineData("1.5", "formatVersion", "$.formatVersion: expected supported integer formatVersion 1.")]
    [InlineData("{}", "targets", "$.targets: expected nonempty array.")]
    [InlineData("[]", "targets", "$.targets: expected nonempty array.")]
    [InlineData("null", "legacyRows", "$.legacyRows: expected nonempty array.")]
    [InlineData("[]", "legacyRows", "$.legacyRows: expected nonempty array.")]
    [InlineData("false", "legacyRows.0.targetIds", "$.legacyRows[0].targetIds: expected nonempty array.")]
    [InlineData("[]", "legacyRows.0.targetIds", "$.legacyRows[0].targetIds: expected nonempty array.")]
    [InlineData("[null]", "legacyRows.0.targetIds", "$.legacyRows[0].targetIds[0]: expected nonempty string without surrounding whitespace.")]
    [InlineData("null", "legacyRows.0.approval", "$.legacyRows[0].approval: expected object.")]
    public void RejectsMalformedDocumentShapes(string json, string path, string expected)
    {
        JsonObject inventory = Inventory();
        if (path == "root")
        {
            InventoryCoverageGate.Check(json, FileLabel, Service(Provider()), Provider()).ShouldBe(Diagnostics(expected));
            return;
        }

        (JsonObject parent, string field, _) = Field(inventory, path);
        parent[field] = JsonNode.Parse(json);
        Check(inventory).ShouldBe(Diagnostics(expected));
    }

    /// <summary>Lone-surrogate escapes become findings instead of crashing the gate.</summary>
    /// <param name="json">The document containing the lone surrogate.</param>
    /// <param name="expected">The exact finding.</param>
    [Theory]
    [InlineData("{\"formatVersion\":1,\"module\":\"\\ud800\"}", "$.module: invalid Unicode string.")]
    [InlineData("{\"formatVersion\":1,\"targets\":[\"\\udc00\"]}", "$.targets[0]: invalid Unicode string.")]
    [InlineData("{\"\\ud800\":1}", "$: invalid Unicode property name.")]
    public void RejectsLoneSurrogateEscapes(string json, string expected)
        => InventoryCoverageGate.Check(json, FileLabel, Service(Provider()), Provider()).ShouldBe(Diagnostics(expected));

    /// <summary>JSON comments and trailing commas are not accepted.</summary>
    /// <param name="json">The otherwise empty document using the extension.</param>
    [Theory]
    [InlineData("{\"formatVersion\":1 // comment\n}")]
    [InlineData("{\"formatVersion\":1,}")]
    public void RejectsJsonCommentsAndTrailingCommas(string json)
        => InventoryCoverageGate.Check(json, FileLabel, Service(Provider()), Provider()).ShouldHaveSingleItem()
            .ShouldStartWith(FileLabel + ":$: invalid JSON at line ");

    /// <summary>Required container and version fields cannot be omitted.</summary>
    /// <param name="path">The required field to remove.</param>
    [Theory]
    [InlineData("formatVersion")]
    [InlineData("targets")]
    [InlineData("legacyRows")]
    [InlineData("legacyRows.0.targetIds")]
    [InlineData("legacyRows.0.approval")]
    public void RejectsMissingContainersAndVersion(string path)
    {
        JsonObject inventory = Inventory();
        (JsonObject parent, string field, string location) = Field(inventory, path);
        parent.Remove(field);
        Check(inventory).ShouldBe(Diagnostics(location + ": missing required field."));
    }

    /// <summary>Target and row entries must be objects with the versioned fields.</summary>
    /// <param name="field">The collection to mutate.</param>
    [Theory]
    [InlineData("targets")]
    [InlineData("legacyRows")]
    public void RejectsNonObjectEntries(string field)
    {
        JsonObject inventory = Inventory();
        inventory[field]![0] = null;
        Check(inventory).ShouldBe(Diagnostics("$." + field + "[0]: expected object."));
    }

    /// <summary>All object levels are strict about missing/unknown fields and duplicate JSON keys.</summary>
    /// <param name="path">The object location.</param>
    [Theory]
    [InlineData("")]
    [InlineData("targets.0")]
    [InlineData("legacyRows.0")]
    [InlineData("legacyRows.0.approval")]
    public void RejectsUnknownAndDuplicateKeys(string path)
    {
        JsonObject inventory = Inventory();
        JsonObject item = inventory;
        string location = "$";
        JsonNode current = inventory;
        foreach (string part in path.Split('.', StringSplitOptions.RemoveEmptyEntries))
        {
            current = int.TryParse(part, out int index) ? current[index]! : current[part]!;
            location += int.TryParse(part, out _) ? "[" + part + "]" : "." + part;
        }
        item = current.AsObject();
        item["unexpected"] = "value";
        Check(inventory).ShouldBe(Diagnostics(location + ".unexpected: unknown field."));
        item.Remove("unexpected");
        string firstKey = item.First().Key;
        string original = item.ToJsonString();
        string duplicate = original.Insert(1, JsonSerializer.Serialize(firstKey) + ":" + item[firstKey]!.ToJsonString() + ",");
        string serialized = inventory.ToJsonString();
        int position = serialized.IndexOf(original, StringComparison.Ordinal);
        string document = serialized[..position] + duplicate + serialized[(position + original.Length)..];
        CatalogProvider provider = Provider();
        InventoryCoverageGate.Check(document, FileLabel, Service(provider), provider)
            .ShouldBe(Diagnostics(location + "." + firstKey + ": duplicate JSON key."));
    }

    /// <summary>Unreadable and syntactically invalid documents produce stable file and parser locations.</summary>
    [Fact]
    public void RejectsUnreadableAndInvalidJson()
    {
        CatalogProvider provider = Provider();
        string absent = Path.Combine(AppContext.BaseDirectory, "inventory-coverage", "v1", "absent.json");
        InventoryCoverageGate.CheckFile(absent, Service(provider), provider)
            .ShouldBe(new[] { absent + ":$: cannot read inventory (FileNotFoundException)." });
        InventoryCoverageGate.Check("{", FileLabel, Service(provider), provider)
            .ShouldBe(Diagnostics("$: invalid JSON at line 0, byte 1."));
    }

    /// <summary>An invalid raw byte in otherwise valid rationale text fails strict UTF-8 decoding.</summary>
    /// <param name="withBom">Whether the inventory begins with a valid UTF-8 byte order mark.</param>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void RejectsMalformedUtf8Encoding(bool withBom)
    {
        JsonObject inventory = Inventory();
        inventory["legacyRows"]![0]!["rationale"] = "encoding-probe";
        string json = inventory.ToJsonString();
        byte[] bytes = Encoding.UTF8.GetBytes(json);
        int position = Encoding.UTF8.GetByteCount(json.AsSpan(0, json.IndexOf("encoding-probe", StringComparison.Ordinal)));
        bytes[position] = 0xFF;
        string path = Path.GetTempFileName();
        try
        {
            File.WriteAllBytes(path, withBom ? [0xEF, 0xBB, 0xBF, .. bytes] : bytes);
            CatalogProvider provider = Provider();
            InventoryCoverageGate.CheckFile(path, Service(provider), provider)
                .ShouldBe(new[] { path + ":$: malformed UTF-8 encoding." });
        }
        finally
        {
            File.Delete(path);
        }
    }

    /// <summary>A valid UTF-8 BOM remains supported by strict decoding.</summary>
    [Fact]
    public void AcceptsValidUtf8WithByteOrderMark()
    {
        string path = Path.GetTempFileName();
        try
        {
            File.WriteAllBytes(path, [0xEF, 0xBB, 0xBF, .. Encoding.UTF8.GetBytes(Inventory().ToJsonString())]);
            CatalogProvider provider = Provider();
            InventoryCoverageGate.CheckFile(path, Service(provider), provider).ShouldBeEmpty();
        }
        finally
        {
            File.Delete(path);
        }
    }

    /// <summary>Synthetic fixture approval cannot be reused as release readiness.</summary>
    [Fact]
    public void RejectsSyntheticReleaseApproval()
    {
        JsonObject inventory = Inventory();
        inventory["purpose"] = "release";
        Check(inventory).ShouldBe(Diagnostics(Enumerable.Range(1, 5).Select(index =>
            $"row L0{index}: synthetic-fixture approval certifies fixtures only; purpose must be 'fixture'.").ToArray()));
    }

    /// <summary>A later module can use the same checker with owner approval and real decorated contracts.</summary>
    [Fact]
    public void ReusesCheckerForAnotherOwnerApprovedModule()
    {
        var provider = new CatalogProvider(() => [new InventoryCoverageContractsAssembly("future", typeof(global::Catalog.Invalid.Contracts.DuplicateFirstQuery))],
            new RecordingLogger<CatalogProvider>());
        Check(SingleOperationInventory("future"), Service(provider), provider).ShouldBeEmpty();
    }

    /// <summary>Warnings alone do not hide declarations and do not invalidate coverage.</summary>
    [Fact]
    public void AcceptsMatchingCatalogWithWarningsOnly()
    {
        var provider = new CatalogProvider(() => [new InventoryCoverageContractsAssembly("future",
            typeof(global::Catalog.Routing.Contracts.RedundantConventionQuery))], new RecordingLogger<CatalogProvider>());
        JsonObject inventory = SingleOperationInventory("future");
        inventory["targets"]![0]!["name"] = "future.redundant-convention";
        inventory["targets"]![0]!["contractType"] = typeof(global::Catalog.Routing.Contracts.RedundantConventionQuery).FullName;
        CatalogSnapshot snapshot = provider.Get(false).Catalog.ShouldNotBeNull();
        snapshot.Diagnostics.ShouldNotBeEmpty();
        snapshot.Diagnostics.ShouldAllBe(diagnostic => diagnostic.Severity == "warning");

        Check(inventory, Service(provider), provider).ShouldBeEmpty();
    }

    /// <summary>A duplicate declaration cannot disappear behind a matching surviving public list.</summary>
    [Fact]
    public void RejectsCatalogErrorsDespiteMatchingSurvivors()
    {
        var provider = new CatalogProvider(() => [new InventoryCoverageContractsAssembly("future",
            typeof(global::Catalog.Invalid.Contracts.DuplicateFirstQuery), typeof(global::Catalog.Invalid.Contracts.DuplicateSecondQuery))],
            new RecordingLogger<CatalogProvider>());
        Service(provider).ListOperations("future").Document.ShouldNotBeNull().Operations.Single().Name.ShouldBe("future.duplicate");
        Check(SingleOperationInventory("future"), Service(provider), provider).ShouldBe(Diagnostics(
            "catalog Catalog.Invalid.Contracts.DuplicateSecondQuery: duplicate_operation_name: Operation name future.duplicate is already declared by an earlier type."));
    }

    /// <summary>A Catalog error from another module still fails the checked module's gate.</summary>
    [Fact]
    public void RejectsCatalogErrorsFromOtherModules()
    {
        var provider = new CatalogProvider(() => [new InventoryCoverageContractsAssembly("future", typeof(global::Catalog.Invalid.Contracts.DuplicateFirstQuery)),
            new InventoryCoverageContractsAssembly("other",
                typeof(global::Catalog.Invalid.Contracts.DuplicateFirstQuery), typeof(global::Catalog.Invalid.Contracts.DuplicateSecondQuery))],
            new RecordingLogger<CatalogProvider>());
        Check(SingleOperationInventory("future"), Service(provider), provider).ShouldBe(Diagnostics(
            "catalog Catalog.Invalid.Contracts.DuplicateSecondQuery: duplicate_operation_name: Operation name other.duplicate is already declared by an earlier type."));
    }

    /// <summary>An inaccessible internal Catalog and failed public discovery are both reported.</summary>
    [Fact]
    public void RejectsEmptyCatalog()
    {
        var provider = new CatalogProvider(() => [], new RecordingLogger<CatalogProvider>());
        Check(Inventory(), Service(provider), provider).ShouldBe(Diagnostics(
            "catalog: internal Catalog error 'catalog_empty': The Catalog exposes no valid Operations.",
            "public: ListOperations error 'catalog_empty': The Catalog exposes no valid Operations."));
    }

    private static JsonObject SingleOperationInventory(string module)
    {
        JsonObject inventory = Inventory();
        inventory["module"] = module;
        inventory["purpose"] = "release";
        inventory["targets"] = new JsonArray(inventory["targets"]![0]!.DeepClone());
        inventory["targets"]![0]!["name"] = module + ".duplicate";
        inventory["targets"]![0]!["contractType"] = typeof(global::Catalog.Invalid.Contracts.DuplicateFirstQuery).FullName;
        inventory["legacyRows"] = new JsonArray(inventory["legacyRows"]![0]!.DeepClone());
        inventory["legacyRows"]![0]!["approval"]!["authority"] = "owning-maintainer";
        inventory["legacyRows"]![0]!["approval"]!["reference"] = "synthetic owner-evidence value for this test only";
        return inventory;
    }

    private static void CheckPublicDocument(JsonElement value, IReadOnlyList<string> mappedNames)
    {
        CheckPublicFields(value);
        foreach (string fullName in mappedNames)
        {
            value.GetRawText().ShouldNotContain(fullName);
        }
    }

    private static void CheckPublicFields(JsonElement value, bool documentRoot = true)
    {
        if (value.ValueKind == JsonValueKind.Object)
        {
            foreach (JsonProperty property in value.EnumerateObject())
            {
                property.Name.Contains("contractType", StringComparison.OrdinalIgnoreCase).ShouldBeFalse();
                property.Name.Contains("clrType", StringComparison.OrdinalIgnoreCase).ShouldBeFalse();
                if (!documentRoot || property.Name is not ("schema" or "example"))
                {
                    CheckPublicFields(property.Value, documentRoot: false);
                }
            }
        }
        else if (value.ValueKind == JsonValueKind.Array)
        {
            foreach (JsonElement item in value.EnumerateArray())
            {
                CheckPublicFields(item, documentRoot: false);
            }
        }
    }

    private static (JsonObject Parent, string Field, string Location) Field(JsonObject inventory, string path)
    {
        string[] parts = path.Split('.');
        JsonNode current = inventory;
        string location = "$";
        foreach (string part in parts.SkipLast(1))
        {
            current = int.TryParse(part, out int index) ? current[index]! : current[part]!;
            location += int.TryParse(part, out _) ? "[" + part + "]" : "." + part;
        }

        return (current.AsObject(), parts[^1], location + "." + parts[^1]);
    }

    private static IReadOnlyList<string> Check(JsonObject inventory, ICatalog? catalog = null, CatalogProvider? provider = null)
    {
        provider ??= Provider();
        return InventoryCoverageGate.Check(inventory.ToJsonString(), FileLabel, catalog ?? Service(provider), provider);
    }

    private static string[] Diagnostics(params string[] messages) => messages.Select(message => FileLabel + ":" + message).Order(StringComparer.Ordinal).ToArray();

    private static JsonObject Inventory() => JsonNode.Parse(System.IO.File.ReadAllText(ArtifactPath))!.AsObject();

    private static CatalogProvider Provider() => new(() => [typeof(CreateItemCommand).Assembly], new RecordingLogger<CatalogProvider>());

    private static ICatalog Service(CatalogProvider provider) => new CatalogService(provider, new ExecutionAvailability(true, false), strict: false);
}
