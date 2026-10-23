# Preserved build-selection failure

The first demo build requested testReleaseUnitTest. AGP9 defaults android.onlyEnableUnitTestForTheTestedBuildType to true, so this project did not expose that task under the existing configuration. Gradle stopped at task selection before code compilation, test execution or device installation. This build remains FAIL.

The repair sets android.onlyEnableUnitTestForTheTestedBuildType=false to generate debug and release unit-test components, following the official AGP behavior documentation: https://developer.android.com/build/releases/agp-9-0-0-release-notes . Build0015 is the new corrected demo attempt. This changes test-component availability; it does not change generator weights, template, native commit, thermal configuration or production runtime policy.
