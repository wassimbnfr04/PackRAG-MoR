package org.packrag.product

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.*
import org.junit.Test

class BlockingIoTest {
    @Test fun fixedDispatcherRunsOutsideCallerMonitorAndReturnsExactValue() {
        val field=BlockingIo::class.java.getDeclaredField("executor");field.isAccessible=true
        // DispatcherExecutor exposes the actual target; physical thread names are not evidence.
        val executor=requireNotNull(field.get(BlockingIo))
        val dispatcher=executor.javaClass.getDeclaredField("dispatcher");dispatcher.isAccessible=true
        assertSame(Dispatchers.IO,dispatcher.get(executor))
        val caller=Thread.currentThread().id;val lock=Any()
        synchronized(lock) {
            val worker=BlockingIo.run { assertFalse(Thread.holdsLock(lock));Thread.currentThread().id }
            assertNotEquals(caller,worker)
            assertEquals("owned",BlockingIo.run { "owned" });assertNull(BlockingIo.run<String?> { null })
        }
    }
    @Test fun taskFailureKeepsOriginalRuntimeCause() {
        val failure=IllegalArgumentException("fixed failure")
        assertSame(failure,assertThrows(IllegalArgumentException::class.java) { BlockingIo.run { throw failure } })
        val fatal=AssertionError("fixed assertion")
        assertSame(fatal,assertThrows(AssertionError::class.java) { BlockingIo.run { throw fatal } })
    }
    @Test fun interruptedCallerWaitsForWorkerBeforeReleasingSnapshotAndRestoresFlag() {
        val entered=CountDownLatch(1);val release=CountDownLatch(1);val finished=CountDownLatch(1)
        val restored=AtomicBoolean();val result=AtomicReference<String>();val failure=AtomicReference<Throwable>()
        val caller=Thread {
            try { result.set(BlockingIo.run { entered.countDown();check(release.await(10,TimeUnit.SECONDS));"complete" })
                restored.set(Thread.currentThread().isInterrupted)
            } catch(problem:Throwable) { failure.set(problem) } finally { finished.countDown() }
        }
        caller.start()
        try {
            assertTrue(entered.await(10,TimeUnit.SECONDS));caller.interrupt()
            assertFalse("Caller returned before its I/O completed",finished.await(100,TimeUnit.MILLISECONDS))
        } finally { release.countDown();caller.join(10_000) }
        assertFalse(caller.isAlive);assertNull(failure.get());assertEquals("complete",result.get());assertTrue(restored.get())
    }
}
