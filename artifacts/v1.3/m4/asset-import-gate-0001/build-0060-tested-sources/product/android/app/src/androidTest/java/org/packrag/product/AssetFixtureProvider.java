package org.packrag.product;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.os.ParcelFileDescriptor;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.concurrent.atomic.AtomicInteger;

/** Instrumentation APK only. A separate UID serves one public pinned template. */
public final class AssetFixtureProvider extends ContentProvider {
    private final AtomicInteger opens=new AtomicInteger();
    private final AtomicInteger closes=new AtomicInteger();
    private final AtomicInteger closeErrors=new AtomicInteger();
    @Override public boolean onCreate(){return true;}
    private void allowed(Uri uri) {
        if(!"content".equals(uri.getScheme()) || !"org.packrag.product.test.asset-fixtures".equals(uri.getAuthority())
            || !"/template-valid".equals(uri.getPath()) || uri.getQuery()!=null || uri.getFragment()!=null)
            throw new IllegalArgumentException("Unknown fixture");
    }
    @Override public String getType(Uri uri){allowed(uri);return "application/octet-stream";}
    @Override public Cursor query(Uri uri,String[] projection,String selection,String[] arguments,String sort) {
        allowed(uri);MatrixCursor cursor=new MatrixCursor(new String[]{"opens","closes","close_errors","provider_uid"});
        cursor.addRow(new Object[]{opens.get(),closes.get(),closeErrors.get(),android.os.Process.myUid()});return cursor;
    }
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode) throws FileNotFoundException {
        allowed(uri);if(!"r".equals(mode)) throw new FileNotFoundException("Read only");
        try {
            File file=new File(getContext().getCacheDir(),"asset-template-valid.jinja");
            try(InputStream input=getContext().getAssets().open("asset-import-source/template-valid.jinja");FileOutputStream output=new FileOutputStream(file,false)) {
                byte[] buffer=new byte[8192];int size,total=0;
                while((size=input.read(buffer))!=-1){total+=size;if(total>5443) throw new IOException("Fixture bound");output.write(buffer,0,size);}
                if(total!=5443) throw new IOException("Fixture size");output.getFD().sync();
            }
            ParcelFileDescriptor descriptor=ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY,
                new Handler(Looper.getMainLooper()),error->{closes.incrementAndGet();if(error!=null)closeErrors.incrementAndGet();});
            opens.incrementAndGet();return descriptor;
        } catch(IOException failure){throw new FileNotFoundException("Fixture unavailable");}
    }
    @Override public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException();}
    @Override public int delete(Uri uri,String selection,String[] args){throw new UnsupportedOperationException();}
    @Override public int update(Uri uri,ContentValues values,String selection,String[] args){throw new UnsupportedOperationException();}
}
