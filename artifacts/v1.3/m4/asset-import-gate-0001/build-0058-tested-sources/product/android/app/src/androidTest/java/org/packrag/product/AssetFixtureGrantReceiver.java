package org.packrag.product;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;

/** Shell/DUMP protected explicit test-only grant. No permission is added to the product. */
public final class AssetFixtureGrantReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context,Intent intent) {
        if(!"org.packrag.product.test.GRANT_TEMPLATE".equals(intent.getAction())){setResultCode(2);return;}
        context.grantUriPermission("org.packrag.product",Uri.parse("content://org.packrag.product.test.asset-fixtures/template-valid"),Intent.FLAG_GRANT_READ_URI_PERMISSION);
        setResultCode(1);setResultData("NARROW_TEMPLATE_READ_GRANTED");
    }
}
