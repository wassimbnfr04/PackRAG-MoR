package org.packrag.retrieval

import kotlin.math.abs
import kotlin.math.sqrt
import org.packrag.model.Chunk
import org.packrag.model.Query
import org.packrag.model.eligible
import org.packrag.model.normalizeQuery
import org.packrag.model.QueryUnicode
import org.packrag.packs.ActivePack
import org.packrag.model.ConflictNode
import org.packrag.model.ConflictEdge
import org.packrag.model.ConflictDecision
import org.packrag.model.Conflicts
import org.packrag.model.RelevanceSignal
import org.packrag.model.RelevanceGate
import org.packrag.model.EvidenceView
import org.packrag.model.PackIdentity
import org.packrag.model.GeneratorRepresentation
import org.packrag.model.GeneratorRepresentations
import org.packrag.model.EvidenceOrigin
import org.packrag.model.CalibrationSnapshot
import org.packrag.model.sourceMetadata
import org.packrag.model.ownedOrigin

data class Candidate(val pack: ActivePack, override val chunk: Chunk, val exact: Boolean,
    val sparseRank: Int?, val denseRank: Int?, val cosine: Double, val rrf: Double,
    val relevant: Boolean = false, val origins: List<String> = listOf("${pack.id}@${pack.version}:${pack.manifestHash}"),
    val conflicts:List<ConflictDecision> = emptyList(),val finalRank:Int?=null,
    val originRecords:List<EvidenceOrigin> = emptyList()):EvidenceView {
    override val packIdentity:PackIdentity get()=PackIdentity(pack.id,pack.version,pack.manifestHash)
    override val originKey:String get()="${pack.id}@${pack.version}:${pack.manifestHash}#${chunk.id}"
    override val generatorRendering:GeneratorRepresentation get()=GeneratorRepresentations.select(
        chunk.canonicalText,chunk.textSha256,chunk.language,pack.derivedByChunk[chunk.id].orEmpty())
    fun captureOrigin():EvidenceOrigin {
        val calibration=pack.manifest.getJSONObject("calibration")
        val status=calibration.optString("status","CALIBRATED")
        return ownedOrigin(EvidenceOrigin(packIdentity,chunk,
            sourceMetadata(chunk,pack.manifest.getJSONObject("publisher").getString("key_id"),pack.relations),
            pack.derivedByChunk[chunk.id].orEmpty(),exact,sparseRank,denseRank,cosine,rrf,
            CalibrationSnapshot(status,if(status=="UNCALIBRATED") null else calibration.getDouble("min_agreed_dense_cosine"),
                if(status=="UNCALIBRATED") null else calibration.getDouble("min_dense_only_cosine")),conflicts))
    }
}
data class RetrievalResult(val candidates: List<Candidate>, val ambiguous: Boolean)

object Retrieval {
    private val order = compareBy<Candidate> { if (it.exact) 0 else 1 }.thenByDescending { it.rrf }
        .thenByDescending { it.exact }.thenByDescending { it.cosine }.thenBy { it.pack.id }.thenBy { it.chunk.id }

    fun retrieve(packs: List<ActivePack>, query: Query, vector: FloatArray,
        sparseLookup:(ActivePack,String)->List<String> = { pack,terms -> pack.sparse(terms) }): RetrievalResult {
        require(vector.size == 384 && vector.all { it.isFinite() })
        require(abs(sqrt(vector.sumOf { it.toDouble() * it }) - 1) <= .01)
        val interpretations=linkedMapOf<String,MutableSet<String>>()
        val all = packs.flatMap { pack ->
            val allowed = pack.chunks.filter { eligible(it, query) }.associateBy { it.id }
            val text = query.normalized
            val matches = linkedMapOf<String, MutableSet<String>>()
            for (alias in pack.aliases) {
                val normalized = normalizeQuery(alias.normalized)
                if (QueryUnicode.containsAlias(text,normalized)) {
                    val targets = if (alias.targetType == "chunk") listOf(alias.targetId)
                        else pack.chunks.filter { it.sourceId == alias.targetId }.map { it.id }
                    matches.getOrPut(normalized) { linkedSetOf() }.addAll(targets.filter { it in allowed })
                }
            }
            val prefix="${pack.id}@${pack.version}:${pack.manifestHash}#"
            for((alias,keys) in matches) interpretations.getOrPut(alias) { linkedSetOf() }.addAll(keys.map { prefix+it })
            val exact = matches.values.flatten().toSet()
            val terms = QueryUnicode.wordTerms(text)
            val sparse = if (terms.isEmpty()) emptyList() else sparseLookup(pack,terms.joinToString(" OR ") { "\"$it\"" }).filter { it in allowed }.take(24)
            val scores = allowed.mapValues { pack.cosine(it.value.denseRow, vector) }
            val dense = scores.keys.sortedWith(compareByDescending<String> { scores.getValue(it) }.thenBy { it }).take(24)
            val sr = sparse.withIndex().associate { it.value to it.index + 1 }
            val dr = dense.withIndex().associate { it.value to it.index + 1 }
            val candidates = (sparse + dense + exact).distinct().map { key ->
                Candidate(pack, allowed.getValue(key), key in exact, sr[key], dr[key], scores.getValue(key),
                    listOfNotNull(sr[key], dr[key]).sumOf { 1.0 / (60 + it) })
            }.sortedWith(order)
            candidates.map { it.copy(relevant=it.exact) }
        }.sortedWith(order)
        val nodes=all.mapIndexed { index,item -> ConflictNode(item.originKey,item.chunk.originalSha256,item.chunk.textSha256,
            item.pack.manifest.getString("domain"),item.pack.manifest.getJSONObject("publisher").getString("key_id"),
            item.chunk.jurisdiction,item.chunk.canonicalUri,item.chunk.article,item.chunk.authorityRank,index) }
        val edges=packs.flatMap { pack ->
            val prefix="${pack.id}@${pack.version}:${pack.manifestHash}#"
            pack.relations.map { ConflictEdge(prefix+it.fromChunkId,prefix+it.toChunkId,it.relationType,it.provenance,it.confidence) }
        }
        val decisions=Conflicts.resolve(nodes,edges)
        val byKey=nodes.associateBy { it.key }
        val ambiguous=interpretations.values.any { keys -> keys.map { byKey.getValue(it).original }.distinct().size>1 &&
            !Conflicts.resolvedInterpretation(keys,decisions) }
        val byMember=decisions.flatMap { decision -> decision.members.map { it to decision } }.toMap()
        val retained=all.mapNotNull { item ->
            val decision=byMember[item.originKey]
            if(decision==null || item.originKey in decision.retained) item.copy(conflicts=listOfNotNull(decision)) else null
        }.toMutableList()
        // Authority moves only a set's members in its own occupied positions.
        for(decision in decisions.filter { it.resolved }) {
            val positions=retained.indices.filter { retained[it].originKey in decision.members }
            val members=positions.map { retained[it] }.sortedBy { decision.retained.indexOf(it.originKey) }
            positions.zip(members).forEach { (index,item) -> retained[index]=item }
        }
        val admitted=mutableSetOf<String>()
        for(rows in retained.groupBy { "${it.pack.id}@${it.pack.version}:${it.pack.manifestHash}" }.values) {
            val fused=rows.filter { it.sparseRank!=null || it.denseRank!=null }.sortedWith(
                compareByDescending<Candidate> { it.rrf }.thenByDescending { it.exact }
                    .thenByDescending { it.cosine }.thenBy { it.pack.id }.thenBy { it.chunk.id }).toMutableList()
            for(decision in rows.flatMap { it.conflicts }.distinct().filter { it.resolved }) {
                val positions=fused.indices.filter { fused[it].originKey in decision.members }
                val members=positions.map { fused[it] }.sortedBy { decision.retained.indexOf(it.originKey) }
                positions.zip(members).forEach { (index,item) -> fused[index]=item }
            }
            admitted.addAll(fused.take(16).map { it.originKey })
            admitted.addAll(rows.filter { it.exact }.map { it.originKey })
        }
        val capped=retained.filter { it.originKey in admitted }
        val dedup = linkedMapOf<Pair<String, String>, Candidate>()
        for (entry in capped) {
            val candidate=entry.copy(originRecords=listOf(entry.captureOrigin()))
            val key = candidate.chunk.originalSha256 to candidate.chunk.textSha256
            val prior = dedup[key]
            dedup[key] = if (prior == null) candidate else prior.copy(relevant = prior.relevant || candidate.relevant,
                origins = (prior.origins + candidate.origins).distinct(),conflicts=(prior.conflicts+candidate.conflicts).distinct(),
                originRecords=prior.originRecords+candidate.originRecords)
        }
        val merged=dedup.values.take(32)
        val flags=RelevanceGate.mark(merged.map { item ->
            val calibration=item.pack.manifest.getJSONObject("calibration")
            val calibrated=calibration.optString("status","CALIBRATED")!="UNCALIBRATED"
            RelevanceSignal(item.exact,item.sparseRank,item.denseRank,item.cosine,calibrated,
                if(calibrated) calibration.getDouble("min_agreed_dense_cosine") else null,
                if(calibrated) calibration.getDouble("min_dense_only_cosine") else null) })
        return RetrievalResult(merged.zip(flags).mapIndexed { index,(item,flag) -> item.copy(relevant=flag,finalRank=index+1) }, ambiguous)
    }
}
