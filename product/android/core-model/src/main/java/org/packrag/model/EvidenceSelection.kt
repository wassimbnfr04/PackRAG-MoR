package org.packrag.model

data class SelectionValue(val priority:Int,val rrf:Double,val exact:Int,val cosine:Double)
data class SelectionItem(val key:String,val position:Int,val canonical:Pair<String,String>,val source:String,
    val value:SelectionValue,val redundancy:String,val required:List<Pair<String,String>> = emptyList(),val resolved:Boolean=true)
data class SelectionDecision(val key:String,val reason:String,val trial:List<String> = emptyList(),val representative:String?=null,
    val evidenceTokens:Int?=null,val prefillTokens:Int?=null)
data class SelectionPlan(val keys:List<String>,val decisions:List<SelectionDecision>,val sources:List<String>,val admission:String="READY")
fun ownedSelection(value:SelectionPlan)=value.copy(keys=ownedList(value.keys),sources=ownedList(value.sources),
    decisions=ownedList(value.decisions.map { it.copy(trial=ownedList(it.trial)) }))
class SelectionFailure(val state:String,val selection:SelectionPlan?=null):IllegalArgumentException(state)

/** No retrieval, score synthesis, semantic equivalence or additive token estimates. */
object EvidenceSelection {
    fun select(input:List<SelectionItem>,chunkCap:Int,evidenceCap:Int,prefillCap:Int,
               measure:(List<String>)->Pair<Int,Int>):SelectionPlan {
        if(minOf(chunkCap,evidenceCap,prefillCap)<=0) throw SelectionFailure("INVALID_SELECTION_CAPS")
        val byKey=linkedMapOf<String,SelectionItem>()
        val positions=mutableSetOf<Int>()
        for(item in input) {
            if(item.position<1 || item.key.isEmpty() || item.source.isEmpty()) throw SelectionFailure("INVALID_SELECTION_POOL")
            val prior=byKey[item.key]
            if(prior!=null) {
                if(prior!=item) throw SelectionFailure("INVALID_SELECTION_POOL")
                continue
            }
            if(!positions.add(item.position)) throw SelectionFailure("INVALID_SELECTION_POOL")
            byKey[item.key]=item
        }
        val ordered=byKey.values.sortedBy { it.position }
        val canonical=linkedMapOf<Pair<String,String>,String>()
        for(item in ordered) canonical.putIfAbsent(item.canonical,item.key)
        val protected=ordered.flatMap { it.required }.toSet()
        val mandatory=ordered.filter { it.required.isNotEmpty() || it.canonical in protected }.map { it.key }.toSet()
        val selected=mutableSetOf<String>()
        val decisions=mutableMapOf<String,SelectionDecision>()
        fun trialKeys(keys:Set<String>)=ordered.filter { it.key in keys }.map { it.key }
        fun fail(state:String,key:String,reason:String,trial:List<String> = emptyList(),cost:Pair<Int,Int>?=null):Nothing {
            decisions[key]=SelectionDecision(key,reason,trial,evidenceTokens=cost?.first,prefillTokens=cost?.second)
            val values=ordered.map { decisions[it.key] ?: SelectionDecision(it.key,"NOT_CONSIDERED_AFTER_REJECTION") }
            throw SelectionFailure(state,ownedSelection(SelectionPlan(emptyList(),values,emptyList(),state)))
        }
        fun bundle(root:SelectionItem):Set<String> {
            val pending=mutableListOf(root.key)
            val result=mutableSetOf<String>()
            while(pending.isNotEmpty()) {
                val key=pending.removeAt(pending.lastIndex)
                if(!result.add(key)) continue
                val item=byKey.getValue(key)
                if(!item.resolved) fail("LEGAL_CONFLICT_UNRESOLVED",key,"UNRESOLVED_CONFLICT",trialKeys(result+selected))
                for(pair in item.required) pending.add(canonical[pair] ?: fail("INCOMPLETE_LEGAL_CONFLICT_EVIDENCE",key,"MISSING_REQUIRED_MEMBER",trialKeys(result+selected)))
            }
            return result
        }
        var cursor=0
        while(cursor<ordered.size) {
            val group=mutableListOf(ordered[cursor++])
            while(cursor<ordered.size && group[0].key !in mandatory && ordered[cursor].key !in mandatory
                  && ordered[cursor].value==group[0].value) group.add(ordered[cursor++])
            while(group.isNotEmpty()) {
                val sources=selected.map { byKey.getValue(it).source }.toSet()
                val root=group.minWith(compareBy<SelectionItem> { it.source in sources }.thenBy { it.position })
                group.remove(root)
                if(root.key in selected) {
                    decisions.putIfAbsent(root.key,SelectionDecision(root.key,"REQUIRED_COMPANION",trialKeys(selected)))
                    continue
                }
                if(root.key !in mandatory) {
                    val duplicate=ordered.firstOrNull { it.key in selected && it.key !in mandatory
                        && it.canonical==root.canonical && it.source==root.source && it.redundancy==root.redundancy }
                    if(duplicate!=null) {
                        decisions[root.key]=SelectionDecision(root.key,"LITERAL_DUPLICATE",representative=duplicate.key)
                        continue
                    }
                }
                val members=bundle(root)
                val trial=trialKeys(selected+members)
                if(trial.size>chunkCap) {
                    if(members.any { it in mandatory }) fail("INCOMPLETE_LEGAL_CONFLICT_EVIDENCE",root.key,"MANDATORY_CHUNK_CAP",trial)
                    decisions[root.key]=SelectionDecision(root.key,"CHUNK_CAP",trial)
                    continue
                }
                val (evidence,prefill)=measure(trial)
                if(minOf(evidence,prefill)<0) throw SelectionFailure("INVALID_SELECTION_COST")
                if(evidence>evidenceCap || prefill>prefillCap) {
                    if(members.any { it in mandatory }) fail("INCOMPLETE_LEGAL_CONFLICT_EVIDENCE",root.key,"MANDATORY_TOKEN_CAP",trial,evidence to prefill)
                    decisions[root.key]=SelectionDecision(root.key,"TOKEN_CAP",trial,evidenceTokens=evidence,prefillTokens=prefill)
                    continue
                }
                for(key in members-selected) decisions[key]=SelectionDecision(key,if(key==root.key) "SELECTED" else "REQUIRED_COMPANION",trial,evidenceTokens=evidence,prefillTokens=prefill)
                selected.addAll(members)
            }
        }
        return ownedSelection(SelectionPlan(trialKeys(selected),ordered.map { decisions.getValue(it.key) },selected.map { byKey.getValue(it).source }.distinct().sorted()))
    }
}
