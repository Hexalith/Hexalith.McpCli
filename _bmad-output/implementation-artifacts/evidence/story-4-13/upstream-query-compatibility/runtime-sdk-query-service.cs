using System;
using System.CodeDom.Compiler;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Text.RegularExpressions.Generated;
using System.Threading;
using System.Threading.Tasks;
using Hexalith.EventStore.Client.Projections;
using Hexalith.EventStore.Client.Queries;
using Hexalith.EventStore.Contracts.Queries;
using Hexalith.Parties.Contracts;
using Hexalith.Parties.Contracts.Models;
using Hexalith.Parties.Contracts.Search;
using Hexalith.Parties.Contracts.Security;
using Hexalith.Parties.Contracts.ValueObjects;
using Hexalith.Parties.Projections.Configuration;
using Hexalith.Parties.Projections.Handlers;
using Hexalith.Parties.Projections.Models;
using Hexalith.Parties.Search;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace Hexalith.Parties.Queries;

public sealed class PartySdkQueryService(IReadModelStore readModelStore, IOptions<PartySdkReadModelOptions> options, TimeProvider timeProvider, IPartySearchProvider searchProvider, IPartyErasureRecordStore erasureRecordStore, IQueryCursorCodec cursorCodec, PartySdkLastKnownReadModelCache lastKnownCache, ILogger<PartySdkQueryService> logger)
{
	private static readonly JsonSerializerOptions s_jsonOptions = PartiesJsonOptions.Default;

	private static readonly PartyDetailSdkReadModel s_unknownFreshness = new PartyDetailSdkReadModel();

	[GeneratedCode("Microsoft.Extensions.Logging.Generators", "10.0.15.504")]
	private static readonly Action<ILogger, string?, string, Exception?> __LogQueryFailedCallback = LoggerMessage.Define<string, string>(LogLevel.Warning, new EventId(115744526, "LogQueryFailed"), "Party SDK query {QueryType} failed with {ExceptionType}.", new LogDefineOptions
	{
		SkipEnabledCheck = true
	});

	[GeneratedCode("Microsoft.Extensions.Logging.Generators", "10.0.15.504")]
	private static readonly Action<ILogger, string, Exception?> __LogProcessingUnavailableCallback = LoggerMessage.Define<string>(LogLevel.Warning, new EventId(638777444, "LogProcessingUnavailable"), "Party processing read model unavailable with {ExceptionType}; returning empty degraded records.", new LogDefineOptions
	{
		SkipEnabledCheck = true
	});

	[GeneratedCode("Microsoft.Extensions.Logging.Generators", "10.0.15.504")]
	private static readonly Action<ILogger, string?, string, Exception?> __LogCursorRejectedCallback = LoggerMessage.Define<string, string>(LogLevel.Debug, new EventId(395460769, "LogCursorRejected"), "Party query cursor rejected for queryType {QueryType}: {FailureReason}.", new LogDefineOptions
	{
		SkipEnabledCheck = true
	});

	private ReadModelFreshnessThresholds Thresholds => ReadModelFreshnessThresholds.Create(TimeSpan.FromSeconds(options.Value.FreshnessAgingSeconds), TimeSpan.FromSeconds(options.Value.FreshnessStaleSeconds));

	private string StoreName
	{
		get
		{
			string readModelStateStoreName = options.Value.ReadModelStateStoreName;
			ArgumentException.ThrowIfNullOrWhiteSpace(readModelStateStoreName, "value");
			return readModelStateStoreName;
		}
	}

	[GeneratedRegex("\\A[A-Za-z0-9_\\-\\.]{1,128}\\z", RegexOptions.CultureInvariant)]
	[GeneratedCode("System.Text.RegularExpressions.Generator", "10.0.15.504")]
	private static Regex ValidTenantIdRegex()
	{
		return <RegexGenerator_g>FED5B25CF2702215D5AE5F4425A661A16DCC860A37079FB997C39919A9E8221EA__ValidTenantIdRegex_0.Instance;
	}

	public Task<QueryResult> GetPartyAsync(QueryEnvelope query, CancellationToken cancellationToken)
	{
		ArgumentNullException.ThrowIfNull(query, "query");
		return ReadDetailAsync(query, cancellationToken);
	}

	public Task<QueryResult> GetPartyDetailAsync(QueryEnvelope query, CancellationToken cancellationToken)
	{
		ArgumentNullException.ThrowIfNull(query, "query");
		return ReadDetailAsync(query, cancellationToken);
	}

	public async Task<QueryResult> ExportPartyDataAsync(QueryEnvelope query, CancellationToken cancellationToken)
	{
		ArgumentNullException.ThrowIfNull(query, "query");
		if (!TryValidateDetailEnvelope(query, out string partyId))
		{
			return QueryResult.Failure("invalid-envelope");
		}
		try
		{
			(ReadModelEntry<PartyDetailSdkReadModel>, bool) tuple = await ReadDetailModelAsync(query.TenantId, partyId, cancellationToken).ConfigureAwait(continueOnCapturedContext: false);
			ReadModelEntry<PartyDetailSdkReadModel> read = tuple.Item1;
			bool degraded = tuple.Item2;
			PartyDetail stored = read.Value?.Detail;
			if ((object)stored == null)
			{
				return QueryResult.Failure("actor-not-found-infrastructure");
			}
			(ReadModelEntry<PartyProcessingSdkReadModel>, bool) tuple2 = await ReadProcessingModelAsync(query.TenantId, partyId, cancellationToken).ConfigureAwait(continueOnCapturedContext: false);
			ReadModelEntry<PartyProcessingSdkReadModel> item = tuple2.Item1;
			bool item2 = tuple2.Item2;
			degraded = degraded || item2;
			DateTimeOffset utcNow = timeProvider.GetUtcNow();
			ProjectionFreshnessMetadata freshness = ToPartiesFreshness(read.Value, utcNow, degraded);
			PartyDetail partyDetail = stored with
			{
				Freshness = freshness
			};
			IReadOnlyList<ProcessingActivityRecord> processingRecords = item.Value?.Records ?? Array.Empty<ProcessingActivityRecord>();
			bool flag = string.IsNullOrWhiteSpace(partyDetail.DisplayName) || string.IsNullOrWhiteSpace(partyDetail.SortName);
			PartyDataPortabilityPackage payload = new PartyDataPortabilityPackage
			{
				PartyId = partyDetail.Id,
				TenantId = query.TenantId,
				Status = (partyDetail.IsErased ? "Erased" : (flag ? "PersonalDataUnavailable" : (partyDetail.IsRestricted ? "RestrictedExported" : "Exported"))),
				ExportedAt = utcNow,
				ExportedBy = (string.IsNullOrWhiteSpace(query.UserId) ? "unknown" : query.UserId.Trim()),
				CorrelationId = (string.IsNullOrWhiteSpace(query.CorrelationId) ? "unspecified" : query.CorrelationId.Trim()),
				Party = ((partyDetail.IsErased || flag) ? null : partyDetail),
				ProcessingRecords = processingRecords,
				Freshness = freshness
			};
			return Success(payload, "party-data-portability", read.Value, read.ETag, utcNow, degraded);
		}
		catch (OperationCanceledException)
		{
			throw;
		}
		catch (Exception ex2)
		{
			LogQueryFailed(query.QueryType, ex2.GetType().Name);
			return QueryResult.Failure("actor-exception");
		}
	}

	public async Task<QueryResult> GetProcessingRecordsAsync(QueryEnvelope query, CancellationToken cancellationToken)
	{
		ArgumentNullException.ThrowIfNull(query, "query");
		if (!TryValidateDetailEnvelope(query, out string partyId))
		{
			return QueryResult.Failure("invalid-envelope");
		}
		try
		{
			var (readModelEntry, detailDegraded) = await ReadDetailModelAsync(query.TenantId, partyId, cancellationToken).ConfigureAwait(continueOnCapturedContext: false);
			if ((object)readModelEntry.Value?.Detail == null)
			{
				return QueryResult.Failure("actor-not-found-infrastructure");
			}
			(ReadModelEntry<PartyProcessingSdkReadModel>, bool) tuple2 = await ReadProcessingModelAsync(query.TenantId, partyId, cancellationToken).ConfigureAwait(continueOnCapturedContext: false);
			ReadModelEntry<PartyProcessingSdkReadModel> item = tuple2.Item1;
			bool item2 = tuple2.Item2;
			item2 = item2 || detailDegraded;
			PartyProcessingSdkReadModel partyProcessingSdkReadModel = item.Value ?? new PartyProcessingSdkReadModel();
			return Success(partyProcessingSdkReadModel.Records, "party-processing-records", partyProcessingSdkReadModel, item.ETag, timeProvider.GetUtcNow(), item2);
		}
		catch (OperationCanceledException)
		{
			throw;
		}
		catch (Exception ex2)
		{
			LogQueryFailed(query.QueryType, ex2.GetType().Name);
			return QueryResult.Failure("actor-exception");
		}
	}

	public async Task<QueryResult> GetErasureStatusAsync(QueryEnvelope query, CancellationToken cancellationToken)
	{
		ArgumentNullException.ThrowIfNull(query, "query");
		if (!TryValidateDetailEnvelope(query, out string partyId))
		{
			return QueryResult.Failure("invalid-envelope");
		}
		try
		{
			(ReadModelEntry<PartyDetailSdkReadModel>, bool) tuple = await ReadDetailModelAsync(query.TenantId, partyId, cancellationToken).ConfigureAwait(continueOnCapturedContext: false);
			ReadModelEntry<PartyDetailSdkReadModel> item = tuple.Item1;
			bool item2 = tuple.Item2;
			PartyDetailSdkReadModel value = item.Value;
			PartyErasureStatusRecord payload = value?.ErasureLifecycle;
			return Success(payload, "party-erasure-status", value ?? s_unknownFreshness, item.ETag, timeProvider.GetUtcNow(), item2);
		}
		catch (OperationCanceledException)
		{
			throw;
		}
		catch (Exception ex2)
		{
			LogQueryFailed(query.QueryType, ex2.GetType().Name);
			return QueryResult.Failure("actor-exception");
		}
	}

	public async Task<QueryResult> GetErasureCertificateAsync(QueryEnvelope query, CancellationToken cancellationToken)
	{
		ArgumentNullException.ThrowIfNull(query, "query");
		if (!TryValidateDetailEnvelope(query, out string partyId))
		{
			return QueryResult.Failure("invalid-envelope");
		}
		try
		{
			return Success(await erasureRecordStore.GetCertificateAsync(query.TenantId, partyId, cancellationToken).ConfigureAwait(continueOnCapturedContext: false), "party-erasure-certificate", s_unknownFreshness, null, timeProvider.GetUtcNow());
		}
		catch (OperationCanceledException)
		{
			throw;
		}
		catch (Exception ex2)
		{
			LogQueryFailed(query.QueryType, ex2.GetType().Name);
			return QueryResult.Failure("actor-exception");
		}
	}

	public async Task<QueryResult> GetPartyIndexAsync(QueryEnvelope query, CancellationToken cancellationToken)
	{
		ArgumentNullException.ThrowIfNull(query, "query");
		if (!TryValidateIndexEnvelope(query) || !PartyIndexQueryTypes.TryParseListPayload(query.Payload, out ListPartiesQueryPayload payload, (object)query.Paging != null))
		{
			return QueryResult.Failure("invalid-envelope");
		}
		string cursorScope = CreateListCursorScope(query, payload, ScopePageSize(query, payload.PageSize));
		if (!TryResolvePaging(query, payload.Page, payload.PageSize, cursorScope, out int pageNumber, out int pageSize, out int offset, out string failureReason))
		{
			return QueryResult.Failure(failureReason);
		}
		return await ReadIndexAsync(query, cancellationToken, delegate(PartyIndexSdkReadModel model, ProjectionFreshnessMetadata freshness)
		{
			IEnumerable<PartyIndexEntry> values = model.Entries.Values;
			PagedResult<PartyIndexEntry> pagedResult = PartySearchResultsBuilder.BuildPagedList(values, payload.Type, payload.Active, payload.CreatedAfter, payload.CreatedBefore, payload.ModifiedAfter, payload.ModifiedBefore, pageNumber, pageSize)with
			{
				Freshness = freshness
			};
			return (Payload: pagedResult, Paging: CreatePagingMetadata(query, cursorScope, offset, pagedResult.PageSize, pagedResult.Items.Count, pagedResult.TotalCount));
		}).ConfigureAwait(continueOnCapturedContext: false);
	}

	public async Task<QueryResult> SearchPartiesAsync(QueryEnvelope query, CancellationToken cancellationToken)
	{
		ArgumentNullException.ThrowIfNull(query, "query");
		if (!TryValidateIndexEnvelope(query) || !PartyIndexQueryTypes.TryParseSearchPayload(query.Payload, out SearchPartiesQueryPayload payload, (object)query.Paging != null))
		{
			return QueryResult.Failure("invalid-envelope");
		}
		if (PartyIndexQueryTypes.IsUnsupportedSearchMode(payload.Mode) || payload.CaseId != null)
		{
			return QueryResult.Failure("unsupported-query-type");
		}
		string cursorScope = CreateSearchCursorScope(query, payload, ScopePageSize(query, payload.PageSize));
		if (!TryResolvePaging(query, payload.Page, payload.PageSize, cursorScope, out int pageNumber, out int pageSize, out int offset, out string failureReason))
		{
			return QueryResult.Failure(failureReason);
		}
		return await ReadIndexAsync(query, cancellationToken, delegate(PartyIndexSdkReadModel model, ProjectionFreshnessMetadata freshness)
		{
			IEnumerable<PartyIndexEntry> entries = model.Entries.Values.Where((PartyIndexEntry entry) => !entry.IsErased);
			PagedResult<PartySearchResult> pagedResult = searchProvider.Search(entries, payload.Query, payload.Type, payload.Active, pageNumber, pageSize, cancellationToken)with
			{
				Freshness = freshness
			};
			return (Payload: pagedResult, Paging: CreatePagingMetadata(query, cursorScope, offset, pagedResult.PageSize, pagedResult.Items.Count, pagedResult.TotalCount));
		}).ConfigureAwait(continueOnCapturedContext: false);
	}

	private async Task<QueryResult> ReadDetailAsync(QueryEnvelope query, CancellationToken cancellationToken)
	{
		if (!TryValidateDetailEnvelope(query, out string partyId))
		{
			return QueryResult.Failure("invalid-envelope");
		}
		try
		{
			(ReadModelEntry<PartyDetailSdkReadModel>, bool) tuple = await ReadDetailModelAsync(query.TenantId, partyId, cancellationToken).ConfigureAwait(continueOnCapturedContext: false);
			ReadModelEntry<PartyDetailSdkReadModel> item = tuple.Item1;
			bool item2 = tuple.Item2;
			PartyDetail partyDetail = item.Value?.Detail;
			if ((object)partyDetail == null || partyDetail.IsErased)
			{
				return QueryResult.Failure("actor-not-found-infrastructure");
			}
			DateTimeOffset utcNow = timeProvider.GetUtcNow();
			PartyDetail payload = partyDetail with
			{
				Freshness = ToPartiesFreshness(item.Value, utcNow, item2)
			};
			return Success(payload, "party-detail", item.Value, item.ETag, utcNow, item2);
		}
		catch (OperationCanceledException)
		{
			throw;
		}
		catch (Exception ex2)
		{
			LogQueryFailed(query.QueryType, ex2.GetType().Name);
			return QueryResult.Failure("actor-exception");
		}
	}

	private async Task<QueryResult> ReadIndexAsync<TPayload>(QueryEnvelope query, CancellationToken cancellationToken, Func<PartyIndexSdkReadModel, ProjectionFreshnessMetadata, (TPayload Payload, QueryPagingMetadata? Paging)> createPayload)
	{
		try
		{
			string storeName = StoreName;
			bool degraded = false;
			long cacheGeneration = lastKnownCache.BeginRead(PartySdkReadModelAddresses.Index(query.TenantId));
			ReadModelEntry<PartyIndexSdkReadModel> readModelEntry;
			try
			{
				readModelEntry = await readModelStore.GetAsync<PartyIndexSdkReadModel>(storeName, PartySdkReadModelAddresses.Index(query.TenantId), cancellationToken).ConfigureAwait(continueOnCapturedContext: false);
				if ((object)readModelEntry.Value != null)
				{
					PartyIndexSdkReadModel value = readModelEntry.Value;
					if ((object)value == null || value.Entries == null || value.LastIndexedEvents == null || value.LastSequenceNumbers == null || value.ErasureSequenceNumbers == null)
					{
						lastKnownCache.EvictIndex(query.TenantId);
						return QueryResult.Failure("actor-exception");
					}
				}
				if ((object)readModelEntry.Value == null)
				{
					lastKnownCache.EvictIndex(query.TenantId);
				}
				else if (!lastKnownCache.StoreIndexIfCurrent(query.TenantId, cacheGeneration, readModelEntry.Value))
				{
					throw new InvalidOperationException("read-model-invalidated");
				}
			}
			catch (OperationCanceledException)
			{
				throw;
			}
			catch (Exception)
			{
				if (!lastKnownCache.TryGetIndex(query.TenantId, out PartyIndexSdkReadModel value2))
				{
					throw;
				}
				if ((object)value2 == null)
				{
					goto IL_01dc;
				}
				IReadOnlyDictionary<string, PartyIndexEntry> entries = value2.Entries;
				if (entries == null || entries.Count != 0 || value2.LastIndexedEvents == null || value2.LastSequenceNumbers == null || value2.ErasureSequenceNumbers == null)
				{
					goto IL_01dc;
				}
				readModelEntry = new ReadModelEntry<PartyIndexSdkReadModel>(value2, null);
				degraded = true;
				goto end_IL_018a;
				IL_01dc:
				lastKnownCache.EvictIndex(query.TenantId);
				throw;
				end_IL_018a:;
			}
			finally
			{
				lastKnownCache.EndRead(cacheGeneration);
			}
			PartyIndexSdkReadModel value3 = readModelEntry.Value;
			if ((object)value3 == null)
			{
				return QueryResult.Failure("actor-not-found-infrastructure");
			}
			DateTimeOffset utcNow = timeProvider.GetUtcNow();
			var (payload, paging) = createPayload(value3, ToPartiesFreshness(value3, utcNow, degraded));
			return Success(payload, "party-index", value3, readModelEntry.ETag, utcNow, degraded, paging);
		}
		catch (OperationCanceledException)
		{
			throw;
		}
		catch (Exception ex4)
		{
			LogQueryFailed(query.QueryType, ex4.GetType().Name);
			return QueryResult.Failure("actor-exception");
		}
	}

	private async Task<(ReadModelEntry<PartyDetailSdkReadModel> Read, bool Degraded)> ReadDetailModelAsync(string tenantId, string partyId, CancellationToken cancellationToken)
	{
		long cacheGeneration = lastKnownCache.BeginRead(PartySdkReadModelAddresses.Detail(tenantId, partyId));
		try
		{
			ReadModelEntry<PartyDetailSdkReadModel> readModelEntry = await readModelStore.GetAsync<PartyDetailSdkReadModel>(StoreName, PartySdkReadModelAddresses.Detail(tenantId, partyId), cancellationToken).ConfigureAwait(continueOnCapturedContext: false);
			PartyDetail partyDetail = readModelEntry.Value?.Detail;
			if ((object)partyDetail != null && partyDetail.IsErased)
			{
				readModelEntry = new ReadModelEntry<PartyDetailSdkReadModel>(readModelEntry.Value with
				{
					Detail = PartyDetailProjectionHandler.ApplyErasure(partyId, partyDetail)with
					{
						ErasedAt = partyDetail.ErasedAt,
						LastModifiedAt = partyDetail.LastModifiedAt
					}
				}, readModelEntry.ETag);
			}
			if ((object)readModelEntry.Value == null)
			{
				lastKnownCache.EvictDetail(tenantId, partyId);
			}
			else if (!lastKnownCache.StoreDetailIfCurrent(tenantId, partyId, cacheGeneration, readModelEntry.Value))
			{
				throw new InvalidOperationException("read-model-invalidated");
			}
			return (Read: readModelEntry, Degraded: false);
		}
		catch (OperationCanceledException)
		{
			throw;
		}
		catch (Exception)
		{
			if (!lastKnownCache.TryGetDetail(tenantId, partyId, out PartyDetailSdkReadModel value))
			{
				throw;
			}
			PartyDetail detail = value.Detail;
			if ((object)detail != null && !detail.IsErased)
			{
				lastKnownCache.EvictDetail(tenantId, partyId);
				throw;
			}
			PartyDetail detail2 = value.Detail;
			if ((object)detail2 != null)
			{
				value = value with
				{
					Detail = PartyDetailProjectionHandler.ApplyErasure(partyId, detail2)with
					{
						ErasedAt = detail2.ErasedAt,
						LastModifiedAt = detail2.LastModifiedAt
					}
				};
			}
			return (Read: new ReadModelEntry<PartyDetailSdkReadModel>(value, null), Degraded: true);
		}
		finally
		{
			lastKnownCache.EndRead(cacheGeneration);
		}
	}

	private async Task<(ReadModelEntry<PartyProcessingSdkReadModel> Read, bool Degraded)> ReadProcessingModelAsync(string tenantId, string partyId, CancellationToken cancellationToken)
	{
		long cacheGeneration = lastKnownCache.BeginRead(PartySdkReadModelAddresses.Processing(tenantId, partyId));
		PartyProcessingSdkReadModel value;
		try
		{
			ReadModelEntry<PartyProcessingSdkReadModel> readModelEntry = await readModelStore.GetAsync<PartyProcessingSdkReadModel>(StoreName, PartySdkReadModelAddresses.Processing(tenantId, partyId), cancellationToken).ConfigureAwait(continueOnCapturedContext: false);
			if ((object)readModelEntry.Value == null)
			{
				lastKnownCache.EvictProcessing(tenantId, partyId);
			}
			else if (!lastKnownCache.StoreProcessingIfCurrent(tenantId, partyId, cacheGeneration, readModelEntry.Value))
			{
				throw new InvalidOperationException("read-model-invalidated");
			}
			return ((object)readModelEntry.Value == null) ? (Read: new ReadModelEntry<PartyProcessingSdkReadModel>(new PartyProcessingSdkReadModel(), null), Degraded: true) : (Read: readModelEntry, Degraded: false);
		}
		catch (OperationCanceledException)
		{
			throw;
		}
		catch (Exception) when (lastKnownCache.TryGetProcessing(tenantId, partyId, out value))
		{
			return (Read: new ReadModelEntry<PartyProcessingSdkReadModel>(value, null), Degraded: true);
		}
		catch (Exception ex3)
		{
			LogProcessingUnavailable(ex3.GetType().Name);
			return (Read: new ReadModelEntry<PartyProcessingSdkReadModel>(new PartyProcessingSdkReadModel(), null), Degraded: true);
		}
		finally
		{
			lastKnownCache.EndRead(cacheGeneration);
		}
	}

	private QueryResult Success<TPayload>(TPayload payload, string projectionType, IReadModelFreshness freshness, string? etag, DateTimeOffset now, bool degraded = false, QueryPagingMetadata? paging = null)
	{
		QueryResponseMetadata queryResponseMetadata = freshness.ToQueryResponseMetadata(Thresholds, now, etag);
		QueryResponseMetadata obj = queryResponseMetadata with
		{
			IsStale = (degraded ? new bool?(true) : queryResponseMetadata.IsStale),
			IsDegraded = degraded,
			Paging = paging
		};
		IReadOnlyList<string> warningCodes;
		if (!degraded)
		{
			warningCodes = queryResponseMetadata.WarningCodes;
		}
		else
		{
			IReadOnlyList<string> readOnlyList = new global::<>z__ReadOnlySingleElementList<string>("projection-state-store-unavailable");
			warningCodes = readOnlyList;
		}
		obj.WarningCodes = warningCodes;
		obj.Provenance = QueryResponseProvenance.ProjectionBacked;
		obj.Lifecycle = (degraded ? ProjectionLifecycleState.Stale : queryResponseMetadata.Lifecycle);
		QueryResponseMetadata metadata = obj;
		return QueryResult.FromPayload(JsonSerializer.SerializeToElement(payload, s_jsonOptions), projectionType, metadata);
	}

	private ProjectionFreshnessMetadata ToPartiesFreshness(IReadModelFreshness model, DateTimeOffset now, bool degraded = false)
	{
		if (degraded)
		{
			return ProjectionFreshnessMetadata.Create(ProjectionFreshnessStatus.Stale, "projection-state-store-unavailable");
		}
		ProjectionFreshnessMetadata result;
		switch (ReadModelFreshness.Classify(model, Thresholds, now))
		{
		case ReadModelFreshnessState.Current:
		case ReadModelFreshnessState.Aging:
			result = ProjectionFreshnessMetadata.Create(ProjectionFreshnessStatus.Current);
			break;
		case ReadModelFreshnessState.Stale:
			result = ProjectionFreshnessMetadata.Create(ProjectionFreshnessStatus.Stale);
			break;
		default:
			result = ProjectionFreshnessMetadata.Create(ProjectionFreshnessStatus.Unavailable, "projection-state-unavailable");
			break;
		}
		return result;
	}

	private QueryPagingMetadata? CreatePagingMetadata(QueryEnvelope query, string cursorScope, int offset, int pageSize, int itemCount, int totalCount)
	{
		if ((object)query.Paging == null)
		{
			return null;
		}
		int num = checked(offset + itemCount);
		bool flag = num < totalCount;
		string text = (flag ? cursorCodec.Encode(query.QueryType, cursorScope, num.ToString(CultureInfo.InvariantCulture)) : null);
		if (text != null && text.Length > 4096)
		{
			text = cursorCodec.Encode(query.QueryType, CompactCursorScope(cursorScope), num.ToString(CultureInfo.InvariantCulture));
		}
		return new QueryPagingMetadata(pageSize, offset, text, totalCount, flag);
	}

	private bool TryResolvePaging(QueryEnvelope query, int payloadPage, int payloadPageSize, string cursorScope, out int page, out int pageSize, out int offset, out string failureReason)
	{
		failureReason = "invalid-cursor";
		page = payloadPage;
		pageSize = Math.Clamp(payloadPageSize, 1, 100);
		long num = (long)(page - 1) * (long)pageSize;
		offset = (int)((num > int.MaxValue) ? int.MaxValue : num);
		if ((object)query.Paging == null)
		{
			return true;
		}
		pageSize = query.Paging.PageSize ?? 20;
		offset = 0;
		int num2 = pageSize;
		if ((num2 < 1 || num2 > 100) ? true : false)
		{
			failureReason = "invalid-page";
			return false;
		}
		string failureReason2 = null;
		int? offset2 = query.Paging.Offset;
		if ((offset2.HasValue && offset2.GetValueOrDefault() < 0) || (!string.IsNullOrWhiteSpace(query.Paging.Cursor) && query.Paging.Offset.HasValue) || !TryDecodeCursor(query, cursorScope, out string position, out failureReason2))
		{
			if (!string.IsNullOrWhiteSpace(failureReason2))
			{
				LogCursorRejected(query.QueryType, failureReason2);
			}
			return false;
		}
		if (!string.IsNullOrWhiteSpace(position))
		{
			if (!int.TryParse(position, NumberStyles.None, CultureInfo.InvariantCulture, out offset) || offset < 0)
			{
				return false;
			}
		}
		else
		{
			offset2 = query.Paging.Offset;
			if (offset2.HasValue)
			{
				int valueOrDefault = offset2.GetValueOrDefault();
				offset = valueOrDefault;
			}
		}
		if (offset % pageSize != 0)
		{
			return false;
		}
		long num3 = (long)offset / (long)pageSize + 1;
		if (num3 > int.MaxValue)
		{
			return false;
		}
		page = (int)num3;
		return true;
	}

	private bool TryDecodeCursor(QueryEnvelope query, string cursorScope, out string? position, out string? failureReason)
	{
		if (cursorCodec.TryDecode(query.Paging.Cursor, query.QueryType, cursorScope, out position, out failureReason))
		{
			return true;
		}
		if (string.Equals(failureReason, "wrong-scope", StringComparison.Ordinal))
		{
			return cursorCodec.TryDecode(query.Paging.Cursor, query.QueryType, CompactCursorScope(cursorScope), out position, out failureReason);
		}
		return false;
	}

	private static string CompactCursorScope(string scope)
	{
		return "sha256:" + Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(scope)));
	}

	private static int ScopePageSize(QueryEnvelope query, int payloadPageSize)
	{
		if ((object)query.Paging != null)
		{
			return query.Paging.PageSize ?? 20;
		}
		return Math.Clamp(payloadPageSize, 1, 100);
	}

	private static string CreateListCursorScope(QueryEnvelope query, ListPartiesQueryPayload payload, int pageSize)
	{
		return QueryCursorScope.Create().Add("tenant", query.TenantId).Add("user", query.UserId)
			.Add("type", payload.Type?.ToString())
			.Add("active", payload.Active?.ToString(CultureInfo.InvariantCulture))
			.Add("created-after", payload.CreatedAfter)
			.Add("created-before", payload.CreatedBefore)
			.Add("modified-after", payload.ModifiedAfter)
			.Add("modified-before", payload.ModifiedBefore)
			.Add("page-size", pageSize.ToString(CultureInfo.InvariantCulture))
			.Build();
	}

	private static string CreateSearchCursorScope(QueryEnvelope query, SearchPartiesQueryPayload payload, int pageSize)
	{
		return QueryCursorScope.Create().Add("tenant", query.TenantId).Add("user", query.UserId)
			.Add("query", payload.Query.Trim())
			.Add("type", payload.Type?.ToString())
			.Add("active", payload.Active?.ToString(CultureInfo.InvariantCulture))
			.Add("mode", payload.Mode)
			.Add("case", payload.CaseId)
			.Add("page-size", pageSize.ToString(CultureInfo.InvariantCulture))
			.Build();
	}

	private static bool TryValidateDetailEnvelope(QueryEnvelope query, out string partyId)
	{
		partyId = (string.IsNullOrWhiteSpace(query.EntityId) ? query.AggregateId : query.EntityId);
		if (ValidTenantIdRegex().IsMatch(query.TenantId ?? string.Empty) && PartyIdentifier.IsValid(partyId))
		{
			return string.Equals(partyId, query.AggregateId, StringComparison.Ordinal);
		}
		return false;
	}

	private static bool TryValidateIndexEnvelope(QueryEnvelope query)
	{
		string a = (string.IsNullOrWhiteSpace(query.EntityId) ? query.AggregateId : query.EntityId);
		if (ValidTenantIdRegex().IsMatch(query.TenantId ?? string.Empty) && string.Equals(query.AggregateId, "parties", StringComparison.Ordinal))
		{
			return string.Equals(a, "parties", StringComparison.Ordinal);
		}
		return false;
	}

	[LoggerMessage(Level = LogLevel.Warning, Message = "Party SDK query {QueryType} failed with {ExceptionType}.")]
	[GeneratedCode("Microsoft.Extensions.Logging.Generators", "10.0.15.504")]
	private void LogQueryFailed(string? queryType, string exceptionType)
	{
		if (logger.IsEnabled(LogLevel.Warning))
		{
			__LogQueryFailedCallback(logger, queryType, exceptionType, null);
		}
	}

	[LoggerMessage(Level = LogLevel.Warning, Message = "Party processing read model unavailable with {ExceptionType}; returning empty degraded records.")]
	[GeneratedCode("Microsoft.Extensions.Logging.Generators", "10.0.15.504")]
	private void LogProcessingUnavailable(string exceptionType)
	{
		if (logger.IsEnabled(LogLevel.Warning))
		{
			__LogProcessingUnavailableCallback(logger, exceptionType, null);
		}
	}

	[LoggerMessage(Level = LogLevel.Debug, Message = "Party query cursor rejected for queryType {QueryType}: {FailureReason}.")]
	[GeneratedCode("Microsoft.Extensions.Logging.Generators", "10.0.15.504")]
	private void LogCursorRejected(string? queryType, string failureReason)
	{
		if (logger.IsEnabled(LogLevel.Debug))
		{
			__LogCursorRejectedCallback(logger, queryType, failureReason, null);
		}
	}
}
