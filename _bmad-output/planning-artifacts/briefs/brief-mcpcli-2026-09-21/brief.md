---
title: "Product Brief: Hexalith MCP Server & CLI"
status: ready-for-review
created: 2026-09-21
updated: 2026-09-21
---

# Product Brief: Hexalith MCP Server & CLI

## Executive Summary

The goal is for a human to do any operation in Hexalith through an LLM agent. This module gets there by replacing six handwritten, per-module MCP servers with one generic MCP server and one CLI, both driven by a single catalog of commands and queries.

Hexalith is a modular CQRS platform in which every business action is a command, every read is a query, and all of them travel through one EventStore gateway. A domain module declares an operation once, in its Contracts library, with a small attribute that the MCP module provides. The server discovers those declarations, describes them to the agent, validates each incoming payload, and submits it through the EventStore gateway client. It depends on nothing else in Hexalith and knows nothing about module internals.

Version one covers Tenants, Parties, Projects, and Folders. The six existing servers are end of life and are deleted as the generic one covers them.

## The Problem

**Inconsistency is the cost.** An LLM working across Hexalith sees six different products where there should be one. Each per-module server has its own transport, tool-naming scheme, description mechanism, and authentication story, and none can tell an agent what any other module can do. An agent that learns one module's conventions gains nothing for the next. Prompts, tool selection, and error handling have to be tuned per module, and every divergence is a place for the model to guess wrong. The specifics of each server are in the addendum under "Prior art".

**Descriptions are invisible.** Operation descriptions live in XML doc comments, which do not exist at runtime, so each server redescribes its operations by hand and each drifts from the code.

**This is an anticipatory build.** There is no triggering incident. The bet is that Hexalith's own Agents, ChatBot, and Conversations modules will soon need to act on business data across modules, and that six dialects will not survive that contact. Maintenance of six servers and friction for the next module author are real costs too, but they follow from the same root cause and disappear with it.

## The Solution

One module, three deliverables.

**An attribute package** that domain modules reference from their Contracts library. Two attributes mark a record as a command or a query and carry what the agent needs but the contract cannot express: a description, whether the operation reads or writes, and an optional example. Routing data comes from the existing contract interfaces, with attribute fallbacks for modules that do not implement them. The package has no dependencies and stays that way.

**A catalog** built at startup from the Contracts assemblies the server references. It knows every module, every operation, the JSON schema of each payload, and whether the operation is a read or a write. The same catalog drives both heads below.

**Two heads on one body.** An MCP server exposing five generic tools: list modules, list operations for a module, describe an operation with its schema and example, send a command, run a query. A CLI with the matching verbs, plus a `serve` verb that starts the MCP server. Both validate the payload against the schema, fill the message envelope with a fresh message ID and idempotency key, and submit through the EventStore gateway client.

Version one runs over stdio, configured by a connection profile or environment variables, so Claude Code, Claude Desktop, and VS Code can use it locally against a dev or test EventStore.

## Who This Serves

**The developer or agent operator, first.** Someone with a dev or test EventStore and an MCP-capable agent. They install one .NET tool, point a profile at the gateway, and their agent can list, describe, and run every decorated operation in the four covered modules. Success for them is a working cross-module task with no per-module setup.

**Hexalith's own agents, next.** Agents, ChatBot, and Conversations gain one way to act on business data instead of one integration per module.

**Module authors, indirectly.** Their obligation shrinks to decorating records in their Contracts library. In exchange, their module is visible to every agent on the day it ships, and they never write an MCP server again.

## Success Criteria

Checked three months after version one ships.

- Tenants, Parties, Projects, and Folders are fully exposed with zero module-specific code in this repository. Adding a fifth module is a package reference and a rebuild.
- An agent completes a task that spans at least two modules using only the five generic tools, with no per-module prompting or handwritten tool.
- At least one legacy per-module MCP server has been deleted, and no new one has been created since this brief was accepted.
- Every operation in the four modules carries a description that a person who has never seen the code can understand. A schema that validates is not enough.
- The CLI produces the same catalog and the same results as the MCP server, so a shell script and an agent cannot disagree about what Hexalith can do.

## Scope

**In for version one.** The attribute package. The catalog builder. The five generic MCP tools and matching CLI verbs described above, over stdio, with JSON on stdout, logs on stderr, and connection profiles borrowed from the existing admin CLI. Coverage of Tenants, Parties, Projects, and Folders. A written rule, placed in the Hexalith agent instructions, that no new per-module MCP server is created.

**Next release, already decided.** HTTP transport in the same binary, forwarding the caller's bearer token, tenant header, and user header, as Parties does today. No new authentication server. Deletion of legacy MCP servers as each is covered.

**Out of version one, and refused if proposed for it.** Plugin loading of Contracts assemblies from a folder. Typed one-tool-per-operation exposure. Generated per-operation CLI subcommands. Any OAuth or identity server. Event stream reading. MCP resources or prompts. Any reference to an aggregate, projection, handler, or server-side project from another module. These are parked, not rejected forever, and several are the obvious follow-ups once the catalog is stable.

**Guardrails that hold in every release.** The only Hexalith dependencies are the EventStore client package and the Contracts libraries being exposed. The tenant is supplied by the envelope, from a profile, a flag, or a forwarded header, and never by the payload. Identifiers are ULIDs and are never validated as GUIDs. Commands and queries are distinguishable in the catalog, so a read-only mode is one filter away.

## Vision

In two years, an agent is a peer of the Hexalith user interface: anything a person can do through a screen, they can do by asking. Two consequences follow now.

The human's own identity has to be the one acting and the one in the audit trail, so identity forwarding over HTTP is in the second release, not a nice-to-have. And a command without a description is a command an agent cannot use, so the attribute stops being decoration and becomes part of what it means for a Hexalith operation to exist. Every module that ships after this brief ships agent-ready or is not finished.
