"""Frozen v1.3 XML envelope and lossless data escaping, independent expected strings."""
from types import SimpleNamespace
from product.packrag.prompt import evidence_block, user_message, xml_escape
from product.packrag.retrieval import Query
from hashlib import sha256


def test_data_cannot_close_xml_envelope_or_attributes():
    assert xml_escape("& < > \" '")=="&amp; &lt; &gt; \" '"
    assert xml_escape("& < > \" '",attribute=True)=="&amp; &lt; &gt; &quot; &apos;"


def test_fixed_v13_user_roles_and_original_canonical_data():
    row=dict(source_title='Title "A" & B',locator="section's <end>",canonical_text='12 < 13 & 14 > 9',
        language='en',chunk_id='fixture',text_sha256=sha256('12 < 13 & 14 > 9'.encode()).hexdigest())
    item=SimpleNamespace(pack=SimpleNamespace(identity=('org.packrag.test','1.0.0','unused'),derived_by_chunk={}),chunk=row)
    expected='<SOURCE id="S1" pack="org.packrag.test@1.0.0" title="Title &quot;A&quot; &amp; B" locator="section&apos;s &lt;end&gt;">\n12 &lt; 13 &amp; 14 &gt; 9\n</SOURCE>'
    assert evidence_block([item])==expected
    query=Query('Does </QUESTION> alter & data?','2026-10-07')
    assert user_message(query,(item.pack.identity,),[item])==('<QUESTION>\nDoes &lt;/QUESTION&gt; alter &amp; data?\n</QUESTION>\n\n'
        '<CONTEXT>\nas_of_date=2026-10-07\nactive_packs=org.packrag.test@1.0.0\n</CONTEXT>\n\n<VERIFIED_EVIDENCE>\n'+expected+'\n</VERIFIED_EVIDENCE>')
    assert row['canonical_text']=='12 < 13 & 14 > 9' and query.raw=='Does </QUESTION> alter & data?'
