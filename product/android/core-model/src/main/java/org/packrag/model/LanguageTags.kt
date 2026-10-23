package org.packrag.model

import java.util.Locale

/** RFC5646 well-formed syntax; registry membership/translation quality are separate provenance checks. */
object LanguageTags {
    private val grandfathered = setOf("en-gb-oed","i-ami","i-bnn","i-default","i-enochian","i-hak","i-klingon","i-lux","i-mingo","i-navajo","i-pwn","i-tao","i-tay","i-tsu","sgn-be-fr","sgn-be-nl","sgn-ch-de","art-lojban","cel-gaulish","no-bok","no-nyn","zh-guoyu","zh-hakka","zh-min","zh-min-nan","zh-xiang")
    private val normal = Regex("(?:[a-z]{2,3}(?:-[a-z]{3}){0,3}|[a-z]{4}|[a-z]{5,8})(?:-[a-z]{4})?(?:-(?:[a-z]{2}|[0-9]{3}))?((?:-(?:[a-z0-9]{5,8}|[0-9][a-z0-9]{3}))*)((?:-[0-9a-wy-z](?:-[a-z0-9]{2,8})+)*)(?:-x(?:-[a-z0-9]{1,8})+)?")
    fun valid(value: String): Boolean {
        val tag = value.lowercase(Locale.ROOT)
        if (tag in grandfathered || Regex("x(?:-[a-z0-9]{1,8})+").matches(tag)) return true
        val match = normal.matchEntire(tag) ?: return false
        val variants = match.groupValues[1].split('-').filter { it.isNotEmpty() }
        val singletons = match.groupValues[2].split('-').filter { it.length == 1 }
        return variants.distinct().size == variants.size && singletons.distinct().size == singletons.size
    }
}
