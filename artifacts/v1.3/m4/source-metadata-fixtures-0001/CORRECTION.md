# Unaccepted draft fixture

Authenticated source-metadata loading passed, but this draft reused the prior
document vectors after changing the article header fields. The raw record
explicitly identifies that reuse. It is not faithful to the updated document
input recipe and is not eligible for C2a acceptance. No unit/build/phone gate
was run against it. Preserve these bytes; fresh0002 regenerates actual Granite
document vectors and replaces only the three unchanged uncommitted draft test
assets. The prior normalized query input is unchanged and its measured query
vector can be reused explicitly. This is a fixture preparation error, not a
model, importer or retrieval failure.
