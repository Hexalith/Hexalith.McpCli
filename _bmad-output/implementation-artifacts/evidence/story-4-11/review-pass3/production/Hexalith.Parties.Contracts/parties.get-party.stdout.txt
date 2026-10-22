{
  "name": "parties.get-party",
  "kind": "read",
  "description": "Read an existing party\u0027s detail in the envelope tenant. Missing and erased parties return the same safe not-found result; inactive parties remain visible.",
  "schema": {
    "type": [
      "object",
      "null"
    ],
    "properties": {
      "PartyId": {
        "type": "string",
        "description": "The supplied PartyId, at most 128 characters; tenant comes from the envelope. Use ASCII letters or digits plus \u0027.\u0027, \u0027_\u0027 or \u0027-\u0027; start and end with an ASCII letter or digit. McpCli refuses legacy braced, parenthesized and X-format GUID IDs before submission, although Parties accepts them."
      }
    },
    "required": [
      "PartyId"
    ],
    "additionalProperties": false
  },
  "example": {
    "PartyId": "party-49"
  },
  "envelope": {
    "aggregateIdRequired": false,
    "idempotencyKeyRequired": false,
    "arguments": [
      "tenant",
      "aggregateId",
      "entityId",
      "pageSize",
      "offset",
      "cursor"
    ]
  },
  "lintFindings": [],
  "submittable": false,
  "reason": "configuration_invalid"
}
