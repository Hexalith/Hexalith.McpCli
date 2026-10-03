using System.Text.Json;
using System.Text.Json.Nodes;
using ByteAether.Ulid;
using Hexalith.EventStore.Client.Gateway;
using Hexalith.EventStore.Contracts.Commands;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Core.Catalog;
using Hexalith.McpCli.Core.Schema;

namespace Hexalith.McpCli.Core.Execution;

/// <summary>Validates and submits one declared operation through the EventStore gateway.</summary>
public sealed class OperationExecutor(
    CatalogProvider provider,
    ExecutionAvailability availability,
    IEventStoreGatewayClient gateway,
    bool strict) : IOperationExecutor
{
    private static readonly JsonDocumentOptions ParseOptions = new() { AllowDuplicateProperties = false };

    /// <inheritdoc />
    public async Task<OperationOutcome> ExecuteAsync(
        OperationCall call,
        EnvelopeContext context,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(call);
        ArgumentNullException.ThrowIfNull(context);
        try
        {
            return await ExecuteCoreAsync(call, context, cancellationToken).ConfigureAwait(false);
        }
        catch (EventStoreGatewayException exception)
        {
            return new OperationOutcome(null, OperationError.FromGateway(exception));
        }
        catch (Exception)
        {
            return new OperationOutcome(null, new OperationError("internal_error", Message: "Operation execution failed."));
        }
    }

    private async Task<OperationOutcome> ExecuteCoreAsync(
        OperationCall call,
        EnvelopeContext context,
        CancellationToken cancellationToken)
    {
        CatalogAccess access = provider.Get(strict);
        if (access.Catalog is null)
        {
            return new OperationOutcome(null, new OperationError(access.ErrorCode ?? "internal_error",
                Message: access.Message ?? "Catalog access failed."));
        }

        (ModuleDescriptor Module, OperationDescriptor Operation) selected = access.Catalog.Modules
            .SelectMany(module => module.Operations.Select(operation => (Module: module, Operation: operation)))
            .FirstOrDefault(item => string.Equals(item.Operation.Name, call.Operation, StringComparison.Ordinal));
        if (selected.Operation is null)
        {
            OperationError lookup = new CatalogService(provider, availability, strict).Describe(call.Operation).Error!;
            return new OperationOutcome(null, lookup);
        }

        (ModuleDescriptor module, OperationDescriptor operation) = selected;
        bool isCommand = call is SendCommandArguments;
        if ((isCommand && operation.Kind != OperationKind.Command)
            || (call is RunQueryArguments && operation.Kind != OperationKind.Query))
        {
            return Fail(call, "/operation", "The call kind does not match the declared operation kind.");
        }

        if (call is not (SendCommandArguments or RunQueryArguments))
        {
            return Fail(call, "/operation", "The operation call kind is unsupported.");
        }

        string? unavailable = availability.ReasonFor(operation.Kind);
        if (unavailable is not null)
        {
            return new OperationOutcome(null, new OperationError(unavailable,
                Message: unavailable == "read_only" ? "Command submission is disabled in read-only mode." : "Gateway URL is not configured."));
        }

        JsonElement raw;
        try
        {
            using JsonDocument document = JsonDocument.Parse(call.Payload, ParseOptions);
            raw = document.RootElement.Clone();
        }
        catch (Exception exception) when (exception is JsonException or ArgumentException)
        {
            return Fail(call, "/", "The payload must be valid JSON without duplicate properties.");
        }

        JsonNode? payload = JsonNode.Parse(raw.GetRawText());
        JsonNode? prefill = payload?.DeepClone();
        if (prefill is JsonObject prefillObject)
        {
            foreach (string member in operation.EnvelopeFilledProperties)
            {
                prefillObject.Remove(member);
            }
        }

        PayloadValidationResult prefillValidation = PayloadValidator.Validate(operation.Schema, ToElement(prefill), isCommand);
        if (!prefillValidation.IsValid)
        {
            return Fail(call, prefillValidation.Violations);
        }

        string? tenant = ResolveTenant(module, call.Tenant, context, out PayloadViolation? tenantViolation);
        if (tenantViolation is not null)
        {
            return Fail(call, tenantViolation);
        }

        if (!RoutingResolver.IsTenantDomain(tenant))
        {
            return Fail(call, "/tenant", "The tenant does not match the Gateway tenant pattern.");
        }

        string? actor = context.Actor;
        if (operation.PropertyBindings.ContainsKey(PropertyRole.Actor) && string.IsNullOrWhiteSpace(actor))
        {
            return Fail(call, "/actor", "The operation requires a trusted actor.");
        }

        if (operation.PropertyBindings.TryGetValue(PropertyRole.Tenant, out PropertyBinding? tenantBinding)
            && !RawMatches(raw, tenantBinding, tenant!))
        {
            return Fail(call, tenantBinding.Pointer, "The payload tenant disagrees with the resolved tenant.");
        }

        if (operation.PropertyBindings.TryGetValue(PropertyRole.Actor, out PropertyBinding? actorBinding)
            && !RawMatches(raw, actorBinding, actor!))
        {
            return Fail(call, actorBinding.Pointer, "The payload actor disagrees with the trusted actor.");
        }

        string? messageId = null;
        string? correlationId = null;
        string? idempotencyKey = null;
        Dictionary<string, string>? extensions = null;
        if (call is SendCommandArguments command)
        {
            messageId = Ulid.New().ToString();
            correlationId = command.CorrelationId ?? messageId;
            idempotencyKey = command.IdempotencyKey;
            if (!IsCanonicalUlid(correlationId))
            {
                return Fail(call, "/correlationId", "The correlation identifier must be a canonical uppercase ULID.");
            }

            if (idempotencyKey is not null && !IsCanonicalUlid(idempotencyKey))
            {
                return Fail(call, "/idempotencyKey", "The idempotency key must be a canonical uppercase ULID.");
            }

            if (operation.IdempotencyKeyRequired && idempotencyKey is null)
            {
                return Fail(call, "/idempotencyKey", "This operation requires a caller-supplied idempotency key.");
            }

            if (operation.PropertyBindings.TryGetValue(PropertyRole.IdempotencyKey, out PropertyBinding? keyBinding)
                && RawHasNonNull(raw, keyBinding)
                && idempotencyKey is null)
            {
                return Fail(call, "/idempotencyKey", "A payload idempotency key requires a caller-supplied key.");
            }

            extensions = command.Extensions is null ? null : new Dictionary<string, string>(command.Extensions, StringComparer.Ordinal);
            IReadOnlyList<PayloadViolation> extensionViolations = ExtensionValidator.Validate(extensions, context.AllowedExtensions);
            if (extensionViolations.Count > 0)
            {
                return Fail(call, extensionViolations);
            }
        }
        else if (call is RunQueryArguments query)
        {
            PayloadViolation? pagingViolation = ValidateQueryArguments(query);
            if (pagingViolation is not null)
            {
                return Fail(call, pagingViolation);
            }
        }

        if (payload is JsonObject payloadObject)
        {
            Fill(payloadObject, operation, PropertyRole.Tenant, tenant);
            Fill(payloadObject, operation, PropertyRole.Actor, actor);
            Fill(payloadObject, operation, PropertyRole.Correlation, correlationId);
            Fill(payloadObject, operation, PropertyRole.IdempotencyKey, idempotencyKey);
        }

        JsonElement rebuilt = ToElement(payload);
        PayloadValidationResult finalValidation = PayloadValidator.Validate(operation.Schema, rebuilt, isCommand);
        if (!finalValidation.IsValid)
        {
            return Fail(call, finalValidation.Violations);
        }

        string? accessorId = operation.AggregateIdAccessor?.Invoke(rebuilt);
        if (call.AggregateId is not null && accessorId is not null
            && !string.Equals(call.AggregateId, accessorId, StringComparison.Ordinal))
        {
            return Fail(call, "/aggregateId", "The explicit aggregate identifier disagrees with the payload.");
        }

        string? aggregateId = call.AggregateId ?? accessorId ?? operation.AggregateIdConstant;
        if (string.IsNullOrWhiteSpace(aggregateId)
            || module.IdentifierKind == IdentifierKind.Ulid && !IsCanonicalUlid(aggregateId)
            || !RoutingResolver.IsAggregateId(aggregateId))
        {
            return Fail(call, "/aggregateId", "The aggregate identifier does not match the module and Gateway rules.");
        }

        if (call is SendCommandArguments)
        {
            var request = new SubmitCommandRequest(messageId!, tenant!, operation.Routing.Domain, aggregateId!,
                operation.Routing.WireType, rebuilt, correlationId,
                extensions, idempotencyKey);
            SubmitCommandResponse response = await gateway.SubmitCommandAsync(request, cancellationToken).ConfigureAwait(false);
            return new OperationOutcome(new CommandResult(operation.Name, response.MessageId ?? messageId!,
                correlationId!, tenant!, aggregateId!, "accepted", idempotencyKey, response.ResultPayload), null);
        }

        var run = (RunQueryArguments)call;
        var queryRequest = new SubmitQueryRequest(tenant!, operation.Routing.Domain, aggregateId!, operation.Routing.WireType,
            operation.Routing.ProjectionType, rebuilt.ValueKind == JsonValueKind.Null ? null : rebuilt,
            run.EntityId, operation.Routing.ProjectionActorType)
        {
            Paging = run.PageSize is not null || run.Offset is not null || run.Cursor is not null
                ? new QueryPagingOptions(run.PageSize, run.Offset, run.Cursor) : null,
        };
        EventStoreQueryResult result = await gateway.SubmitQueryAsync(queryRequest, cancellationToken: cancellationToken)
            .ConfigureAwait(false);
        QueryPagingMetadata? paging = result.Metadata?.Paging;
        return new OperationOutcome(new QueryResult(operation.Name, tenant!, result.Payload,
            paging is null ? null : new QueryPagingDocument(paging.PageSize, paging.Offset, paging.NextCursor,
                paging.TotalCount, paging.HasMore)), null);
    }

    private static void Fill(JsonObject payload, OperationDescriptor operation, PropertyRole role, string? value)
    {
        if (!operation.PropertyBindings.TryGetValue(role, out PropertyBinding? binding))
        {
            return;
        }

        if (value is null)
        {
            payload.Remove(binding.SerializedName);
        }
        else
        {
            payload[binding.SerializedName] = value;
        }
    }

    private static bool RawMatches(JsonElement raw, PropertyBinding binding, string expected)
        => raw.ValueKind != JsonValueKind.Object
            || !raw.TryGetProperty(binding.SerializedName, out JsonElement supplied)
            || supplied.ValueKind == JsonValueKind.String && string.Equals(supplied.GetString(), expected, StringComparison.Ordinal);

    private static bool RawHasNonNull(JsonElement raw, PropertyBinding binding)
        => raw.ValueKind == JsonValueKind.Object
            && raw.TryGetProperty(binding.SerializedName, out JsonElement supplied)
            && supplied.ValueKind != JsonValueKind.Null;

    private static string? ResolveTenant(ModuleDescriptor module, string? perCall, EnvelopeContext context,
        out PayloadViolation? violation)
    {
        violation = null;
        if (module.FixedTenant is not null)
        {
            if (perCall is not null && !string.Equals(perCall, module.FixedTenant, StringComparison.Ordinal))
            {
                violation = new PayloadViolation("/tenant", "The per-call tenant disagrees with the module's fixed tenant.");
            }

            return module.FixedTenant;
        }

        if (context.Tenant is not null && perCall is not null
            && !context.AllowTenantOverride && !string.Equals(perCall, context.Tenant, StringComparison.Ordinal))
        {
            violation = new PayloadViolation("/tenant", "Per-call tenant override is disabled.");
            return null;
        }

        return perCall is not null && (context.Tenant is null || context.AllowTenantOverride) ? perCall : context.Tenant;
    }

    private static PayloadViolation? ValidateQueryArguments(RunQueryArguments query)
    {
        if (query.PageSize is < 1 or > 200)
        {
            return new PayloadViolation("/pageSize", "Page size must be between 1 and 200.");
        }

        if (query.Offset is < 0)
        {
            return new PayloadViolation("/offset", "Offset cannot be negative.");
        }

        if (query.Cursor is { Length: > 4096 } || !string.IsNullOrWhiteSpace(query.Cursor) && query.Offset is not null)
        {
            return new PayloadViolation("/cursor", "Cursor must be at most 4096 characters and cannot be combined with offset.");
        }

        if (query.EntityId is not null && !RoutingResolver.IsAggregateId(query.EntityId))
        {
            return new PayloadViolation("/entityId", "Entity identifier does not match the Gateway pattern.");
        }

        return null;
    }

    private static JsonElement ToElement(JsonNode? node)
    {
        using JsonDocument document = JsonDocument.Parse(node?.ToJsonString() ?? "null");
        return document.RootElement.Clone();
    }

    private static bool IsCanonicalUlid(string value)
        => Ulid.TryParse(value, provider: null, out Ulid parsed)
            && string.Equals(value, parsed.ToString(), StringComparison.Ordinal);

    private static OperationOutcome Fail(OperationCall call, string path, string message)
        => Fail(call, [new PayloadViolation(path, message)]);

    private static OperationOutcome Fail(OperationCall call, PayloadViolation violation)
        => Fail(call, [violation]);

    private static OperationOutcome Fail(OperationCall call, IReadOnlyList<PayloadViolation> violations)
        => new(null, new OperationError("validation_failed", Operation: call.Operation, Violations: violations));
}
