using Hexalith.Tenants.Authorization;
internal sealed class AdministratorAuthority(bool administrator) : ITenantsGlobalAdministratorAuthority
{
    public Task<bool> IsCurrentGlobalAdministratorAsync(string userId, CancellationToken cancellationToken)
        => Task.FromResult(administrator);
}
