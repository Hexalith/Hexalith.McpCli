using System.Reflection;
using System.Runtime.Loader;
using Hexalith.McpCli.Abstractions;

namespace Hexalith.McpCli.Core.Catalog;

/// <summary>
/// Binds enrolled Contracts assemblies to the host <c>Hexalith.McpCli.Abstractions</c> assembly.
/// </summary>
/// <remarks>
/// Enrolled packages compile against a published Abstractions version. Local and later host builds
/// often carry a different assembly version, and <see cref="CustomAttributeExtensions.GetCustomAttribute{T}(Assembly)"/>
/// then fails with <see cref="FileNotFoundException"/> before any module is cataloged.
/// </remarks>
internal static class CatalogAbstractionsResolver
{
    private const string AbstractionsAssemblyName = "Hexalith.McpCli.Abstractions";
    private static int _registered;

    /// <summary>Registers the default load-context binder once per process.</summary>
    internal static void Register()
    {
        if (Interlocked.Exchange(ref _registered, 1) == 1)
        {
            return;
        }

        AssemblyLoadContext.Default.Resolving += Resolve;
    }

    /// <summary>Returns the host Abstractions assembly when a Contracts package requests that name.</summary>
    /// <param name="context">The load context requesting the assembly.</param>
    /// <param name="name">The requested assembly identity.</param>
    /// <returns>The host Abstractions assembly, or <see langword="null"/> for any other name.</returns>
    internal static Assembly? Resolve(AssemblyLoadContext context, AssemblyName name)
    {
        ArgumentNullException.ThrowIfNull(context);
        ArgumentNullException.ThrowIfNull(name);
        return string.Equals(name.Name, AbstractionsAssemblyName, StringComparison.Ordinal)
            ? typeof(HexalithModuleAttribute).Assembly
            : null;
    }
}
