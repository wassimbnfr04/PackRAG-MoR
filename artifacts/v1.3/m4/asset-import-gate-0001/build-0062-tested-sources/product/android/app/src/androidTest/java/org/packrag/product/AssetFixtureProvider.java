package org.packrag.product;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.res.AssetFileDescriptor;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.os.ParcelFileDescriptor;
import android.os.CancellationSignal;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/** Instrumentation APK only. A separate UID serves one public pinned template. */
public final class AssetFixtureProvider extends ContentProvider {
    private final AtomicInteger opens=new AtomicInteger();
    private final AtomicInteger closes=new AtomicInteger();
    private final AtomicInteger closeErrors=new AtomicInteger();
    private final AtomicInteger openingAttempts=new AtomicInteger();
    private final AtomicInteger openingCancelled=new AtomicInteger();
    private final AtomicInteger pipeClosed=new AtomicInteger();
    static final String[] GRANTED={"template-valid","empty","truncated","oversized","corrupt","read-error","metadata-lie","short-pipe","blocked-pipe","opening-blocked"};
    private final Set<String> fixtures=new HashSet<>(Arrays.asList(GRANTED));
    @Override public boolean onCreate(){return true;}
    private void allowed(Uri uri) {
        if(!"content".equals(uri.getScheme()) || !"org.packrag.product.test.asset-fixtures".equals(uri.getAuthority())
            || uri.getPath()==null || (!fixtures.contains(uri.getPath().substring(1)) && !"/no-grant".equals(uri.getPath())) || uri.getQuery()!=null || uri.getFragment()!=null)
            throw new IllegalArgumentException("Unknown fixture");
    }
    @Override public String getType(Uri uri){allowed(uri);return "application/octet-stream";}
    @Override public Cursor query(Uri uri,String[] projection,String selection,String[] arguments,String sort) {
        allowed(uri);MatrixCursor cursor=new MatrixCursor(new String[]{"opens","closes","close_errors","provider_uid","opening_attempts","opening_cancelled","pipe_writers_closed","_display_name","_size"});
        cursor.addRow(new Object[]{opens.get(),closes.get(),closeErrors.get(),android.os.Process.myUid(),openingAttempts.get(),openingCancelled.get(),pipeClosed.get(),"../../untrusted.gguf",Long.MAX_VALUE});return cursor;
    }
    private byte[] template() throws IOException {
        try(InputStream input=getContext().getAssets().open("asset-import-source/template-valid.jinja")) {
            byte[] bytes=new byte[5443];int offset=0,size;
            while(offset<bytes.length && (size=input.read(bytes,offset,bytes.length-offset))!=-1){if(size==0)throw new IOException("Zero fixture read");offset+=size;}
            if(offset!=5443 || input.read()!=-1)throw new IOException("Fixture size");return bytes;
        }
    }
    @Override public AssetFileDescriptor openAssetFile(Uri uri,String mode,CancellationSignal signal) throws FileNotFoundException {
        allowed(uri);if(!"r".equals(mode))throw new FileNotFoundException("Read only");
        String kind=uri.getLastPathSegment();
        if("opening-blocked".equals(kind)) {
            openingAttempts.incrementAndGet();
            if(signal==null)throw new FileNotFoundException("Cancellation required");
            signal.setOnCancelListener(()->openingCancelled.incrementAndGet());
            long end=android.os.SystemClock.elapsedRealtime()+30000;
            while(!signal.isCanceled() && android.os.SystemClock.elapsedRealtime()<end)android.os.SystemClock.sleep(20);
            signal.throwIfCanceled();throw new FileNotFoundException("Opening fixture timed out");
        }
        if("short-pipe".equals(kind) || "blocked-pipe".equals(kind)) {
            try {
                byte[] bytes=template();ParcelFileDescriptor[] pipe=ParcelFileDescriptor.createReliablePipe();
                if(signal!=null)signal.setOnCancelListener(()->{try{pipe[1].close();}catch(IOException ignored){}});
                new Thread(()->{
                    try(ParcelFileDescriptor.AutoCloseOutputStream output=new ParcelFileDescriptor.AutoCloseOutputStream(pipe[1])) {
                        for(int offset=0;offset<bytes.length;offset+=128) {
                            output.write(bytes,offset,Math.min(128,bytes.length-offset));output.flush();
                            if("blocked-pipe".equals(kind)) {
                                long end=android.os.SystemClock.elapsedRealtime()+30000;
                                while((signal==null || !signal.isCanceled()) && android.os.SystemClock.elapsedRealtime()<end)android.os.SystemClock.sleep(20);
                                break;
                            }
                            android.os.SystemClock.sleep(10);
                        }
                    }catch(IOException ignored){}finally{pipeClosed.incrementAndGet();}
                },"test-asset-pipe").start();opens.incrementAndGet();
                return new AssetFileDescriptor(pipe[0],0,AssetFileDescriptor.UNKNOWN_LENGTH);
            }catch(IOException failure){throw new FileNotFoundException("Pipe unavailable");}
        }
        return super.openAssetFile(uri,mode,signal);
    }
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode) throws FileNotFoundException {
        allowed(uri);if(!"r".equals(mode)) throw new FileNotFoundException("Read only");
        String kind=uri.getLastPathSegment();if("read-error".equals(kind))throw new FileNotFoundException("Untrusted private provider error detail");
        try {
            byte[] bytes=template();
            if("empty".equals(kind))bytes=new byte[0];
            else if("truncated".equals(kind))bytes=Arrays.copyOf(bytes,5442);
            else if("oversized".equals(kind))bytes=Arrays.copyOf(bytes,5444);
            else if("corrupt".equals(kind))bytes[100]^=1;
            File file=new File(getContext().getCacheDir(),"asset-"+kind+".fixture");
            try(FileOutputStream output=new FileOutputStream(file,false)) {
                output.write(bytes);output.getFD().sync();
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
