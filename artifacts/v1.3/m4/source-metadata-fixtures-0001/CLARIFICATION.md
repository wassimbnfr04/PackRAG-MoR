# Heading-policy clarification

The first correction assumed that changing article metadata necessarily changed
the previous embedding input. The helper actually takes title, section/article
heading, contextual prefix and canonical text; the pinned profile says
section_or_article. Keeping a nonempty section would permit unchanged old
vectors under an explicit section-first policy. The draft had not specified
that choice, so calling it an established recipe defect was too strong.

It remains unaccepted preparation, with no build/phone acceptance against it.
Fresh0003 deliberately uses nonempty article else section and an empty contextual
prefix, saves exact embedding-inputs.json, and computes actual new Granite
vectors for those inputs. Fresh0002 failed because the regeneration accidentally
passed nullable article into the contextual-prefix argument; no final pack or
new test assets were produced there. Neither issue concerns the verified C1
implementation, model quality or importer security. Both earlier records and
the first correction remain unchanged so the reasoning history is reviewable.
