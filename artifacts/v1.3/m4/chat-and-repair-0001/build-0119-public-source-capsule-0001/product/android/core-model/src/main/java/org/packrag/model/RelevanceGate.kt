package org.packrag.model

/** Ordered merged-pool gate; threshold provenance and calibration measurement are separate. */
data class RelevanceSignal(val exact:Boolean,val sparseRank:Int?,val denseRank:Int?,val denseScore:Double,
    val calibrated:Boolean,val agreedThreshold:Double?,val denseOnlyThreshold:Double?)

object RelevanceGate {
    fun mark(signals:List<RelevanceSignal>):List<Boolean> {
        val marked=signals.map { it.exact }.toMutableList()
        val top=signals.indexOfFirst { !it.exact }
        if(top>=0) {
            val item=signals[top]
            if(item.calibrated) {
                val agreed=requireNotNull(item.agreedThreshold)
                val dense=requireNotNull(item.denseOnlyThreshold)
                marked[top]=(item.sparseRank!=null && item.denseRank!=null && item.denseScore>=agreed) ||
                    (item.denseRank==1 && item.denseScore>=dense)
            }
        }
        return marked
    }
}
