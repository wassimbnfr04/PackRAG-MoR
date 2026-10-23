package org.packrag.model

/** Inputs are already eligible authenticated retrieval hits, never graph-expanded rows. */
data class ConflictNode(val key:String,val original:String,val text:String,val domain:String,
    val publisherKey:String,val jurisdiction:String?,val canonicalUri:String?,val article:String?,
    val authority:Int?,val order:Int) {
    val canonical:Pair<String,String> get()=original to text
}
data class ConflictEdge(val source:String,val target:String,val kind:String,val provenance:String,val confidence:Double)
data class ConflictDecision(val members:List<String>,val state:String,val reason:String,val preferred:String?,
    val retained:List<String>,val required:List<Pair<String,String>>) {
    val resolved:Boolean get()=state!="UNRESOLVED"
}

object Conflicts {
    private val legalTypes=setOf("amends","supersedes","exception_to")
    fun resolve(nodes:List<ConflictNode>,edges:List<ConflictEdge>):List<ConflictDecision> {
        val ordered=nodes.sortedWith(compareBy<ConflictNode> { it.order }.thenBy { it.key })
        val byKey=ordered.associateBy { it.key };require(byKey.size==nodes.size) { "Duplicate conflict node" }
        val parent=ordered.associate { it.key to it.key }.toMutableMap()
        fun root(value:String):String {
            var key=value
            while(parent.getValue(key)!=key) { parent[key]=parent.getValue(parent.getValue(key));key=parent.getValue(key) }
            return key
        }
        fun join(a:String,b:String) {
            val x=root(a);val y=root(b)
            if(x!=y) parent[maxOf(x,y)]=minOf(x,y)
        }
        val scopes=mutableMapOf<Triple<String,String,String>,String>()
        for(node in ordered) {
            val article=node.article?.let(::normalizeQuery) ?: ""
            if(node.domain=="law" && node.jurisdiction!=null && !node.canonicalUri.isNullOrEmpty() && article.isNotEmpty()) {
                val scope=Triple(node.jurisdiction,node.canonicalUri,article)
                val previous=scopes[scope]
                if(previous!=null) join(node.key,previous) else scopes[scope]=node.key
            }
        }
        val legal=edges.filter { edge ->
            val a=byKey[edge.source];val b=byKey[edge.target]
            edge.kind in legalTypes && a!=null && b!=null && a.domain=="law" && b.domain=="law" &&
                a.jurisdiction!=null && a.jurisdiction==b.jurisdiction
        }
        legal.forEach { join(it.source,it.target) }
        val groups=ordered.groupBy { root(it.key) }
        val decisions=mutableListOf<ConflictDecision>()
        val canonicalOrder=compareBy<Pair<String,String>> { it.first }.thenBy { it.second }
        for(members in groups.values) {
            val keys=members.map { it.key }
            val links=legal.filter { it.source in keys && it.target in keys }
            if(members.size<2 && links.isEmpty()) continue
            if(members.map { it.original }.distinct().size==1 && links.isEmpty()) continue
            fun unresolved(reason:String)=ConflictDecision(keys,"UNRESOLVED",reason,null,keys,emptyList())
            if(links.isEmpty() && members.map { it.text }.distinct().size==1) {
                decisions+=ConflictDecision(keys,"EQUIVALENT","SAME_PROVISION_EXACT_TEXT",keys.first(),keys,emptyList());continue
            }
            if(links.any { it.confidence!=1.0 || it.provenance !in setOf("explicit-reference","curated") }) {
                decisions+=unresolved("RELATION_NOT_FULL_PUBLISHER_ASSERTION");continue
            }
            if(members.any { it.authority==null }) { decisions+=unresolved("UNKNOWN_AUTHORITY");continue }
            if(members.map { it.publisherKey }.distinct().size!=1) { decisions+=unresolved("INCOMPARABLE_CURATORS");continue }
            if(members.groupBy { it.original }.values.any { edition -> edition.map { it.authority }.distinct().size!=1 }) {
                decisions+=unresolved("INCONSISTENT_EDITION_AUTHORITY");continue
            }
            if(links.any { requireNotNull(byKey.getValue(it.source).authority)>requireNotNull(byKey.getValue(it.target).authority) }) {
                decisions+=unresolved("WEAKER_DECLARED_REPLACEMENT");continue
            }
            val outgoing=keys.associateWith { linkedSetOf<String>() }
            val indegree=keys.associateWith { 0 }.toMutableMap()
            for(edge in links) if(outgoing.getValue(edge.source).add(edge.target)) indegree[edge.target]=indegree.getValue(edge.target)+1
            val ready=keys.filter { indegree.getValue(it)==0 }.toMutableList()
            val topology=mutableListOf<String>()
            val preference=compareBy<String> { requireNotNull(byKey.getValue(it).authority) }.thenBy { byKey.getValue(it).order }.thenBy { it }
            while(ready.isNotEmpty()) {
                ready.sortWith(preference);val key=ready.removeAt(0);topology+=key
                for(target in outgoing.getValue(key).sorted()) {
                    indegree[target]=indegree.getValue(target)-1
                    if(indegree.getValue(target)==0) ready+=target
                }
            }
            if(topology.size!=keys.size) { decisions+=unresolved("DIRECTED_CYCLE");continue }
            val companion=links.any { it.kind in setOf("amends","exception_to") }
            val superseded=links.filter { it.kind=="supersedes" }.map { it.target }.toSet()
            val preferred=members.filter { it.key !in superseded }.minWith(compareBy<ConflictNode> { requireNotNull(it.authority) }
                .thenBy { topology.indexOf(it.key) }.thenBy { it.order }.thenBy { it.key })
            val retained=if(companion) topology.toList() else members.filter { it.original==preferred.original && it.key !in superseded }.map { it.key }
            val required=(if(companion) members else retained.map { byKey.getValue(it) }).map { it.canonical }.distinct().sortedWith(canonicalOrder)
            decisions+=ConflictDecision(keys,if(links.isNotEmpty()) "RESOLVED_RELATION" else "RESOLVED_AUTHORITY",
                if(companion) "RETAIN_BASE_AND_COMPANIONS" else "PREFERRED_EDITION",preferred.key,retained,required)
        }
        return decisions
    }
    fun resolvedInterpretation(keys:Set<String>,decisions:List<ConflictDecision>)=
        decisions.any { it.resolved && it.members.containsAll(keys) }
}
