"""Shared credential redaction for retained diagnostic and operator evidence."""
from __future__ import annotations

import html
import json
import os
import re
import xml.etree.ElementTree as ET

REDACTION_POLICY = 'mcpcli-evidence-redaction/v1'
_STRINGS = re.compile(r'(?<!\\)"(?:[^"\\]|\\.)*"')
_PRIVATE = re.compile(r'(?:SigningKey|PrivateKey)\Z', re.I)
_PRIVATE_OPTION = re.compile(r'--[\w:.-]*(?:SigningKey|PrivateKey)', re.I)
_ARGUMENT_PREFIX = re.compile(
    rf'(?:(?P<option>(?<![\w-]){_PRIVATE_OPTION.pattern})(?:\s*[=:]\s*|[ \t]+)'
    r'|(?:SigningKey|PrivateKey)\s*[=:]\s*)', re.I)
_QUOTED_WORD = r'''(?P<quote>['"])(?:\\[\s\S]|(?!(?P=quote))[^\\])*(?P<close>(?P=quote)|\\?\Z)'''
_FIRST_QUOTED = re.compile(_QUOTED_WORD)
_MARKER_WORD = r'(?:\[REDACTED(?: PEM| JWT)?\]|<redacted>)(?=[\s,}\]]|\Z)'
_ARGUMENT_WORD = re.compile(rf'''{_MARKER_WORD}|(?:{_QUOTED_WORD}|\\(?:[\s\S]|\Z)|[^\s,"'}}\\])+''')
_ASSIGNMENT_WORD = re.compile(rf'''{_MARKER_WORD}|{_QUOTED_WORD}|[^\s,"'}}]+''')
_JSON_FIELD_SEPARATOR = re.compile(r'\s*:\s*')
_ARGV_SEPARATOR = re.compile(r'\s*,\s*')
_ARGV_VALUE_END = re.compile(r'\s*(?:,|\]|\Z)')
_ESCAPED_FIELD = re.compile(
    r'''(?<!\\)(?P<escape>\\+)"[^"\r\n]*?(?P=escape)"(?P<separator>\s*:\s*)''')
_XML_TAG = re.compile(
    r'''(?P<opaque><!--.*?(?:-->|\Z)|<!\[CDATA\[.*?(?:\]\]>|\Z)|<\?.*?(?:\?>|\Z))|'''
    r'''<(?P<closing>/)?(?P<name>[A-Za-z_][\w:.-]*)(?P<attributes>'''
    r'''(?:[^<>"']|"[^"]*(?:"|\Z)|'[^']*(?:'|\Z))*)(?P<end>>|(?=<|\Z))''', re.S)
_XML_ATTRIBUTE = re.compile(
    r'''(?P<name>[\w:.-]+)\s*=\s*(?P<quote>['"])(?P<value>.*?)(?:(?P=quote)|\Z)''', re.S)
_ENVIRONMENT = re.compile(r'TOKEN|PASSWORD|SECRET|CERT_KEY|SIGNINGKEY|PRIVATE_?KEY|API_KEY', re.I)
_PEM = re.compile(r'-----BEGIN (?P<kind>[^\r\n-]+)-----.*?(?:-----END (?P=kind)-----|\Z)', re.S)
_JWT = re.compile(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+')
_BEARER = re.compile(r'\bBearer\s+[A-Za-z0-9._~+/-]+=*', re.I)
_MARKERS = {'[REDACTED]', '[REDACTED PEM]', '[REDACTED JWT]', '<redacted>'}


def private_key(key):
    """Identify the supported named private settings, including qualified names."""
    return isinstance(key, str) and _PRIVATE.search(key) is not None


def known_credentials(environment=None):
    """Return known credential values; an explicit empty mapping disables ambient input."""
    environment = os.environ if environment is None else environment
    return {value for key, value in environment.items() if isinstance(value, str) and value.strip()
            and _ENVIRONMENT.search(key)}


def _arguments(text, marker, *, protect_json=False):
    tokens = _STRINGS.finditer(text) if protect_json else iter(())
    protected = next(tokens, None)
    parts, cursor = [], 0
    for prefix in _ARGUMENT_PREFIX.finditer(text):
        start = prefix.start()
        while protected is not None and protected.end() <= start:
            protected = next(tokens, None)
        if start < cursor or protected is not None and protected.start() <= start:
            continue
        # Shell logs can quote the entire option, including the separator.
        if prefix['option'] and start and text[start - 1] == "'":
            outer = _FIRST_QUOTED.match(text, start - 1)
            if outer is not None and prefix.end() < outer.start('close'):
                value = text[prefix.end():outer.start('close')]
                if value not in _MARKERS and value != marker:
                    parts.extend((text[cursor:prefix.end()], marker))
                    cursor = outer.start('close')
                continue
        pattern = _ARGUMENT_WORD if prefix['option'] else _ASSIGNMENT_WORD
        word = pattern.match(text, prefix.end())
        if word is None or word[0] in _MARKERS or word[0] == marker:
            continue
        quoted = _FIRST_QUOTED.match(word[0])
        if quoted:
            closing_quote = quoted['quote'] if quoted['close'] == quoted['quote'] else ''
            content = quoted[0][1:quoted.start('close')]
            if quoted.end() == len(word[0]) and quoted['close'] == closing_quote and (
                content in _MARKERS or content == marker
            ):
                continue
            replacement = quoted['quote'] + marker + closing_quote
        else:
            replacement = marker
        parts.extend((text[cursor:word.start()], replacement))
        cursor = word.end()
    return ''.join([*parts, text[cursor:]])


def _known(text, secrets, marker):
    # Match once so a shorter known credential cannot rewrite a marker just
    # inserted for a longer value in the same pass.
    if not secrets:
        return text
    alternatives = [r'\[REDACTED(?: PEM| JWT)?\]|<redacted>', re.escape(marker),
                    *(re.escape(value) for value in sorted(secrets, key=lambda item: (-len(item), item)))]
    return re.sub('|'.join(alternatives), lambda match: match[0] if match[0] in _MARKERS
                  or match[0] == marker else marker, text)


def _scalar(text, secrets, marker):
    pem_marker = '[REDACTED PEM]' if marker == '[REDACTED]' else marker
    jwt_marker = '[REDACTED JWT]' if marker == '[REDACTED]' else marker
    text = _PEM.sub(pem_marker, text)
    text = _JWT.sub(jwt_marker, text)
    text = _BEARER.sub('Bearer ' + marker, text)
    # Named arguments are accepted by the fixture hosts. Ordinary prose such as
    # "SigningKey is configured" must remain useful and byte-identical.
    return _known(_arguments(text, marker), secrets, marker)


def _escaped_json_end(text, start, token, decoder):
    quote = re.escape(token)
    # The token's backslashes are the escape-layer delimiter. Each literal
    # backslash in a JSON string contributes a pair at the underlying layer.
    encoded_pair = re.escape('\\' * (2 * len(token)))
    delimiter = rf'(?<!\\)(?:{encoded_pair})*{quote}'
    if text.startswith(token, start):
        closing = re.compile(delimiter).search(text, start + len(token))
        return closing.end() if closing else None
    if text[start:start + 1] in ('{', '['):
        depth, in_string = 0, False
        structure = re.compile(rf'(?P<quote>{delimiter})|[{{}}\[\]]')
        for piece in structure.finditer(text, start):
            if piece['quote']:
                in_string = not in_string
            elif not in_string:
                depth += 1 if piece[0] in '{[' else -1
                if depth == 0:
                    return piece.end()
        return None
    try:
        return decoder.raw_decode(text, start)[1]
    except ValueError:
        return None


def _escaped_json(text, marker, decoder):
    parts, cursor = [], 0
    for field in _ESCAPED_FIELD.finditer(text):
        if field.start() < cursor:
            continue
        encoded_key = text[field.start():field.start('separator')]
        try:
            while encoded_key.startswith('\\'):
                encoded_key = json.loads('"' + encoded_key + '"')
            key = json.loads(encoded_key)
        except ValueError:
            continue
        if not private_key(key):
            continue
        quote = field['escape'] + '"'
        start = field.end()
        end = _escaped_json_end(text, start, quote, decoder)
        close = '' if end is None and text.startswith(quote, start) else quote
        replacement = quote + marker + close
        if end is None:
            end = len(text)
        original = text[start:end]
        if original in {quote + item + close for item in _MARKERS} or original == replacement:
            continue
        parts.extend((text[cursor:start], replacement))
        cursor = end
    return ''.join([*parts, text[cursor:]])


def _xml_fallback(text, secrets, marker):
    """Conservatively redact raw XML fragments, including unfinished attributes."""
    def text_node(raw):
        decoded = html.unescape(raw)
        redacted = _scalar(decoded, secrets, marker)
        return raw if redacted == decoded else html.escape(redacted, quote=False)

    def private_body(raw):
        decoded = html.unescape(raw)
        return raw if not decoded.strip() or decoded in _MARKERS or decoded == marker else marker

    parts, cursor = [], 0
    private_tag, private_depth = None, 0
    for tag in _XML_TAG.finditer(text):
        if tag['opaque']:
            if private_tag is None:
                parts.extend((text_node(text[cursor:tag.start()]), _scalar(tag[0], secrets, marker)))
                cursor = tag.end()
            continue
        name = tag['name'].casefold()
        attributes = tag['attributes']
        self_closing = attributes.rstrip().endswith('/')
        if private_tag is not None:
            if tag['end'] and name == private_tag:
                if tag['closing']:
                    private_depth -= 1
                elif not self_closing:
                    private_depth += 1
            if private_depth == 0:
                parts.extend((private_body(text[cursor:tag.start()]), tag[0]))
                cursor, private_tag = tag.end(), None
            continue

        parts.append(text_node(text[cursor:tag.start()]))
        private_setting = any(attribute['name'].rsplit(':', 1)[-1].lower() in ('name', 'key')
                              and private_key(html.unescape(attribute['value']))
                              for attribute in _XML_ATTRIBUTE.finditer(attributes))

        def redact_attribute(attribute):
            content = html.unescape(attribute['value'])
            name = attribute['name']
            if private_key(name) or private_setting and name.rsplit(':', 1)[-1].lower() == 'value':
                redacted = content if not content or content in _MARKERS or content == marker else marker
            else:
                redacted = _scalar(content, secrets, marker)
            if redacted == content:
                return attribute[0]
            start = attribute.start('value') - attribute.start()
            end = attribute.end('value') - attribute.start()
            return attribute[0][:start] + html.escape(redacted, quote=True) + attribute[0][end:]

        prefix = text[tag.start():tag.start('attributes')]
        parts.extend((prefix, _XML_ATTRIBUTE.sub(redact_attribute, attributes), tag['end']))
        cursor = tag.end()
        if tag['end'] and not tag['closing'] and not self_closing and (private_key(name) or private_setting):
            private_tag, private_depth = name, 1

    remainder = text[cursor:]
    parts.append(private_body(remainder) if private_tag is not None else text_node(remainder))
    return ''.join(parts)


def _text(text, secrets, marker, depth=0):
    if depth > 40:
        # Deeply nested diagnostics are not useful enough to retain ambiguously.
        return marker
    strings = [(match.start(), match.end()) for match in _STRINGS.finditer(text)]
    pem_marker = '[REDACTED PEM]' if marker == '[REDACTED]' else marker
    text = _PEM.sub(lambda match: match[0] if any(start <= match.start() < end for start, end in strings)
                    else pem_marker, text)
    strings = [(match.start(), match.end()) for match in _STRINGS.finditer(text)]
    # XML fragments can follow quoted log prefixes. Protect only '<' signs
    # contained inside JSON tokens; those are handled after string decoding.
    for match in re.finditer('<', text):
        if not any(start <= match.start() < end for start, end in strings):
            text = text[:match.start()] + _xml_fallback(text[match.start():], secrets, marker)
            break
    text = _arguments(text, marker, protect_json=True)
    decoder = json.JSONDecoder()
    parts, cursor = [], 0
    # Redact raw spans, rather than parsing a whole object and losing duplicate
    # fields. This also replaces private objects and arrays in their entirety.
    for match in _STRINGS.finditer(text):
        if match.start() < cursor:
            continue
        try:
            key = json.loads(match[0])
        except ValueError:
            continue
        if not private_key(key):
            continue
        separator = _JSON_FIELD_SEPARATOR.match(text, match.end())
        argv = separator is None and bool(_PRIVATE_OPTION.fullmatch(key))
        if argv and text[:match.start()].rstrip().endswith(('[', ',')):
            separator = _ARGV_SEPARATOR.match(text, match.end())
        if separator is None:
            continue
        start = separator.end()
        if argv and text[start:start + 1] != '"':
            continue
        try:
            value, end = decoder.raw_decode(text, start)
        except ValueError:
            # An unfinished private value is unsafe through the input boundary.
            value, end = None, len(text)
        if argv and not _ARGV_VALUE_END.match(text, end):
            continue
        if isinstance(value, str) and (value in _MARKERS or value == marker):
            continue
        parts.extend((text[cursor:start], json.dumps(marker)))
        cursor = end
    text = ''.join([*parts, text[cursor:]])
    def string(match):
        try:
            decoded = json.loads(match[0])
        except ValueError:
            return match[0]
        redacted = _text(decoded, secrets, marker, depth + 1)
        return json.dumps(redacted, ensure_ascii=False) if redacted != decoded else match[0]
    text = _STRINGS.sub(string, text)

    def raw_span(raw):
        # Logs may retain escaped JSON fragments without their outer string quotes.
        raw = _escaped_json(raw, marker, decoder)
        if '<' in raw or '&' in raw:
            raw = _xml_fallback(raw, secrets, marker)
        return _scalar(raw, secrets, marker)

    # The decoded tokens above have already been sanitized. Process only raw
    # spans here: an unterminated XML/PEM diagnostic inside a JSON string must
    # never consume that string's closing quote or its safe siblings.
    parts, cursor = [], 0
    for match in _STRINGS.finditer(text):
        parts.extend((raw_span(text[cursor:match.start()]), match[0]))
        cursor = match.end()
    result = ''.join([*parts, raw_span(text[cursor:])])
    try:
        json.loads(result)
    except ValueError:
        # Plain logs can contain a known value spanning quoted snippets. Run
        # this after syntactic redaction so a short known credential cannot
        # erase the Bearer/private-setting labels before their values are found.
        return _known(result, secrets, marker)
    # Valid JSON tokens were decoded and sanitized above; replacing raw syntax
    # here could mistake a quote in a known credential for a JSON delimiter.
    return result


def sanitized(text: str, *, environment=None, marker='[REDACTED]') -> str:
    """Redact credentials while retaining safe JSON strings and duplicate fields."""
    return _text(text, known_credentials(environment), marker)


def sanitized_values(value, *, environment=None, marker='[REDACTED]'):
    """Redact decoded operator evidence, including named private containers."""
    if isinstance(value, dict):
        return {sanitized_values(key, environment=environment, marker=marker):
                item if isinstance(item, str) and (item in _MARKERS or item == marker)
                else marker if private_key(key) else sanitized_values(item, environment=environment, marker=marker)
                for key, item in value.items()}
    if isinstance(value, list):
        result = []
        private_argument = False
        for item in value:
            if private_argument and isinstance(item, str):
                result.append(item if item in _MARKERS or item == marker else marker)
                private_argument = False
            else:
                result.append(sanitized_values(item, environment=environment, marker=marker))
                private_argument = isinstance(item, str) and bool(_PRIVATE_OPTION.fullmatch(item))
        return result
    if not isinstance(value, str):
        return value
    return sanitized(value, environment=environment, marker=marker)


def sanitized_xml(text: str, *, environment=None, marker='[REDACTED]') -> str:
    """Redact decoded XML values, preserving the exact original bytes when safe."""
    secrets = known_credentials(environment)
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return _text(text, secrets, marker)
    changed = False
    for element in root.iter():
        private_setting = any(private_key(value) for key, value in element.attrib.items()
                              if key.rsplit('}', 1)[-1].lower() in ('name', 'key'))
        if (private_key(element.tag) or private_setting) and ((element.text and element.text.strip()) or len(element)):
            if element.text not in _MARKERS and element.text != marker or len(element):
                element.text = marker
                for child in list(element):
                    element.remove(child)
                changed = True
        for field in ('text', 'tail'):
            value = getattr(element, field)
            if value is not None:
                redacted = _text(value, secrets, marker)
                if redacted != value:
                    setattr(element, field, redacted)
                    changed = True
        for key, value in list(element.attrib.items()):
            redacted = (value if not value or value in _MARKERS or value == marker else marker) \
                if private_key(key) or private_setting and key.rsplit('}', 1)[-1].lower() == 'value' \
                else _text(value, secrets, marker)
            if redacted != value:
                element.set(key, redacted)
                changed = True
    return _text(ET.tostring(root, encoding='unicode') if changed else text, secrets, marker)
