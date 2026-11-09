"""Shared credential redaction for retained diagnostic and operator evidence."""
from __future__ import annotations

import html
import json
import os
import re
import xml.etree.ElementTree as ET

REDACTION_POLICY = 'mcpcli-evidence-redaction/v1'
_STRINGS = re.compile(r'"(?:[^"\\]|\\.)*"')
_PRIVATE = re.compile(r'(?:SigningKey|PrivateKey)\Z', re.I)
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


def _quoted_arguments(text, marker, *, protect_json=False):
    strings = [(match.start(), match.end()) for match in _STRINGS.finditer(text)] if protect_json else []
    pattern = r'''(?i)((?:SigningKey|PrivateKey)\s*[=:]\s*)(?P<quote>['"])(?P<value>.*?)(?P<close>(?P=quote)|\Z)'''
    def replace(match):
        if any(start <= match.start() < end for start, end in strings):
            return match[0]
        value = match['value']
        if value in _MARKERS or value == marker:
            return match[0]
        return match[1] + match['quote'] + marker + match['close']
    return re.sub(pattern, replace, text, flags=re.S)


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
    text = _quoted_arguments(text, marker)
    # Named arguments are accepted by the fixture hosts. Ordinary prose such as
    # "SigningKey is configured" must remain useful and byte-identical.
    text = re.sub(r'''(?i)((?:SigningKey|PrivateKey)\s*[=:]\s*)((?:\[REDACTED(?: PEM| JWT)?\]|<redacted>)(?=[\s,}\]]|\Z)|[^\s,"'}]+)''',
                  lambda match: match[0] if match[2] in _MARKERS or match[2] == marker
                  else match[1] + marker, text)
    return _known(text, secrets, marker)


def _xml_fallback(text, secrets, marker):
    """Conservatively redact raw XML fragments, including unfinished attributes."""
    attribute_pattern = r'''(?P<name>[\w:.-]+)\s*=\s*(?P<quote>['"])(?P<value>.*?)(?P<close>(?P=quote)|\Z)'''
    def selectors(attributes):
        return any(match['name'].rsplit(':', 1)[-1].lower() in ('name', 'key')
                   and private_key(html.unescape(match['value']))
                   for match in re.finditer(attribute_pattern, attributes, flags=re.S))
    def attributes(match):
        tag = match[0]
        private_setting = selectors(tag)
        def value(attribute):
            name, content = attribute['name'], html.unescape(attribute['value'])
            if private_key(name) or private_setting and name.rsplit(':', 1)[-1].lower() == 'value':
                redacted = content if content in _MARKERS or content == marker or not content else marker
            else:
                redacted = _scalar(content, secrets, marker)
            if redacted == content:
                return attribute[0]
            return name + '=' + attribute['quote'] + html.escape(redacted, quote=True) + attribute['close']
        return re.sub(attribute_pattern, value, tag, flags=re.S)
    redacted = re.sub(r'<[A-Za-z_][^>]*(?:>|\Z)', attributes, text)
    pattern = r'<(?P<tag>[\w:.-]*(?:SigningKey|PrivateKey))\b[^>]*(?<!/)>(?P<body>.*?)(?P<close></(?P=tag)\s*>|\Z)'
    def element(match):
        body = html.unescape(match['body'])
        if not body.strip() or body in _MARKERS or body == marker:
            return match[0]
        opening = match[0][:match.start('body') - match.start()]
        return opening + marker + match['close']
    redacted = re.sub(pattern, element, redacted, flags=re.I | re.S)
    # Select only private settings before matching their body; an unrelated
    # parent name attribute must not consume a nested private setting.
    setting_pattern = r'''<(?P<tag>[\w:.-]+)\b(?=[^>]*\b(?:name|key)\s*=\s*(?:"[^"<>]*(?:SigningKey|PrivateKey)"|'[^'<>]*(?:SigningKey|PrivateKey)'))(?P<attributes>[^>]*(?<!/))>(?P<body>.*?)(?P<close></(?P=tag)\s*>|\Z)'''
    def setting(match):
        body = html.unescape(match['body'])
        if not selectors(match['attributes']) or not body.strip() or body in _MARKERS or body == marker:
            return match[0]
        return '<' + match['tag'] + match['attributes'] + '>' + marker + match['close']
    redacted = re.sub(setting_pattern, setting, redacted, flags=re.S | re.I)
    # Decode each text node independently. Decoding quotes before recognizing
    # attributes would split an entity-encoded credential into false fields.
    parts = re.split(r'(<[^>]*(?:>|\Z))', redacted)
    for index in range(0, len(parts), 2):
        decoded = html.unescape(parts[index])
        value = _scalar(decoded, secrets, marker)
        if value != decoded:
            parts[index] = html.escape(value, quote=False)
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
    text = _quoted_arguments(text, marker, protect_json=True)
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
        separator = re.match(r'\s*:\s*', text[match.end():])
        if separator is None:
            continue
        start = match.end() + separator.end()
        try:
            value, end = decoder.raw_decode(text, start)
        except ValueError:
            # An unfinished private value is unsafe through the input boundary.
            value, end = None, len(text)
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
    # Logs may retain escaped JSON fragments without their outer string quotes.
    text = re.sub(r'(?i)((?P<quote>\\+)"[^"\r\n]*(?:SigningKey|PrivateKey)(?P=quote)"\s*:\s*)(?P=quote)"[^"\r\n]*(?P=quote)"',
                  lambda match: match[1] + match['quote'] + '"' + marker + match['quote'] + '"', text)
    # The decoded tokens above have already been sanitized. Process only raw
    # spans here: an unterminated XML/PEM diagnostic inside a JSON string must
    # never consume that string's closing quote or its safe siblings.
    parts, cursor = [], 0
    for match in _STRINGS.finditer(text):
        raw = text[cursor:match.start()]
        if '<' in raw or '&' in raw:
            raw = _xml_fallback(raw, secrets, marker)
        parts.extend((_scalar(raw, secrets, marker), match[0]))
        cursor = match.end()
    raw = text[cursor:]
    if '<' in raw or '&' in raw:
        raw = _xml_fallback(raw, secrets, marker)
    result = ''.join([*parts, _scalar(raw, secrets, marker)])
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
        return [sanitized_values(item, environment=environment, marker=marker) for item in value]
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
