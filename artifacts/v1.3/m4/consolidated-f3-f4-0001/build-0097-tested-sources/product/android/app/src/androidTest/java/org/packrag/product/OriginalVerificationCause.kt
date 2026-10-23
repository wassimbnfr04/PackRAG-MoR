package org.packrag.product

import org.packrag.packs.PackImportRejected

/** Preserve the existing exact rejection-reason assertions beneath the new typed boundary. */
fun originalVerificationCause(error:Throwable):Throwable {
    var current=error
    while(current is PackImportRejected && current.cause!=null) current=requireNotNull(current.cause)
    return current
}
