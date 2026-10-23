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
import android.os.Bundle;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.channels.FileChannel;
import java.nio.ByteBuffer;
import java.nio.file.StandardOpenOption;
import java.nio.charset.StandardCharsets;

/** Instrumentation APK only. Separate UID; fixed public template/fault fixtures and owned real assets. */
public final class AssetFixtureProvider extends ContentProvider {
    private final AtomicInteger opens=new AtomicInteger();
    private final AtomicInteger closes=new AtomicInteger();
    private final AtomicInteger closeErrors=new AtomicInteger();
    private final AtomicInteger openingAttempts=new AtomicInteger();
    private final AtomicInteger openingCancelled=new AtomicInteger();
    private final AtomicInteger pipeClosed=new AtomicInteger();
    private final AtomicInteger typedCancellable=new AtomicInteger();
    private final AtomicInteger typedPlain=new AtomicInteger();
    private final AtomicInteger pipeOpens=new AtomicInteger();
    static final String[] GRANTED={"template-valid","empty","truncated","oversized","corrupt","read-error","metadata-lie","short-pipe","blocked-pipe","opening-blocked"};
    static final String[] FULL_ASSETS={"full-generator","full-template","full-tokenizer","full-encoder"};
    private final Set<String> fixtures=new HashSet<>(Arrays.asList(GRANTED));
    @Override public boolean onCreate(){return true;}
    private void allowed(Uri uri) {
        if(!"content".equals(uri.getScheme()) || !"org.packrag.product.test.asset-fixtures".equals(uri.getAuthority())
            || uri.getPath()==null || (!fixtures.contains(uri.getPath().substring(1)) && !Arrays.asList(FULL_ASSETS).contains(uri.getPath().substring(1)) && !"/no-grant".equals(uri.getPath())) || uri.getQuery()!=null || uri.getFragment()!=null)
            throw new IllegalArgumentException("Unknown fixture");
    }
    @Override public String getType(Uri uri){allowed(uri);return "application/octet-stream";}
    @Override public Cursor query(Uri uri,String[] projection,String selection,String[] arguments,String sort) {
        allowed(uri);MatrixCursor cursor=new MatrixCursor(new String[]{"opens","closes","close_errors","provider_uid","opening_attempts","opening_cancelled","pipe_writers_closed","typed_cancellable_opens","typed_plain_opens","pipe_opens","_display_name","_size"});
        cursor.addRow(new Object[]{opens.get(),closes.get(),closeErrors.get(),android.os.Process.myUid(),openingAttempts.get(),openingCancelled.get(),pipeClosed.get(),typedCancellable.get(),typedPlain.get(),pipeOpens.get(),"../../untrusted.gguf",Long.MAX_VALUE});return cursor;
    }
    @Override public AssetFileDescriptor openTypedAssetFile(Uri uri,String filter,Bundle opts,CancellationSignal signal) throws FileNotFoundException {
        typedCancellable.incrementAndGet();
        if(!"*/*".equals(filter) && !"application/octet-stream".equals(filter))throw new FileNotFoundException("Unsupported fixture type");
        return openAssetFile(uri,"r",signal);
    }
    @Override public AssetFileDescriptor openTypedAssetFile(Uri uri,String filter,Bundle opts) throws FileNotFoundException {
        typedPlain.incrementAndGet();return openAssetFile(uri,"r",null);
    }
    @Override public AssetFileDescriptor openAssetFile(Uri uri,String mode) throws FileNotFoundException {return openAssetFile(uri,mode,null);}
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
                                // Leave the reader blocked between writes; a closed read end
                                // is detected by the next bounded write, even after open-time
                                // CancellationSignal's remote transport has been detached.
                                android.os.SystemClock.sleep(500);
                                if(signal!=null && signal.isCanceled())break;
                            } else {
                                android.os.SystemClock.sleep(10);
                            }
                        }
                    }catch(IOException ignored){}finally{pipeClosed.incrementAndGet();}
                },"test-asset-pipe").start();opens.incrementAndGet();pipeOpens.incrementAndGet();
                return new AssetFileDescriptor(pipe[0],0,AssetFileDescriptor.UNKNOWN_LENGTH);
            }catch(IOException failure){throw new FileNotFoundException("Pipe unavailable");}
        }
        return new AssetFileDescriptor(openFile(uri,mode),0,AssetFileDescriptor.UNKNOWN_LENGTH);
    }
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode) throws FileNotFoundException {
        allowed(uri);if(!"r".equals(mode)) throw new FileNotFoundException("Read only");
        String kind=uri.getLastPathSegment();if("read-error".equals(kind))throw new FileNotFoundException("Untrusted private provider error detail");
        try {
            if(Arrays.asList(FULL_ASSETS).contains(kind)) {
                File root=new File(getContext().getFilesDir(),"f2-full-assets-0001");
                BasicFileAttributes rootAttrs=Files.readAttributes(root.toPath(),BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
                if(!rootAttrs.isDirectory() || rootAttrs.isSymbolicLink() || !root.getCanonicalFile().getParentFile().equals(getContext().getFilesDir().getCanonicalFile()))throw new IOException("Unsafe source root");
                File marker=new File(root,"owner.marker");byte[] magic="PackRAG F2 full assets v1\n".getBytes(StandardCharsets.US_ASCII);
                BasicFileAttributes markerAttrs=Files.readAttributes(marker.toPath(),BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
                if(!markerAttrs.isRegularFile() || markerAttrs.isSymbolicLink() || markerAttrs.size()!=magic.length)throw new IOException("Source not owned");
                ByteBuffer buffer=ByteBuffer.allocate(magic.length+1);
                try(FileChannel channel=FileChannel.open(marker.toPath(),StandardOpenOption.READ,LinkOption.NOFOLLOW_LINKS)){while(buffer.hasRemaining() && channel.read(buffer)!=-1){}}
                if(buffer.position()!=magic.length || !Arrays.equals(Arrays.copyOf(buffer.array(),magic.length),magic))throw new IOException("Source marker mismatch");
                int index=Arrays.asList(FULL_ASSETS).indexOf(kind);
                long[] sizes={1593894944L,5443L,25301672L,390004608L};
                File file=new File(root,kind+".asset");
                BasicFileAttributes attrs=Files.readAttributes(file.toPath(),BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);
                if(!attrs.isRegularFile() || attrs.isSymbolicLink() || attrs.size()!=sizes[index])throw new IOException("Source size/path mismatch");
                ParcelFileDescriptor descriptor=ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY,
                    new Handler(Looper.getMainLooper()),error->{closes.incrementAndGet();if(error!=null)closeErrors.incrementAndGet();});
                opens.incrementAndGet();return descriptor;
            }
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
