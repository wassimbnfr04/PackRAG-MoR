package org.packrag.model

import java.time.LocalDate

object TemporalDates {
    fun date(value: String): LocalDate {
        require(Regex("[0-9]{4}-[0-9]{2}-[0-9]{2}").matches(value))
        return LocalDate.parse(value).also { require(it.year >= 1) }
    }
    fun utc(value: String) {
        val m = Regex("([0-9]{4}-[0-9]{2}-[0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\\.[0-9]+)?Z").matchEntire(value) ?: throw IllegalArgumentException("Invalid UTC timestamp")
        date(m.groupValues[1]); val h = m.groupValues[2].toInt(); val min = m.groupValues[3].toInt(); val sec = m.groupValues[4].toInt()
        require(h <= 23 && min <= 59 && sec <= 60 && (sec != 60 || (h == 23 && min == 59)))
        // Syntax acceptance is distinct from verifying historical IERS leap-second announcements.
    }
    fun dateOrTimestamp(value: String) { if (value.length == 10) date(value) else utc(value) }
}
