package org.packrag.model

/** Frozen Unicode 15; query/alias semantics do not depend on JVM or Android UCD. */
object QueryUnicode {
    const val VERSION = QueryUnicodeData.VERSION
    const val TABLE_SHA256 = QueryUnicodeData.TABLE_SHA256
    private fun property(point:Int, bounds:IntArray):Boolean {
        var lo=0; var hi=bounds.size
        while(lo<hi) { val mid=(lo+hi) ushr 1; if(bounds[mid]<=point) lo=mid+1 else hi=mid }
        return lo%2==1 || (lo>0 && bounds[lo-1]==point)
    }
    fun isWord(point:Int):Boolean = property(point,QueryUnicodeData.word)
    fun isWhitespace(point:Int):Boolean = property(point,QueryUnicodeData.whitespace)
    fun wordTerms(text:String):List<String> {
        val terms=sortedSetOf(PortableNames.order); val current=StringBuilder()
        fun flush() { if(current.isNotEmpty()) { terms.add(current.toString()); current.setLength(0) } }
        text.codePoints().forEach { if(isWord(it)) current.appendCodePoint(it) else flush() }; flush()
        return terms.toList()
    }
    fun containsAlias(text:String,alias:String):Boolean {
        if(alias.isEmpty()) return false
        var start=0
        while(start<text.length) {
            val index=text.indexOf(alias,start); if(index<0) return false
            val end=index+alias.length
            if((index==0 || !isWord(text.codePointBefore(index))) && (end==text.length || !isWord(text.codePointAt(end)))) return true
            start=index+1
        }
        return false
    }
    private fun ccc(point:Int):Int = QueryUnicodeData.combining[point] ?: 0
    fun nfkc(text:String):String {
        val expanded=ArrayList<Int>()
        text.codePoints().forEach { point ->
            if(point in 0xac00..0xd7a3) {
                val index=point-0xac00
                expanded.add(0x1100+index/588); expanded.add(0x1161+index%588/28)
                if(index%28!=0) expanded.add(0x11a7+index%28)
            } else {
                val mapping=QueryUnicodeData.decomposition[point]
                if(mapping==null) expanded.add(point) else mapping.codePoints().forEach { expanded.add(it) }
            }
        }
        val ordered=ArrayList<Int>(); val marks=ArrayList<Int>()
        fun flush() { marks.sortWith(compareBy { ccc(it) }); ordered.addAll(marks); marks.clear() }
        for(point in expanded) { if(ccc(point)==0) { flush(); ordered.add(point) } else marks.add(point) }; flush()
        val result=ArrayList<Int>(); var starterIndex=-1; var starter=-1; var lastCcc=0
        for(point in ordered) {
            val currentCcc=ccc(point)
            val composite=if(starterIndex>=0 && (lastCcc<currentCcc || lastCcc==0)) {
                when {
                    starter in 0x1100..0x1112 && point in 0x1161..0x1175 -> 0xac00+(starter-0x1100)*588+(point-0x1161)*28
                    starter in 0xac00..0xd7a3 && (starter-0xac00)%28==0 && point in 0x11a8..0x11c2 -> starter+point-0x11a7
                    else -> QueryUnicodeData.composition[(starter.toLong() shl 21) or point.toLong()]
                }
            } else null
            if(composite!=null) { result[starterIndex]=composite; starter=composite }
            else { if(currentCcc==0) { starterIndex=result.size; starter=point }; result.add(point); lastCcc=currentCcc }
        }
        return buildString { for(point in result) appendCodePoint(point) }
    }
    fun lowercase(text:String):String {
        val points=text.codePoints().toArray()
        return buildString {
            for(i in points.indices) {
                val point=points[i]
                if(point==0x03a3) {
                    var before=i-1; var after=i+1
                    while(before>=0 && property(points[before],QueryUnicodeData.case_ignorable)) before--
                    while(after<points.size && property(points[after],QueryUnicodeData.case_ignorable)) after++
                    val final=before>=0 && property(points[before],QueryUnicodeData.cased) && !(after<points.size && property(points[after],QueryUnicodeData.cased))
                    appendCodePoint(if(final) 0x03c2 else 0x03c3)
                } else QueryUnicodeData.lower[point]?.let { append(it) } ?: appendCodePoint(point)
            }
        }
    }
    fun normalize(text:String):String {
        val filtered=buildString { nfkc(text).codePoints().forEach { if(it!=0x0640 && it !in 0x064b..0x065f && it!=0x0670) appendCodePoint(it) } }
        return buildString {
            var pendingSpace=false
            lowercase(filtered).codePoints().forEach { point ->
                if(property(point,QueryUnicodeData.whitespace)) pendingSpace=isNotEmpty()
                else { if(pendingSpace) append(' '); appendCodePoint(point); pendingSpace=false }
            }
        }
    }
}
