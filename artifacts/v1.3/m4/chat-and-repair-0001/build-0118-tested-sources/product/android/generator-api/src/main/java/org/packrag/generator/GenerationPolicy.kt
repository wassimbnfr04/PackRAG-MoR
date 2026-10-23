package org.packrag.generator

import java.security.MessageDigest
import java.util.Collections
import org.json.JSONObject

/** Immutable, hash-approved generation settings; retrieval compatibility stays mobile-v1. */
class GenerationPolicy private constructor(val profileId:String,val context:Int,val generated:Int,
    val suffix:String,val quoted:Boolean,val configSha256:String?) {
    fun system(baseline:String)=baseline+if(quoted) "\n$suffix" else ""
    companion object {
        val BASELINE=GenerationPolicy("mobile-v1",2048,512,"",false,null)
        const val QUOTE_CONFIG_SHA="dae71e602caa7f10e9030f4a19e21b44d513067ebccbc9ccee600b996965225d"
        fun quotes(bytes:ByteArray):GenerationPolicy {
            val owned=bytes.copyOf()
            val hash=MessageDigest.getInstance("SHA-256").digest(owned).joinToString(""){"%02x".format(it.toInt() and 255)}
            require(hash==QUOTE_CONFIG_SHA){"GENERATION_POLICY_HASH_MISMATCH"}
            val row=JSONObject(owned.toString(Charsets.UTF_8))
            require(row.getInt("schema_version")==1 && row.getString("compatible_retrieval_profile")=="mobile-v1"
                && row.getInt("context_tokens")==3072 && row.getInt("generated_tokens_cap")==1536
                && row.getInt("prefill_tokens_cap")==1536 && row.getInt("max_evidence_tokens_cap")==1200
                && row.getInt("max_evidence_chunks")==4 && row.getInt("max_quote_units")==64 && row.getInt("max_output_lines")==4)
            return GenerationPolicy(row.getString("profile_id"),3072,1536,row.getString("system_suffix"),true,hash)
        }
    }
}

/** Physical-line normalization matches Python's declared Unicode whitespace protocol. */
object QuoteProtocol {
    private val separators=Regex("\\r\\n|[\\n\\r\\u000b\\u000c\\u001c\\u001d\\u001e\\u0085\\u2028\\u2029]")
    private fun space(c:Char)=c.code in 9..13 || c.code in 28..32 || c.code in 0x2000..0x200a ||
        c.code in listOf(0x85,0xa0,0x1680,0x2028,0x2029,0x202f,0x205f,0x3000)
    private fun trimmed(value:String)=value.trim(::space)
    fun units(texts:List<String>):List<String> {
        val owned=texts.toList();require(owned.size in 1..4){"INPUT_TOO_LONG"}
        val result=owned.flatMapIndexed { index,text -> separators.split(text).map(::trimmed).filter{it.isNotEmpty()}.map{"$it [S${index+1}]"} }.distinct()
        require(result.size in 1..64){"INPUT_TOO_LONG"}
        return Collections.unmodifiableList(result.toList())
    }
    private fun literal(value:String):String=buildString {
        append('"')
        var index=0
        while(index<value.length) {
            val c=value[index++]
            when(c) {
                '"'->append("\\\"");'\\'->append("\\\\");'\n'->append("\\n");'\r'->append("\\r")
                '\t'->append("\\t");'\b'->append("\\b");'\u000c'->append("\\f")
                else -> when {
                    c.code<32->append("\\u%04x".format(c.code))
                    c.isHighSurrogate()->{require(index<value.length && value[index].isLowSurrogate()){ "INVALID_EVIDENCE_UNICODE" };append(c);append(value[index++])}
                    c.isLowSurrogate()->error("INVALID_EVIDENCE_UNICODE")
                    else->append(c)
                }
            }
        }
        append('"')
    }
    fun grammar(units:List<String>):String {
        require(units.size in 1..64){"INPUT_TOO_LONG"}
        val result="root ::= \"</think>\" pad (\"INSUFFICIENT_EVIDENCE\" | \"1. \" line (sep \"2. \" line (sep \"3. \" line (sep \"4. \" line)?)?)?) pad\n"+
            "line ::= "+units.joinToString(" | ",transform=::literal)+"\n"+
            "pad ::= (\"\\n\" | \"\\n\\n\")?\nsep ::= \"\\n\" | \"\\n\\n\"\n"
        require(result.toByteArray(Charsets.UTF_8).size<=128*1024){"INPUT_TOO_LONG"};return result
    }
    fun matches(final:String,units:List<String>):Boolean {
        val lines=separators.split(final).map(::trimmed).filter{it.isNotEmpty()}
        if(lines.size !in 1..4)return false
        val selected=mutableListOf<String>()
        for((index,line) in lines.withIndex()) {
            val prefix="${index+1}. "
            if(!line.startsWith(prefix))return false
            val unit=line.removePrefix(prefix);if(unit !in units)return false;selected.add(unit)
        }
        return selected.distinct().size==selected.size
    }
}

/** One owned request binds policy, actual prompt IDs and selected immutable rendering units. */
class GenerationRequest(val policy:GenerationPolicy,tokens:IntArray,val maximum:Int,texts:List<String>) {
    private val ownedTokens=tokens.copyOf()
    val tokens:IntArray get()=ownedTokens.copyOf()
    val units:List<String> = if(policy.quoted)QuoteProtocol.units(texts) else emptyList()
    val grammar:String? = if(policy.quoted)QuoteProtocol.grammar(units) else null
    init {
        require(ownedTokens.size in 1..1536 && maximum in 1..policy.generated && ownedTokens.size+maximum<=policy.context){"INPUT_TOO_LONG"}
    }
    override fun toString()="GenerationRequest(profile=${policy.profileId},prefill=${ownedTokens.size},maximum=$maximum)"
}
