package org.packrag.product

import java.util.concurrent.ExecutionException
import java.util.concurrent.FutureTask
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.asExecutor

/** Fixed I/O dispatcher bridge for the synchronous registry snapshot contract.
 * No coroutine suspends under that monitor. Tasks may access an ActivePack, never
 * call back into the caller's registry/session monitors. Await completion even if
 * interrupted: releasing the snapshot while its SQL task still runs is unsafe.
 */
object BlockingIo {
    private val executor=Dispatchers.IO.asExecutor()
    fun <T> run(action:()->T):T {
        val task=FutureTask<T> { action() };executor.execute(task)
        var interrupted=false
        try {
            while(true) {
                try { return task.get() }
                catch(failure:InterruptedException) { interrupted=true }
                catch(failure:ExecutionException) {
                    val cause=requireNotNull(failure.cause)
                    when(cause) { is RuntimeException -> throw cause;is Error -> throw cause
                        else -> throw IllegalStateException("I/O task failed",cause) }
                }
            }
        } finally { if(interrupted) Thread.currentThread().interrupt() }
    }
}
