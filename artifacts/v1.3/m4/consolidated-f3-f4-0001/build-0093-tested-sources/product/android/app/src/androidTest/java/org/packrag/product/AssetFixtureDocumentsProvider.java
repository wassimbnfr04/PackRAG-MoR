package org.packrag.product;

import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.Binder;
import android.os.CancellationSignal;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
import android.provider.DocumentsProvider;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicInteger;
import org.json.JSONObject;

/** Test APK only: actual system-picker grants. MANAGE_DOCUMENTS protects every document. */
public final class AssetFixtureDocumentsProvider extends DocumentsProvider {
    private static final String AUTHORITY="org.packrag.product.test.asset-documents";
    private static final String[] IDS={"full-template","corrupt","blocked-pipe","signed-kpack","invalid-kpack"};
    private final AtomicInteger opens=new AtomicInteger();
    private static final String[] ROOT_COLUMNS={DocumentsContract.Root.COLUMN_ROOT_ID,DocumentsContract.Root.COLUMN_DOCUMENT_ID,
        DocumentsContract.Root.COLUMN_TITLE,DocumentsContract.Root.COLUMN_SUMMARY,DocumentsContract.Root.COLUMN_FLAGS,
        DocumentsContract.Root.COLUMN_MIME_TYPES,DocumentsContract.Root.COLUMN_AVAILABLE_BYTES};
    private static final String[] DOC_COLUMNS={DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_MIME_TYPE,
        DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_FLAGS,DocumentsContract.Document.COLUMN_SIZE};
    @Override public boolean onCreate(){return true;}
    private void admitted(String id) throws FileNotFoundException {if(!Arrays.asList(IDS).contains(id))throw new FileNotFoundException("Unknown test document");}
    @Override public Cursor queryRoots(String[] projection) {
        MatrixCursor cursor=new MatrixCursor(projection==null?ROOT_COLUMNS:projection);MatrixCursor.RowBuilder row=cursor.newRow();
        for(String column:cursor.getColumnNames()) {
            Object value=null;
            if(DocumentsContract.Root.COLUMN_ROOT_ID.equals(column))value="packrag-test-root";
            else if(DocumentsContract.Root.COLUMN_DOCUMENT_ID.equals(column))value="root";
            else if(DocumentsContract.Root.COLUMN_TITLE.equals(column))value="PackRAG test assets";
            else if(DocumentsContract.Root.COLUMN_SUMMARY.equals(column))value="Isolated instrumentation fixtures";
            else if(DocumentsContract.Root.COLUMN_FLAGS.equals(column))value=DocumentsContract.Root.FLAG_LOCAL_ONLY;
            else if(DocumentsContract.Root.COLUMN_MIME_TYPES.equals(column))value="*/*";
            else if(DocumentsContract.Root.COLUMN_AVAILABLE_BYTES.equals(column))value=0L;
            row.add(value);
        };return cursor;
    }
    private void row(MatrixCursor cursor,String id) {
        MatrixCursor.RowBuilder row=cursor.newRow();String label="root".equals(id)?"PackRAG test assets":
            "full-template".equals(id)?"Official template.jinja":"corrupt".equals(id)?"Corrupt template.jinja":
            "signed-kpack".equals(id)?"Signed synthetic test pack.kpack":"invalid-kpack".equals(id)?"Invalid synthetic test pack.kpack":"Slow template.jinja";
        for(String column:cursor.getColumnNames()) {
            Object value=null;
            if(DocumentsContract.Document.COLUMN_DOCUMENT_ID.equals(column))value=id;
            else if(DocumentsContract.Document.COLUMN_DISPLAY_NAME.equals(column))value=label;
            else if(DocumentsContract.Document.COLUMN_MIME_TYPE.equals(column))value="root".equals(id)?DocumentsContract.Document.MIME_TYPE_DIR:"application/octet-stream";
            else if(DocumentsContract.Document.COLUMN_FLAGS.equals(column))value=0;
            else if(DocumentsContract.Document.COLUMN_SIZE.equals(column) && !"root".equals(id))value="invalid-kpack".equals(id)?3L:"signed-kpack".equals(id)?signedLength():5443L;
            row.add(value);
        }
    }
    @Override public Cursor queryDocument(String id,String[] projection) throws FileNotFoundException {
        if(!"root".equals(id))admitted(id);MatrixCursor cursor=new MatrixCursor(projection==null?DOC_COLUMNS:projection);row(cursor,id);return cursor;
    }
    @Override public Cursor queryChildDocuments(String parent,String[] projection,String order) throws FileNotFoundException {
        if(!"root".equals(parent))throw new FileNotFoundException("Unknown parent");MatrixCursor cursor=new MatrixCursor(projection==null?DOC_COLUMNS:projection);
        for(String id:IDS)row(cursor,id);return cursor;
    }
    @Override public boolean isChildDocument(String parent,String child){return "root".equals(parent) && Arrays.asList(IDS).contains(child);}
    private long signedLength() {
        try(java.io.InputStream input=getContext().getAssets().open("release-trust-corpus/calibration-schema-only.kpack")) {
            byte[] buffer=new byte[65536];long total=0;int count;while((count=input.read(buffer))>=0)total+=count;return total;
        } catch(IOException error){return -1L;}
    }
    private synchronized ParcelFileDescriptor packDescriptor(String id) throws FileNotFoundException {
        File file=new File(getContext().getCacheDir(),"f3-saf-"+id+".kpack");
        try {
            if(java.nio.file.Files.isSymbolicLink(file.toPath()) || (file.exists() && !file.isFile()))throw new IOException("Invalid owned cache type");
            if(!file.exists()) { if(!file.createNewFile())throw new IOException("Owned cache creation failed");
            try(java.io.FileOutputStream output=new java.io.FileOutputStream(file)) {
                if("signed-kpack".equals(id)) {
                    try(java.io.InputStream source=getContext().getAssets().open("release-trust-corpus/calibration-schema-only.kpack")) { byte[] buffer=new byte[65536];int count;while((count=source.read(buffer))>=0)output.write(buffer,0,count); }
                } else output.write(new byte[]{1,2,3});
                output.getFD().sync();
            }
            }
            if(file.length()!=("signed-kpack".equals(id)?signedLength():3L))throw new IOException("Owned cached fixture size changed");
            return ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY);
        } catch(IOException error){throw new FileNotFoundException("Owned synthetic pack document unavailable");}
    }
    @Override public ParcelFileDescriptor openDocument(String id,String mode,CancellationSignal signal) throws FileNotFoundException {
        admitted(id);if(!"r".equals(mode))throw new FileNotFoundException("Read only");int caller=Binder.getCallingUid();
        // The selected document is a closed test whitelist. Its backing fixture belongs to this
        // provider UID; clear the incoming identity only for that same-UID descriptor delegation.
        long identity=Binder.clearCallingIdentity();
        try {
            ParcelFileDescriptor descriptor=("signed-kpack".equals(id) || "invalid-kpack".equals(id))?packDescriptor(id):
                getContext().getContentResolver().openFileDescriptor(Uri.parse("content://org.packrag.product.test.asset-fixtures/"+id),"r",signal);
            if(descriptor==null)throw new FileNotFoundException("Test document unavailable");
            try {
                JSONObject audit=new JSONObject().put("opens",opens.incrementAndGet()).put("last_document_id",id).put("calling_uid",caller)
                    .put("provider_uid",android.os.Process.myUid()).put("document_uri",DocumentsContract.buildDocumentUri(AUTHORITY,id).toString());
                File file=new File(getContext().getFilesDir(),"f2-document-open-audit.json");
                try(java.io.FileOutputStream output=new java.io.FileOutputStream(file)){output.write(audit.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));output.getFD().sync();}
            }catch(Exception failure){try{descriptor.close();}catch(IOException ignored){}throw new FileNotFoundException("Test audit unavailable");}
            return descriptor;
        } finally {Binder.restoreCallingIdentity(identity);}
    }
}
