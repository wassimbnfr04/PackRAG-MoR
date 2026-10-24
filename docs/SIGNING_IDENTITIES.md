# Three different signing identities

1. **APK signing:** the distributed development APK is signed with the original
   Android debug certificate, SHA256
   `66355628e741ed61960535e08c19ddbe6cb75c7983106c88c344ba04397f8c7c`.
   Its signature was verified before distribution. Gradle creates a local debug
   keystore for another developer's build. Android requires matching certificates
   for an in-place update; do not silently uninstall an existing app to work
   around a different signing key. No owner key is needed to build your own APK.
2. **Knowledge-pack publisher:** `release-trust.json` contains approved PUBLIC
   keys. The private publisher seed signs new packs, but is not needed to
   verify/import existing signed packs. The supplied repair pack works with the
   supplied APK. A new publisher generates its own local private key and
   explicitly approves its PUBLIC key in its app configuration. Existing
   `v13_publisher_setup` refuses silent rotation of an approved identity.
3. **Interop test fixture:** `tests/signature_vector/test_private_key` is a
   deliberately public non-secret test seed. It is neither the APK signing key
   nor the project publisher's private key. Its README says TEST KEY ONLY.

Private custody is not published to a public GitHub repository. It is not needed
to run the distributed app or signed repair pack. Final nondebug release signing
and rotation are separate from M4's development artifact.
