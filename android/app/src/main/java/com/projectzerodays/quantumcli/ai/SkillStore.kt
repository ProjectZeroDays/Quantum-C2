package com.projectzerodays.quantumcli.ai

import com.projectzerodays.quantumcli.c2.C2State
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/** One skill pack: a reusable prompt template for the chat brain. */
data class SkillDef(
    val id: String,
    val name: String,
    val description: String,
    val prompt: String,
)

/**
 * JSON-file-backed skill registry (skills.json under the app files dir).
 * Seeded with the operator skill packs (recon, weapon-craft, report).
 */
object SkillStore {

    private val _skills = MutableStateFlow<List<SkillDef>>(emptyList())
    val skills: StateFlow<List<SkillDef>> = _skills.asStateFlow()

    @Volatile
    private var loaded = false

    private fun file(): File = File(C2State.filesRoot, "skills.json")

    /** Load (or seed) on first access; safe to call repeatedly. */
    fun load(): List<SkillDef> {
        if (loaded) return _skills.value
        synchronized(this) {
            if (loaded) return _skills.value
            val parsed = try {
                val f = file()
                if (f.isFile) parse(f.readText()) else emptyList()
            } catch (e: Exception) {
                C2State.audit("AI", "skill store load failed: ${e.message}")
                emptyList()
            }
            val list = parsed.ifEmpty { seed() }
            _skills.value = list
            loaded = true
            return list
        }
    }

    private fun parse(json: String): List<SkillDef> {
        val arr = JSONArray(json)
        val out = ArrayList<SkillDef>(arr.length())
        for (i in 0 until arr.length()) {
            val o = arr.getJSONObject(i)
            out.add(
                SkillDef(
                    id = o.optString("id"),
                    name = o.optString("name"),
                    description = o.optString("description"),
                    prompt = o.optString("prompt"),
                )
            )
        }
        return out.filter { it.id.isNotBlank() }
    }

    private fun save(list: List<SkillDef>) {
        try {
            val arr = JSONArray()
            list.forEach { s ->
                arr.put(
                    JSONObject()
                        .put("id", s.id)
                        .put("name", s.name)
                        .put("description", s.description)
                        .put("prompt", s.prompt)
                )
            }
            file().writeText(arr.toString(2))
        } catch (e: Exception) {
            C2State.audit("AI", "skill store save failed: ${e.message}")
        }
    }

    /** Insert or update by id; persists immediately. */
    fun upsert(s: SkillDef) {
        val list = load().filterNot { it.id == s.id } + s
        _skills.value = list.sortedBy { it.id }
        save(_skills.value)
    }

    fun delete(id: String) {
        val list = load().filterNot { it.id == id }
        _skills.value = list
        save(list)
    }

    fun byId(id: String): SkillDef? = load().firstOrNull { it.id == id }

    // ------------------------------------------------------------ seed data
    private fun seed(): List<SkillDef> = listOf(
        SkillDef(
            "recon", "Recon pass",
            "Turn a CIDR sweep into a ranked target shortlist.",
            "Run a recon pass over the local scope. List live hosts with open ports, " +
                "rank the most promising targets and name the single best next probe " +
                "for each. Reply as a compact list, no fluff."
        ),
        SkillDef(
            "weapon-craft", "Weapon craft",
            "Match a fingerprint to the ZERO_DAY registry.",
            "Given this fingerprint, pick the best matching weapon from the ZERO_DAY " +
                "registry, justify the tier choice, and draft the exact fire " +
                "parameters as JSON {\"cve\": ..., \"ip\": ...}."
        ),
        SkillDef(
            "report", "Engagement report",
            "Compress the audit journal into a clean report.",
            "Summarize this engagement as an operator report: timeline of actions with " +
                "targets and results, MITRE techniques touched, loot collected and the " +
                "recommended cleanup pass. Terminal tone, tight prose."
        ),
    )
}
