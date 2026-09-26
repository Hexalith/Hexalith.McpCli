using System.Reflection;
using System.Reflection.Emit;

namespace Hexalith.McpCli.Core.Tests;

/// <summary>Emits serializer options providers into fresh assemblies so each declaration bypasses the per-assembly cache.</summary>
public static class DynamicProviderFactory
{
    private static int _count;

    /// <summary>Emits a provider type in its own dynamic assembly.</summary>
    /// <param name="optionsType">The static <c>Options</c> property type, or <see langword="null"/> to omit the property.</param>
    /// <returns>The provider type; its property getter returns <see langword="null"/>.</returns>
    public static Type Emit(Type? optionsType) => Emit(optionsType, throwFromGetter: false, throwFromInitializer: false);

    /// <summary>Emits a provider whose static <c>Options</c> getter throws <see cref="InvalidOperationException"/>.</summary>
    /// <returns>The provider type.</returns>
    public static Type EmitThrowing() => Emit(typeof(System.Text.Json.JsonSerializerOptions), throwFromGetter: true, throwFromInitializer: false);

    /// <summary>Emits a provider whose static constructor throws <see cref="InvalidOperationException"/>.</summary>
    /// <returns>The provider type.</returns>
    public static Type EmitThrowingInitializer()
        => Emit(typeof(System.Text.Json.JsonSerializerOptions), throwFromGetter: false, throwFromInitializer: true);

    private static Type Emit(Type? optionsType, bool throwFromGetter, bool throwFromInitializer)
    {
        AssemblyBuilder assembly = AssemblyBuilder.DefineDynamicAssembly(
            new AssemblyName("DynamicProvider" + Interlocked.Increment(ref _count).ToString(System.Globalization.CultureInfo.InvariantCulture)),
            AssemblyBuilderAccess.Run);
        ModuleBuilder module = assembly.DefineDynamicModule("Provider");
        TypeBuilder type = module.DefineType(
            "Provider",
            TypeAttributes.Public | TypeAttributes.Abstract | TypeAttributes.Sealed | TypeAttributes.Class);
        if (throwFromInitializer)
        {
            ILGenerator initializer = type.DefineTypeInitializer().GetILGenerator();
            initializer.Emit(OpCodes.Ldstr, "Initializer failure.");
            initializer.Emit(OpCodes.Newobj, typeof(InvalidOperationException).GetConstructor([typeof(string)])!);
            initializer.Emit(OpCodes.Throw);
        }

        if (optionsType is not null)
        {
            MethodBuilder getter = type.DefineMethod(
                "get_Options",
                MethodAttributes.Public | MethodAttributes.Static | MethodAttributes.SpecialName | MethodAttributes.HideBySig,
                optionsType,
                Type.EmptyTypes);
            ILGenerator il = getter.GetILGenerator();
            if (throwFromGetter)
            {
                il.Emit(OpCodes.Ldstr, "Provider failure.");
                il.Emit(OpCodes.Newobj, typeof(InvalidOperationException).GetConstructor([typeof(string)])!);
                il.Emit(OpCodes.Throw);
            }
            else
            {
                il.Emit(OpCodes.Ldnull);
                il.Emit(OpCodes.Ret);
            }
            PropertyBuilder property = type.DefineProperty("Options", PropertyAttributes.None, optionsType, null);
            property.SetGetMethod(getter);
        }

        return type.CreateType();
    }
}
