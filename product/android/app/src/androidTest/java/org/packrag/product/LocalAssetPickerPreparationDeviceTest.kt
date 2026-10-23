package org.packrag.product

import android.content.Intent
import android.content.pm.PackageManager
import android.os.Process
import android.provider.DocumentsContract
import androidx.test.ext.junit.runners.AndroidJUnit4
import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Background preflight; no Activity, picker interaction, imports, generation or owner writes. */
@RunWith(AndroidJUnit4::class)
class LocalAssetPickerPreparationDeviceTest {
    @Test fun realSystemPickerResolvesAndUnselectedDocumentIsPermissionDenied() {
        val support=LocalAssetImportTestSupport;val context=support.context;val before=support.ownerGuard()
        val intent=Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("*/*")
        val target=context.packageManager.resolveActivity(intent,PackageManager.MATCH_DEFAULT_ONLY)?.activityInfo?.packageName
        val shell=support.documentPickerPackage();assertNotEquals(context.packageName,shell)
        val uri=DocumentsContract.buildDocumentUri("org.packrag.product.test.asset-documents","full-template")
        assertEquals(PackageManager.PERMISSION_DENIED,context.checkSelfPermission("android.permission.MANAGE_DOCUMENTS"))
        assertEquals(PackageManager.PERMISSION_DENIED,context.checkUriPermission(uri,Process.myPid(),Process.myUid(),Intent.FLAG_GRANT_READ_URI_PERMISSION))
        assertThrows(SecurityException::class.java){context.contentResolver.openFileDescriptor(uri,"r")?.close()}
        assertEquals(before,support.ownerGuard())
        File(context.filesDir,"m4-local-asset-picker-preparation.json").writeText(JSONObject().put("status","PASS").put("variant",BuildConfig.BUILD_TYPE)
            .put("target_picker_lookup",target ?: JSONObject.NULL).put("shell_picker_package",shell).put("unselected_document_read_denied",true)
            .put("product_has_manage_documents_permission",false).put("owner_registry_and_model_sha256",JSONObject(before)).put("guards_unchanged",true)
            .put("scope","Background permission/resolution preflight only; shell octet-stream lookup is explicit when target package visibility hides all-MIME resolver. Actual UI/package/window/grant/selection still required. No native, import, system picker interaction or full F2/M4 acceptance.").toString(2),Charsets.UTF_8)
    }
}
