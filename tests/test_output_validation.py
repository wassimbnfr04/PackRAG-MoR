from desktop.output_validation import validate_answer, identifier_admission

def test_buffered_display():
    assert validate_answer('74 °C [S1]', {'S1'}).display_text == '74 °C [S1]'
    for text in ['74 °C', '74 °C [S9]', '74 °C [S1]\n\nInvented fact', 'INSUFFICIENT_EVIDENCE [S1]</ANSWER>']:
        assert validate_answer(text, {'S1'}).display_text is None
    assert validate_answer('INSUFFICIENT_EVIDENCE', {'S1'}).status == 'INSUFFICIENT_EVIDENCE'

def test_identifier_is_not_answer_permission():
    assert identifier_admission(['a','b']) == 'AMBIGUOUS_IDENTIFIER'
    assert identifier_admission(['a']) == 'REQUIRES_FINAL_EVIDENCE_ADMISSION'
