package org.packrag.product;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;

/** Shell/DUMP protected explicit test-only grant. No permission is added to the product. */
public final class AssetFixtureGrantReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context,Intent intent) {
        if("org.packrag.product.test.GRANT_FULL_ASSETS".equals(intent.getAction())) {
            for(String name:AssetFixtureProvider.FULL_ASSETS)context.grantUriPermission("org.packrag.product",Uri.parse("content://org.packrag.product.test.asset-fixtures/"+name),Intent.FLAG_GRANT_READ_URI_PERMISSION);
            setResultCode(1);setResultData("NARROW_FULL_ASSET_READS_GRANTED");return;
        }
        if("org.packrag.product.test.GRANT_CASES".equals(intent.getAction()) || "org.packrag.product.test.REVOKE_CASES".equals(intent.getAction())) {
            boolean revoke="org.packrag.product.test.REVOKE_CASES".equals(intent.getAction());
            for(String name:AssetFixtureProvider.GRANTED) {
                Uri uri=Uri.parse("content://org.packrag.product.test.asset-fixtures/"+name);
                if(revoke)context.revokeUriPermission("org.packrag.product",uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);
                else context.grantUriPermission("org.packrag.product",uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);
            }
            setResultCode(1);setResultData(revoke?"FIXTURE_READS_REVOKED":"NARROW_FIXTURE_READS_GRANTED");return;
        }
        if(!"org.packrag.product.test.GRANT_TEMPLATE".equals(intent.getAction())){setResultCode(2);return;}
        context.grantUriPermission("org.packrag.product",Uri.parse("content://org.packrag.product.test.asset-fixtures/template-valid"),Intent.FLAG_GRANT_READ_URI_PERMISSION);
        setResultCode(1);setResultData("NARROW_TEMPLATE_READ_GRANTED");
    }
}
