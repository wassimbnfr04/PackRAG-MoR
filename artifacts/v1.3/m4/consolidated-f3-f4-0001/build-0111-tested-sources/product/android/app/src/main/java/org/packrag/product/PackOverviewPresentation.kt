package org.packrag.product

import org.packrag.model.PackIdentity
import org.packrag.model.PackOverview
import org.packrag.model.ownedList

fun authenticatedOverview(row:PackRow):PackOverview?=row.overview?.takeIf { it.identity==row.identity }

fun activePackIdentities(rows:List<PackRow>):List<PackIdentity> = ownedList(rows.filter { it.active }.map { it.identity })

fun packOverviewLines(row:PackRow,deviceDate:String):List<String> {
    val overview=authenticatedOverview(row) ?: return listOf("Metadata unavailable: installed content could not be reverified. Open details to retry.")
    val due=PackFreshness(overview.identity,overview.updateCheckAfter).advisoryAt(deviceDate)
    return listOf("Name: ${overview.name}","Publisher: ${overview.publisherName}","Publisher public key ID: ${overview.publisherKeyId}",
        "Version: ${overview.identity.version}","Manifest SHA256: ${overview.identity.manifestSha256}",
        "Update check due: ${overview.updateCheckAfter} · device date: $deviceDate · ${if(due) "advisory due; evidence remains subject to normal validation" else "not due"}",
        "Manifest bytes (signed JSON): ${overview.manifestBytes}","Payload bytes (uncompressed): ${overview.payloadBytes}",
        "Transport bytes (KPack archive): ${overview.transportBytes}")
}

fun packVerificationLabel(row:PackRow):String {
    val activity=if(row.active) "Active" else "Inactive"
    return "$activity · ${if(authenticatedOverview(row)!=null) "freshly verified metadata" else "metadata verification unavailable"}"
}

fun storedPackTrustLabel(trust:String):String=when(trust) {
    "VERIFIED"->"Stored install trust: verified; activation always rechecks content."
    "UNTRUSTED"->"Stored install trust: previously failed verification; activation rechecks content."
    else->"Stored install trust: unavailable."
}
