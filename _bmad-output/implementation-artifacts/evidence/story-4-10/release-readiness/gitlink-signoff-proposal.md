# Pending root dependency selection for the Parties release

The actual release-candidate command `bash scripts/gitlink-rc-gate.sh --diff v1.5.0` exits **1** for these nine already committed pointer advances. The ledger requires an actual release-owner decision; no approval has been invented or entered. The complete reviewed Contracts candidate is separately approved.

The root graph committed at Parties `ea926163fb51033b226541f069ebf6a5941922af` remains unchanged in current candidate `df8173f04bd65cb86bc0d060dc75914e421f7640` ([Parties PR #56](https://github.com/Hexalith/Hexalith.Parties/pull/56)). Source selection does not certify upstream source CI or historical parity. Package-mode Release consumers continue to use their pinned published versions.

| Dependency | Previous release SHA | Proposed committed SHA | Describe |
| --- | --- | --- | --- |
| Hexalith.Builds | `332b2c144defba546fe0a09626a4a72f2340e22f` | `fff4a212180d8cd1c5c0759655a9bc4fb6963c45` | `v4.35.0` |
| Hexalith.Commons | `b7e6e7d5e28568b30c523130339cc4c52e12c674` | `5c23c818f639c5bb3175f964c5549440bd5b876d` | `v2.30.3` |
| Hexalith.EventStore | `d55c6f7c11e9bce6f17d490a84c83f1561979d63` | `54261aeccb1d8d8c5c99beb2437e2e8a5ad69eaa` | `v3.126.0-20-g54261aec` |
| Hexalith.FrontComposer | `1513fe3ed21a554eeee7a9d807f9b9e25fdb4cd2` | `913c4132c71cd7f77fcdf6befa9e396d284dd4bc` | `v4.7.0-16-g913c4132` |
| Hexalith.McpCli | `c25e2140e14a76b696a76aed30c8302107714fd6` | `9354dc08176744c75c2ddb61d924c0948b373b98` | `v1.0.0-32-g9354dc08` |
| Hexalith.Memories | `d0c5d8ca96b06e02acdda88f255b33288642a7f7` | `35df7e2080c369003cacac12f5b44117d7f3ed35` | `v2.29.5` |
| Hexalith.Platform | `5f18593639832d1245577dd93ec07687517d3acb` | `4f036ced45aa40700948c19949bb874881c960b5` | `4f036ced` |
| Hexalith.PolymorphicSerializations | `80ce5afd99216ce5f591d66c833feafaf371f171` | `221ac4592ba908ae7661ba1fa9e2d1fcc23baee0` | `v1.19.5` |
| Hexalith.Tenants | `c9feedb6656d70c7271e851c844ee29bdfb28c3e` | `3ae9db014dfe52bdee4f6731465cc2a7b65701b7` | `v5.9.0-26-g3ae9db01` |

[Machine-readable proposal](gitlink-signoff-proposal.json), [exact gate result](gitlink-rc-gate.json), and [upstream workflow observations](upstream-source-workflows.json) retain the input evidence. Several upstream source CI runs are failed or absent; no green source-qualification claim is made. The source pointers and compiled package versions are separate identities.

The blocking repository rule is in `RELEASE-CHECKLIST.md`: owner-validated means “the owner confirms the forward move ships”; the ledger owner/date fields must be real. Historical ledger approvals do not cover these new SHAs. The proposed decision concerns these exact pointers for this Parties release only, while all automated CI/publication gates stay in force.
