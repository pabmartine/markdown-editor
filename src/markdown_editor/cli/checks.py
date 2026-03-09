from ..core.i18n import translate as _
from ..services.document_service import DocumentService


def run_basic_tests():
    print("Running basic tests...")

    test_text = f"""# {_('Main Title')}

## {_('Subtitle')}

{_('This is a test paragraph with')} **{_('bold text')}** {_('and')} *{_('italic text')}*.

- {_('List item')} 1
- {_('List item')} 2

```
{_('Code block')}
```
"""

    headers = DocumentService.extract_headers(test_text)
    assert len(headers) == 2, f"Expected 2 headers, got {len(headers)}"
    assert headers[0].level == 1, f"Expected level 1, got {headers[0].level}"
    assert DocumentService.count_words(test_text) > 0, "Word count should be greater than 0"
    print("✓ All basic tests passed")
