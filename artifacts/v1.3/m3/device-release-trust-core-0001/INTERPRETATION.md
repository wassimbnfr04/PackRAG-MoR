# Preserved selection-preflight failure

The selected class RegistryProcessDeathTest was a mistyped name. Its actual source class is RegistryProcessDeathDeviceTest. The frozen-build selection preflight rejected the absent class before any ADB install or instrumentation command; the saved commands array is empty. This attempt remains FAIL and contains no phone test result.

device-release-trust-core-0002 uses the corrected selection with the unchanged build0013 APKs. This was an orchestration input repair, with no Android source or fixture change.
