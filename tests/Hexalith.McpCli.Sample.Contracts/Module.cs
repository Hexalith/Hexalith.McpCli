using Hexalith.McpCli.Abstractions;
using Hexalith.McpCli.Sample.Contracts;

[assembly: HexalithModule(
    "sample",
    "Synthetic operations for testing module declarations.",
    IdentifierKind.Ulid,
    WireTypeConvention = WireTypeConvention.KebabCase,
    SerializerOptionsProvider = typeof(SampleSerializerOptions))]
