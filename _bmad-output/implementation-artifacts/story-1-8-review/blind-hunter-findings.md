# Blind Hunter findings (untriaged)

Review snapshot: `/tmp/mcpcli-story-1-8-j1mkpjwq.diff`, 54,879 bytes.
Finding floor: `min(floor(sqrt(54,879 / 1,000) + 1), 10) = 8`.

- `validate.py:54–62`: A JSON integer containing 4,301 digits raises an uncaught `ValueError` from `json.loads`; deeply nested JSON can similarly raise `RecursionError`. Convert parser-limit failures into located validation findings so the reusable entry point and CLI retain their documented error behavior.
- `validate.py:34–38`: Nested duplicate fields always report the root location. A duplicate `a` inside `/invocation/payload/duplicate` produces `vector.json:/: duplicate JSON field 'a'`, losing the offending object's location. Preserve the nested path and add coverage beyond the root duplicate test.
- `schema.json:42`: `offset` has no upper bound, so `2147483648` passes validation even though `RunQueryArguments.Offset` and both Heads use `int?`. Add the supported maximum and boundary tests.
- `schema.json:41–42`: JSON Schema accepts `1.0` as an integer, and the validator approves `pageSize: 1.0`. The runner constructs `--page-size 1.0`, which cannot bind to the CLI integer option. Require a runnable representation or normalize integral numeric values consistently before execution.
- `validate.py:144–147`: Paging consistency uses Python equality, which treats booleans as integers. An envelope containing `pageSize: 1` and an expected request containing `paging: {pageSize: true}` receives no findings. Validate expected paging types or use JSON equality distinguishing booleans from numbers.
- `schema.json:43`: The cursor limit counts Unicode code points, while `OperationExecutor.ValidateQueryArguments` counts UTF-16 code units through C# `string.Length`. A cursor containing 3,000 emoji passes this validator but exceeds the executor's 4,096-unit limit.
- `schema.json:44` and `test_validate.py`: Extension validation checks value types and request equality but omits unconditional runtime restrictions. Matching envelope/request objects containing 33 extensions pass; key syntax, key/value lengths, and total UTF-8 size are also unchecked.
- `validate.py:121–147`: Request consistency is only checked when optional inputs are supplied. A command with no envelope extensions can expect invented extensions, and a query with no paging inputs can expect a page size; both pass although Core constructs these fields directly from the missing inputs.

These are reviewer claims awaiting the workflow's combined triage; they are not accepted defects or completion findings.
